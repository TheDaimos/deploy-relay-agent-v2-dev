"""Batch safety: one explicit consent, immutable plans, ordered HA jobs, fail closed."""
from __future__ import annotations
import asyncio
import importlib
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
PKG="_v2_batch_install_test"
package=types.ModuleType(PKG)
package.__path__=[str(ROOT)]
sys.modules[PKG]=package
batch=importlib.import_module(PKG+".batch_installation")
jobs=importlib.import_module(PKG+".server_deployment_jobs")
registry=importlib.import_module(PKG+".operation_registry")
engine=importlib.import_module(PKG+".v1_engine.deployment")
manifest=importlib.import_module(PKG+".v1_engine.manifest")
inventory=importlib.import_module(PKG+".v1_engine.source_inventory")
preview=importlib.import_module(PKG+".v1_engine.preview")
bridge=importlib.import_module(PKG+".v1_source_bridge")
model=importlib.import_module(PKG+".operation_model")

class BatchSafety(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.owner=jobs.ServerDeploymentJobs(
            registry.OperationRegistry(max_completed=12,max_mutating=4),asyncio.create_task)
        self.batch=batch.BatchDeployment(self.owner,asyncio.create_task)
        self.a="a"*32
        self.b="b"*32

    def spec(self,n,target=None):
        name=f"safe{n}"
        return {
            "repository":f"TheDaimos/{name}","project_id":name,
            "ref":"deploy/dev","commit":str(n)*40,"token":None,
        }

    def frozen(self, spec, *, target=None):
        name=spec["project_id"]
        target=target or f"custom_components/{name}"
        mf=manifest.parse_manifest({
            "schema":"deploy-relay.deployment.v1",
            "project":{"id":name,"name":name},
            "source":{"repository":spec["repository"],"mode":"repository_contents"},
            "deployment":{"root":"/config","groups":[{
                "id":"main","source":f"custom_components/{name}",
                "target":target,"mode":"replace_directory",
            }]},
            "lifecycle":{"after_install":"home_assistant_restart"},
            "policy":{"allow_symlinks":False,"max_files":12,
                      "max_uncompressed_bytes":16000},
        })
        inv=inventory.SourceInventory(
            project_id=name,repository=spec["repository"],
            source_ref=spec["ref"],source_commit=spec["commit"],
            groups=(inventory.SourceGroupInventory("main",()),),
            total_files=1,total_bytes=3)
        pv=preview.PreviewResult(
            project_id=name,repository=spec["repository"],
            source_ref=spec["ref"],source_commit=spec["commit"],
            files=(preview.PreviewFile("main",preview.PreviewOperation.ADD,
                      target+"/main.py",target+"/main.py","f"*64,None,3,None),))
        return bridge.PreparedV1Source(mf,inv,pv)

    async def prepare(self, specs, *, targets=None):
        targets=targets or {}
        async def fake_source(**kwargs):
            spec=next(x for x in specs if x["project_id"]==kwargs["expected_project_id"])
            return self.frozen(spec,target=targets.get(spec["project_id"]))
        with patch.object(batch,"prepare_frozen_v1_source",fake_source):
            return await self.batch.prepare(specs,session=None,config_root=self.root,
                                            client_id=self.a)

    async def start(self,challenge,client=None,confirm=True):
        return await self.batch.start(
            challenge=challenge,client_id=client or self.a,confirm=confirm,
            session=None,config_root=self.root,token_for_repository=lambda _:None,
            blocking_executor=None)

    async def test_two_jobs_one_confirmation_and_no_repeat(self):
        specs=[self.spec(1),self.spec(2)]
        offer=await self.prepare(specs)
        self.assertTrue(offer["preparation"]["confirmation_required"])
        self.assertEqual(len(offer["preparation"]["items"]),2)
        calls=[]
        async def done(_session,mf,*args,**kw):
            calls.append(mf.project_id)
            return types.SimpleNamespace(state=engine.TransactionState.SUCCESS,
                restart_required=True,lifecycle="home_assistant_restart")
        with patch.object(engine,"async_execute_deployment",done):
            receipt=await self.start(offer["challenge"])
            self.assertEqual(receipt["schema"],"dra-v2-batch-start.v1")
            with self.assertRaises(model.OperationContractError):
                await self.start(offer["challenge"])
            await self.batch.close()
        result=await self.batch.status()
        self.assertEqual(result["status"],"success")
        self.assertEqual(result["current"],2)
        self.assertEqual(calls,["safe1","safe2"])
        self.assertEqual([x["status"] for x in result["items"]],["success","success"])
        restarts=await self.owner.restart_summary()
        self.assertEqual(restarts["count"],2)

    async def test_failure_stops_following_projects_and_retains_prior_success(self):
        specs=[self.spec(1),self.spec(2),self.spec(3)]
        offer=await self.prepare(specs)
        calls=[]
        async def run(_session,mf,*args,**kw):
            calls.append(mf.project_id)
            if mf.project_id=="safe2":raise engine.DeploymentError("simulated failure")
            return types.SimpleNamespace(state=engine.TransactionState.SUCCESS,
                restart_required=True,lifecycle="home_assistant_restart")
        with patch.object(engine,"async_execute_deployment",run):
            await self.start(offer["challenge"])
            await self.batch.close()
        state=await self.batch.status()
        self.assertEqual(state["status"],"stopped")
        self.assertEqual(calls,["safe1","safe2"])
        self.assertEqual([x["status"] for x in state["items"]],
                         ["success","failed","prepared"])
        self.assertEqual((await self.owner.restart_summary())["count"],1)

    async def test_takeover_requires_second_explicit_confirmation(self):
        offer=await self.prepare([self.spec(1)])
        with self.assertRaises(model.OperationContractError):
            await self.batch.take_over(self.b,confirm=False)
        accepted=await self.batch.take_over(self.b,confirm=True)
        self.assertEqual(accepted["challenge"],offer["challenge"])
        with self.assertRaises(model.OperationContractError):
            await self.start(offer["challenge"],client=self.a,confirm=True)
        with self.assertRaises(model.OperationContractError):
            await self.start(offer["challenge"],client=self.b,confirm=False)

    async def test_target_overlap_refuses_full_batch(self):
        specs=[self.spec(1),self.spec(2)]
        with self.assertRaises(model.OperationContractError):
            await self.prepare(specs,targets={
                "safe1":"custom_components/same",
                "safe2":"custom_components/same/child",
            })
        self.assertEqual((await self.batch.status())["status"],"idle")

    async def test_self_updates_execute_after_normal_projects_v1_before_v2(self):
        normal = self.spec(1)
        v1 = {"repository": "TheDaimos/deploy-relay-agent-dev",
              "project_id": "deploy_relay", "ref": "deploy/dev",
              "commit": "b"*40, "token": None}
        v2 = {"repository": "TheDaimos/deploy-relay-agent-v2-dev",
              "project_id": "deploy_relay_agent_v2_dev", "ref": "deploy/dev",
              "commit": "c"*40, "token": None}
        specs = [v2, v1, normal]  # Untrusted browser deliberately reverses order.
        targets = {"deploy_relay": "custom_components/deploy_relay",
                   "deploy_relay_agent_v2_dev": "custom_components/deploy_relay_v2_dev"}
        prepared = await self.prepare(specs, targets=targets)
        expected = ["safe1", "deploy_relay", "deploy_relay_agent_v2_dev"]
        self.assertEqual([i["project_key"] for i in prepared["preparation"]["items"]],
                         expected)
        called = []

        async def fake_engine(_session, mf, *args, **kwargs):
            called.append(mf.project_id)
            return types.SimpleNamespace(
                state=engine.TransactionState.SUCCESS,
                restart_required=True, lifecycle="home_assistant_restart")

        with patch.object(engine, "async_execute_deployment", fake_engine):
            await self.start(prepared["challenge"])
            await self.batch.close()
        self.assertEqual(called, expected)
        result = await self.batch.status()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["current"], 3)
        self.assertEqual((await self.owner.restart_summary())["count"], 3)

    async def test_self_update_wrong_target_or_identity_is_rejected(self):
        valid_v2 = {"repository": "TheDaimos/deploy-relay-agent-v2-dev",
                    "project_id": "deploy_relay_agent_v2_dev", "ref": "deploy/dev",
                    "commit": "c"*40, "token": None}
        with self.assertRaises(model.OperationContractError):
            await self.prepare([valid_v2], targets={
                valid_v2["project_id"]: "custom_components/other"})

        # An unrecognized project may not overwrite the DRA V2 directory.
        with self.assertRaises(model.OperationContractError):
            await self.prepare([self.spec(2)], targets={
                "safe2": "custom_components/deploy_relay_v2_dev"})

        forged = dict(valid_v2, repository="TheDaimos/other-repository")
        with self.assertRaises(model.OperationContractError):
            await self.prepare([forged], targets={
                valid_v2["project_id"]: "custom_components/deploy_relay_v2_dev"})

    async def test_v2_self_update_does_not_start_while_other_job_is_active(self):
        v2 = {"repository": "TheDaimos/deploy-relay-agent-v2-dev",
              "project_id": "deploy_relay_agent_v2_dev", "ref": "deploy/dev",
              "commit": "c"*40, "token": None}
        offer = await self.prepare([v2], targets={
            v2["project_id"]: "custom_components/deploy_relay_v2_dev"})
        # Other independent installations must drain before own runtime is replaced.
        active = asyncio.Event()
        release = asyncio.Event()
        async def fake_engine(_session, mf, *args, **kwargs):
            if mf.project_id == "safe1":
                active.set()
                await release.wait()
            return types.SimpleNamespace(
                state=engine.TransactionState.SUCCESS,
                restart_required=True, lifecycle="home_assistant_restart")
        other = self.frozen(self.spec(1))
        with patch.object(engine, "async_execute_deployment", fake_engine):
            job = await self.owner.start_verified(
                manifest=other.manifest, inventory=other.inventory,
                preview=other.preview, session=None, config_root=self.root,
                request_id="external-"+("d"*32))
            await asyncio.wait_for(active.wait(), 1)
            await self.start(offer["challenge"])
            await self.batch.close()
            release.set()
            await self.owner.wait_completion(job["operation_id"])
        status = await self.batch.status()
        self.assertEqual(status["status"], "stopped")

    async def test_expired_and_invalid_owner_are_rejected(self):
        offer=await self.prepare([self.spec(1)])
        self.batch._expires_at=batch.monotonic()-1
        with self.assertRaises(model.OperationContractError):
            await self.start(offer["challenge"])
        with self.assertRaises(model.OperationContractError):
            await self.batch.take_over(self.b,confirm=True)


if __name__ == "__main__":
    unittest.main()
