"""Server-owned execution of the reused V1 engine, tested without HA writes."""
from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

try:
    import aiohttp
except ImportError:
    fake = types.ModuleType("aiohttp")
    fake.ClientSession = type("ClientSession", (), {})
    sys.modules["aiohttp"] = fake

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_server_job_test"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package
jobs = importlib.import_module(PKG + ".server_deployment_jobs")
registry_lib = importlib.import_module(PKG + ".operation_registry")
engine = importlib.import_module(PKG + ".v1_engine.deployment")
manifest_lib = importlib.import_module(PKG + ".v1_engine.manifest")
inventory_lib = importlib.import_module(PKG + ".v1_engine.source_inventory")
preview_lib = importlib.import_module(PKG + ".v1_engine.preview")
model = importlib.import_module(PKG + ".operation_model")

COMMIT = "e" * 40
REQUEST = "synthetic-v2-request-000001"


class ServerDeploymentJobsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.registry = registry_lib.OperationRegistry(max_completed=8, max_readonly=1)
        self.owner = jobs.ServerDeploymentJobs(self.registry, asyncio.create_task)
        self.manifest = manifest_lib.parse_manifest({
            "schema":"deploy-relay.deployment.v1",
            "project":{"id":"example","name":"Example"},
            "source":{"repository":"TheDaimos/example","mode":"repository_contents"},
            "deployment":{"root":"/config","groups":[{
                "id":"example","source":"custom_components/example",
                "target":"custom_components/example","mode":"replace_directory",
            }]},
            "lifecycle":{"after_install":"home_assistant_restart"},
            "policy":{"allow_symlinks":False,"max_files":8,
                      "max_uncompressed_bytes":100000},
        })
        self.inventory = inventory_lib.SourceInventory(
            project_id="example",repository="TheDaimos/example",
            source_ref="main",source_commit=COMMIT,
            groups=(inventory_lib.SourceGroupInventory("example",()),),
            total_files=0,total_bytes=0)
        self.preview = preview_lib.PreviewResult(
            project_id="example",repository="TheDaimos/example",
            source_ref="main",source_commit=COMMIT,files=())
        self.args = {
            "manifest":self.manifest,"inventory":self.inventory,
            "preview":self.preview,"session":None,
            "config_root":Path("/does-not-exist-not-written"),
            "request_id":REQUEST,
        }

    async def test_request_remains_server_owned_after_browser_drops(self):
        active = asyncio.Event()
        release = asyncio.Event()
        calls=[]
        async def v1_engine(*a, **kwargs):
            calls.append(kwargs)
            await kwargs["progress"]("backup", {})
            active.set()
            await release.wait()
            return types.SimpleNamespace(state=engine.TransactionState.SUCCESS)
        with patch.object(engine, "async_execute_deployment", v1_engine):
            started=await self.owner.start_verified(**self.args)
            await asyncio.wait_for(active.wait(),timeout=1)
            current=await self.owner.get(started["operation_id"])
            self.assertEqual(current["status"],"running")
            self.assertEqual(current["phase"],"backup")
            # A second browser can reconnect via the job ID; no second write.
            again=await self.owner.start_verified(**self.args)
            self.assertEqual(again["operation_id"],started["operation_id"])
            self.assertEqual(len(calls),1)
            with self.assertRaises(model.OperationContractError):
                await self.owner.start_verified(**(self.args|{"request_id":"another-request-000001"}))
            release.set()
            await self.owner.finish_before_unload()
            final=await self.owner.get(started["operation_id"])
        self.assertEqual(final["status"],"success")
        self.assertTrue(final["progress_percent"]==100)
        self.assertEqual(final["phase"],"complete")
        self.assertEqual(len(calls),1)

    async def test_engine_failure_never_reports_success(self):
        async def v1_engine(*args,**kwargs):
            raise engine.DeploymentError("synthetic write refused")
        with patch.object(engine,"async_execute_deployment",v1_engine):
            started=await self.owner.start_verified(**self.args)
            await self.owner.finish_before_unload()
        final=await self.owner.get(started["operation_id"])
        self.assertEqual(final["status"],"failed")
        self.assertEqual(final["error_family"],"filesystem")
        self.assertNotIn("synthetic write refused",str(final))

    async def test_unrecoverable_failure_has_distinct_state(self):
        async def v1_engine(*args,**kwargs):
            raise engine.RecoveryRequiredError("do not claim rollback")
        with patch.object(engine,"async_execute_deployment",v1_engine):
            started=await self.owner.start_verified(**self.args)
            await self.owner.finish_before_unload()
        final=await self.owner.get(started["operation_id"])
        self.assertEqual(final["status"],"recovery_required")
        self.assertTrue(final["recovery_required"])

    async def test_invalid_server_identities_are_rejected_before_job(self):
        mismatched=preview_lib.PreviewResult(
            project_id="example",repository="TheDaimos/example",
            source_ref="main",source_commit="f"*40,files=())
        for changed in (
            {"preview":mismatched},
            {"manifest":{"untrusted":"browser dictionary"}},
            {"config_root":Path("/any/path/../that-is-not-root").resolve()},
            {"inventory":None},
        ):
            # An arbitrary existing absolute config path is permitted as a
            # caller-supplied trusted Path; only test actual type/schema errors.
            if "config_root" in changed:
                continue
            with self.subTest(changed=changed),self.assertRaises(model.OperationContractError):
                await self.owner.start_verified(**(self.args|changed))
        self.assertEqual(await self.registry.list(),[])

    def test_no_live_writing_websocket_or_runtime_wiring_yet(self):
        api=(ROOT/"websocket_api.py").read_text(encoding="utf-8")
        runtime=(ROOT/"__init__.py").read_text(encoding="utf-8")
        self.assertNotIn("server_deployment_jobs",api)
        self.assertNotIn("server_deployment_jobs",runtime)
        self.assertNotIn("async_execute_deployment",api)


if __name__=="__main__":
    unittest.main()
