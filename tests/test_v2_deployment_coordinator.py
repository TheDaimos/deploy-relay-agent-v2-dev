"""End-to-end backend confirmation with V1 engine, isolated synthetic files."""
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
    stub=types.ModuleType("aiohttp")
    stub.ClientSession=type("ClientSession",(),{})
    sys.modules["aiohttp"]=stub

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"deploy_relay_v2_dev"
PKG="_v2_deployment_confirm"
package=types.ModuleType(PKG)
package.__path__=[str(ROOT)]
sys.modules[PKG]=package
coord=importlib.import_module(PKG+".deployment_coordinator")
server=importlib.import_module(PKG+".server_deployment_jobs")
registry=importlib.import_module(PKG+".operation_registry")
model=importlib.import_module(PKG+".operation_model")
engine=importlib.import_module(PKG+".v1_engine.deployment")
manifest=importlib.import_module(PKG+".v1_engine.manifest")
source=importlib.import_module(PKG+".v1_engine.source_inventory")
preview=importlib.import_module(PKG+".v1_engine.preview")
bridge=importlib.import_module(PKG+".v1_source_bridge")


class ConfirmationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"config"
        self.root.mkdir()
        self.manifest=manifest.parse_manifest({
            "schema":"deploy-relay.deployment.v1",
            "project":{"id":"safeapp","name":"Safe App"},
            "source":{"repository":"TheDaimos/safeapp","mode":"repository_contents"},
            "deployment":{"root":"/config","groups":[{
                "id":"app","source":"custom_components/safeapp",
                "target":"custom_components/safeapp","mode":"replace_directory",
            }]},
            "lifecycle":{"after_install":"home_assistant_restart"},
            "policy":{"allow_symlinks":False,"max_files":10,"max_uncompressed_bytes":4096},
        })
        self.inventory=source.SourceInventory(
            project_id="safeapp",repository="TheDaimos/safeapp",
            source_ref="deploy/dev",source_commit="a"*40,groups=(
                source.SourceGroupInventory("app",()),),total_files=0,total_bytes=0)
        self.preview=preview.PreviewResult(
            project_id="safeapp",repository="TheDaimos/safeapp",
            source_ref="deploy/dev",source_commit="a"*40,files=(
                preview.PreviewFile("app",preview.PreviewOperation.ADD,
                    "custom_components/safeapp/main.py","custom_components/safeapp/main.py",
                    "f"*64,None,2,None),
            ))
        self.pending=bridge.PreparedV1Source(self.manifest,self.inventory,self.preview)
        self.backend=server.ServerDeploymentJobs(registry.OperationRegistry(),
                                                  asyncio.create_task)
        self.owner=coord.DeploymentCoordinator(self.backend)
        self.kw={"session":None,"repository":"TheDaimos/safeapp",
                 "source_ref":"deploy/dev","source_commit":"a"*40,
                 "expected_project_id":"safeapp","config_root":self.root}

    async def test_one_challenge_and_only_one_confirmed_server_job(self):
        started=asyncio.Event()
        release=asyncio.Event()
        calls=[]
        async def fake_engine(*args,**kwargs):
            calls.append(1)
            started.set()
            await release.wait()
            return types.SimpleNamespace(
                state=engine.TransactionState.SUCCESS,restart_required=True,
                lifecycle="home_assistant_restart")
        async def fake_source(**kwargs):
            return self.pending
        with patch.object(coord,"prepare_frozen_v1_source",fake_source), \
             patch.object(engine,"async_execute_deployment",fake_engine):
            offer=await self.owner.prepare(**self.kw)
            self.assertEqual(offer["schema"],"dra-v2-install-preparation.v1")
            self.assertEqual(offer["add"],1)
            self.assertTrue(offer["confirmation_required"])
            self.assertIsNone(await self.owner.latest())
            with self.assertRaises(model.OperationContractError):
                await self.owner.confirm(
                    challenge=offer["challenge"],repository=offer["repository"],
                    commit=offer["source_commit"],confirm=False,
                    session=None,config_root=self.root)
            offer=await self.owner.prepare(**self.kw)
            response=await self.owner.confirm(
                challenge=offer["challenge"],repository=offer["repository"],
                commit=offer["source_commit"],confirm=True,
                session=None,config_root=self.root)
            await asyncio.wait_for(started.wait(),timeout=1)
            self.assertEqual(len(calls),1)
            self.assertEqual((await self.owner.latest())["operation_id"],
                             response["operation_id"])
            with self.assertRaises(model.OperationContractError):
                await self.owner.confirm(
                    challenge=offer["challenge"],repository=offer["repository"],
                    commit=offer["source_commit"],confirm=True,
                    session=None,config_root=self.root)
            with self.assertRaises(model.OperationContractError):
                await self.owner.prepare(**self.kw)
            release.set()
            await self.owner.close()
            ended=await self.owner.get(response["operation_id"])
            self.assertEqual(ended["status"],"success")
            self.assertTrue(ended["restart_required"])
            self.assertEqual(len(calls),1)

    async def test_old_or_unfinished_transaction_journal_blocks_new_deployment(self):
        async def fake_source(**kwargs):return self.pending
        transaction_dir=self.root/"deploy_relay_v2_dev"/"transactions"
        transaction_dir.mkdir(parents=True)
        journal=transaction_dir/"synthetic.json"
        for state in ("staging","backing_up","installing","verifying_install",
                      "recovery_required","unknown"):
            journal.write_text(json.dumps({"state":state}))
            with self.subTest(state=state), \
                 patch.object(coord,"prepare_frozen_v1_source",fake_source), \
                 self.assertRaises(model.OperationContractError):
                await self.owner.prepare(**self.kw)
        journal.write_text(json.dumps({"state":"rolled_back"}))
        with patch.object(coord,"prepare_frozen_v1_source",fake_source):
            x=await self.owner.prepare(**self.kw)
        self.assertEqual(x["add"],1)
        self.assertEqual(journal.read_text(),json.dumps({"state":"rolled_back"}))
        await self.owner.close()

    async def test_bad_confirmation_never_runs_engine(self):
        async def fake_source(**kwargs):return self.pending
        with patch.object(coord,"prepare_frozen_v1_source",fake_source),\
             patch.object(engine,"async_execute_deployment",
                          side_effect=AssertionError("forbidden")):
            offer=await self.owner.prepare(**self.kw)
            with self.assertRaises(model.OperationContractError):
                await self.owner.confirm(
                    challenge=offer["challenge"],repository=offer["repository"],
                    commit="b"*40,confirm=True,session=None,config_root=self.root)
            self.assertIsNone(await self.owner.latest())
            await self.owner.close()


if __name__=="__main__":
    unittest.main()
