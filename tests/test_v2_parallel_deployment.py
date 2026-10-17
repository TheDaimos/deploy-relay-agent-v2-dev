"""A grouped test of *actual concurrent* V2 server task scheduling.

Synthetic V1 tasks hold real temporary journals and await independent release
events. The original V1 backup/install/rollback algorithms are exercised in
test_v2_reused_v1_engine.py; these tests cover write-target admission only.
"""
from __future__ import annotations

import asyncio
from dataclasses import replace
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

try:
    import aiohttp
except ImportError:
    fake=types.ModuleType("aiohttp")
    fake.ClientSession=type("ClientSession",(),{})
    sys.modules["aiohttp"]=fake

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"deploy_relay_v2_dev"
PKG="_v2_concurrent_jobs"
package=types.ModuleType(PKG)
package.__path__=[str(ROOT)]
sys.modules[PKG]=package
coordinator=importlib.import_module(PKG+".deployment_coordinator")
server=importlib.import_module(PKG+".server_deployment_jobs")
registry_mod=importlib.import_module(PKG+".operation_registry")
model=importlib.import_module(PKG+".operation_model")
engine=importlib.import_module(PKG+".v1_engine.deployment")
manifest_module=importlib.import_module(PKG+".v1_engine.manifest")
inventory_module=importlib.import_module(PKG+".v1_engine.source_inventory")
preview_module=importlib.import_module(PKG+".v1_engine.preview")
source_bridge=importlib.import_module(PKG+".v1_source_bridge")

COMMIT="a"*40


def source_for(name, target=None):
    target=target or f"custom_components/{name}"
    repo=f"TheDaimos/{name}"
    manifest=manifest_module.parse_manifest({
        "schema":"deploy-relay.deployment.v1",
        "project":{"id":name,"name":name},
        "source":{"repository":repo,"mode":"repository_contents"},
        "deployment":{"root":"/config","groups":[{
            "id":name,"source":f"custom_components/{name}",
            "target":target,"mode":"replace_directory",
        }]},
        "lifecycle":{"after_install":"home_assistant_restart"},
        "policy":{"allow_symlinks":False,"max_files":9,
                  "max_uncompressed_bytes":9000},
    })
    inv=inventory_module.SourceInventory(
        project_id=name,repository=repo,source_ref="deploy/dev",
        source_commit=COMMIT,groups=(
            inventory_module.SourceGroupInventory(name,()),),
        total_files=0,total_bytes=0,
    )
    prev=preview_module.PreviewResult(
        project_id=name,repository=repo,source_ref="deploy/dev",source_commit=COMMIT,
        files=(preview_module.PreviewFile(
            name,preview_module.PreviewOperation.ADD,
            target+"/main.py",f"custom_components/{name}/main.py",
            "a"*64,None,10,None,
        ),),
    )
    return source_bridge.PreparedV1Source(manifest,inv,prev)


class ParallelV1InstallTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config=Path(self.temp.name)/"config"
        self.config.mkdir()
        self.backend=server.ServerDeploymentJobs(
            registry_mod.OperationRegistry(max_mutating=4),asyncio.create_task)
        self.coordinator=coordinator.DeploymentCoordinator(self.backend)
        self.events={name:asyncio.Event() for name in ("alpha","beta","gamma","delta")}
        self.release=asyncio.Event()
        self.started=[]
        self.journal=self.config/"deploy_relay_v2_dev"/"transactions"
        self.journal.mkdir(parents=True)

    async def _fake_engine(self,session,manifest,inventory,preview,*,progress,**kwargs):
        name=manifest.project_id
        jobid=f"dra-20261012T060000Z-{name}-{COMMIT[:12]}"
        (self.journal/(jobid+".json")).write_text(json.dumps({
            "schema":"deploy-relay.transaction.v1","transaction_id":jobid,
            "state":"installing","project_id":name,"source_commit":COMMIT}))
        await progress("install",{"transaction_id":jobid})
        self.started.append(name)
        self.events[name].set()
        await self.release.wait()
        (self.journal/(jobid+".json")).write_text(json.dumps({
            "schema":"deploy-relay.transaction.v1","transaction_id":jobid,
            "state":"success","project_id":name,"source_commit":COMMIT}))
        return types.SimpleNamespace(
            state=engine.TransactionState.SUCCESS,restart_required=True,
            lifecycle="home_assistant_restart")

    async def _fake_source(self,**kwargs):
        return source_for(kwargs["expected_project_id"])

    async def _prepare_and_confirm(self,name):
        kwargs=dict(session=None,repository=f"TheDaimos/{name}",
            source_ref="deploy/dev",source_commit=COMMIT,
            expected_project_id=name,config_root=self.config)
        report=await self.coordinator.prepare(**kwargs)
        return await self.coordinator.confirm(
            challenge=report["challenge"],repository=report["repository"],
            commit=report["source_commit"],confirm=True,
            session=None,config_root=self.config)

    async def test_two_disjoint_real_server_tasks_run_before_either_finishes(self):
        with patch.object(coordinator,"prepare_frozen_v1_source",self._fake_source),\
             patch.object(engine,"async_execute_deployment",self._fake_engine):
            a=await self._prepare_and_confirm("alpha")
            await asyncio.wait_for(self.events["alpha"].wait(),1)
            b=await self._prepare_and_confirm("beta")
            await asyncio.wait_for(self.events["beta"].wait(),1)
            self.assertEqual(set(self.started),{"alpha","beta"})
            self.assertEqual((await self.backend.get(a["operation_id"]))["status"],"running")
            self.assertEqual((await self.backend.get(b["operation_id"]))["status"],"running")
            self.assertEqual(len(await self.backend.active_transaction_ids()),2)
            self.release.set()
            await self.coordinator.close()
            for result in (a,b):
                status=await self.backend.get(result["operation_id"])
                self.assertEqual(status["status"],"success")
                self.assertTrue(status["restart_required"])
            self.assertEqual(await self.backend.active_transaction_ids(),frozenset())

    async def test_parent_child_target_conflict_is_rejected_before_second_write(self):
        first=source_for("alpha",target="custom_components/weather")
        second=source_for("beta",target="custom_components/weather/subcomponent")
        with patch.object(engine,"async_execute_deployment",self._fake_engine):
            a=await self.backend.start_verified(
                manifest=first.manifest,inventory=first.inventory,preview=first.preview,
                session=None,config_root=self.config,request_id="request-alpha-001")
            await asyncio.wait_for(self.events["alpha"].wait(),1)
            with self.assertRaises(model.OperationContractError):
                await self.backend.start_verified(
                    manifest=second.manifest,inventory=second.inventory,
                    preview=second.preview,session=None,config_root=self.config,
                    request_id="request-beta-002")
            self.assertEqual(self.started,["alpha"])
            self.release.set()
            await self.backend.finish_before_unload()
            self.assertEqual((await self.backend.get(a["operation_id"]))["status"],"success")
            self.assertEqual(len(self.backend._reserved_targets),0)

    async def test_stale_unfinished_transaction_blocks_new_work_not_active_journal(self):
        active=source_for("alpha")
        with patch.object(engine,"async_execute_deployment",self._fake_engine),\
             patch.object(coordinator,"prepare_frozen_v1_source",self._fake_source):
            await self.backend.start_verified(
                manifest=active.manifest,inventory=active.inventory,
                preview=active.preview,session=None,config_root=self.config,
                request_id="request-alpha-001")
            await asyncio.wait_for(self.events["alpha"].wait(),1)
            prepared=await self.coordinator.prepare(
                session=None,repository="TheDaimos/beta",source_ref="deploy/dev",
                source_commit=COMMIT,expected_project_id="beta",
                config_root=self.config)
            self.assertEqual(prepared["project_id"],"beta")
            (self.journal/"stale-other.json").write_text(json.dumps({
                "state":"installing","transaction_id":"stale-other"}))
            with self.assertRaises(model.OperationContractError):
                await self.coordinator.prepare(
                    session=None,repository="TheDaimos/gamma",source_ref="deploy/dev",
                    source_commit=COMMIT,expected_project_id="gamma",
                    config_root=self.config)
            self.release.set()
            await self.coordinator.close()

    async def test_four_parallel_capacity_and_fifth_rejected(self):
        with patch.object(engine,"async_execute_deployment",self._fake_engine):
            for name in self.events:
                item=source_for(name)
                await self.backend.start_verified(
                    manifest=item.manifest,inventory=item.inventory,
                    preview=item.preview,session=None,config_root=self.config,
                    request_id=f"request-{name}-00001")
                await asyncio.wait_for(self.events[name].wait(),1)
            fifth=source_for("epsilon")
            with self.assertRaises(model.OperationContractError):
                await self.backend.start_verified(
                    manifest=fifth.manifest,inventory=fifth.inventory,
                    preview=fifth.preview,session=None,config_root=self.config,
                    request_id="request-epsilon-00001")
            self.assertEqual(len(self.started),4)
            self.release.set()
            await self.backend.finish_before_unload()
            self.assertEqual(len(self.backend._reserved_targets),0)


if __name__=="__main__":
    unittest.main()
