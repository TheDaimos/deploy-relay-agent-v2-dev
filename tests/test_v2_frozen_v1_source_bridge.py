"""Actual pinned V1 manifest/preview bridge, synthetic files and fake Git only."""
from __future__ import annotations

import importlib
from pathlib import Path
import json
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
PKG="_v2_v1_source_bridge_test"
package=types.ModuleType(PKG)
package.__path__=[str(ROOT)]
sys.modules[PKG]=package
bridge=importlib.import_module(PKG+".v1_source_bridge")
inventory_module=importlib.import_module(PKG+".v1_engine.source_inventory")
SHA="a"*40
REPO="TheDaimos/synthetic"
PID="sample_component"


class FakeClient:
    calls=[]
    def __init__(self,session,token):
        self.token=token
    async def async_resolve_commit(self,repository,ref):
        FakeClient.calls.append(("resolve",repository,ref))
        return SHA
    async def async_get_file_bytes(self,repository,path,*,ref,max_bytes):
        FakeClient.calls.append(("manifest",repository,path,ref,max_bytes))
        return json.dumps({
            "schema":"deploy-relay.deployment.v1",
            "project":{"id":PID,"name":"Sample"},
            "source":{"repository":REPO,"mode":"repository_contents"},
            "deployment":{"root":"/config","groups":[{
                "id":"sample_component",
                "source":"custom_components/sample_component",
                "target":"custom_components/sample_component",
                "mode":"replace_directory",
            }]},
            "lifecycle":{"after_install":"home_assistant_restart"},
            "policy":{"allow_symlinks":False,"max_files":12,
                      "max_uncompressed_bytes":10000},
        }).encode()


class SourceBridgeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"config"
        self.target=self.root/"custom_components"/PID
        self.target.mkdir(parents=True)
        (self.target/"main.py").write_bytes(b"original")
        self.props={"session":object(),"repository":REPO,
                    "source_ref":"main","source_commit":SHA,
                    "expected_project_id":PID,
                    "config_root":self.root,"token":None}
        FakeClient.calls.clear()
        self.inventory=inventory_module.SourceInventory(
            project_id=PID,repository=REPO,source_ref="main",source_commit=SHA,
            groups=(inventory_module.SourceGroupInventory(
                group_id=PID,files=(
                    inventory_module.SourceInventoryFile(
                        relative_path="main.py",
                        source_path="custom_components/sample_component/main.py",
                        size=3,sha256="0"*64),)),),
            total_files=1,total_bytes=3)

    async def test_immutable_source_is_prepared_with_real_v1_preview(self):
        async def fake_inventory(session, manifest, **kw):
            self.assertEqual(kw["source_commit"],SHA)
            self.assertEqual(kw["source_ref"],"main")
            return self.inventory
        with patch.object(bridge,"GitHubClient",FakeClient),\
             patch.object(bridge,"async_build_source_inventory",fake_inventory):
            prepared=await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual(prepared.manifest.project_id,PID)
        self.assertEqual(prepared.inventory.source_commit,SHA)
        self.assertEqual(prepared.preview.change_count,1)
        self.assertEqual((self.target/"main.py").read_bytes(),b"original")
        self.assertEqual([v[0] for v in FakeClient.calls],["resolve","manifest"])
        self.assertEqual(FakeClient.calls[1][3],SHA)
        self.assertEqual(FakeClient.calls[1][4],bridge.MAX_MANIFEST_BYTES)

    async def test_transient_rate_limited_inventory_recovers_with_exact_commit(self):
        calls=[]
        async def unstable(session, manifest, **kw):
            calls.append(kw["source_commit"])
            if len(calls) == 1:
                try:
                    raise bridge.GitHubRateLimitError("GitHub API rate limit exhausted")
                except bridge.GitHubRateLimitError as root:
                    raise inventory_module.SourceInventoryError(
                        "cannot read managed source file") from root
            return self.inventory

        async def immediate(_delay):
            return None

        with patch.object(bridge,"GitHubClient",FakeClient),\
             patch.object(bridge,"async_build_source_inventory",unstable),\
             patch.object(bridge.asyncio,"sleep",immediate):
            out=await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual(out.inventory.source_commit,SHA)
        self.assertEqual(calls,[SHA,SHA])
        self.assertEqual([x[0] for x in FakeClient.calls],["resolve","manifest"])

    async def test_secondary_403_rate_limit_can_recover_without_writing(self):
        calls=0
        async def unstable(*args,**kw):
            nonlocal calls
            calls+=1
            if calls == 1:
                try:
                    raise bridge.GitHubAccessError("GitHub access forbidden")
                except bridge.GitHubAccessError as root:
                    raise inventory_module.SourceInventoryError(
                        "cannot read source directory") from root
            return self.inventory
        async def immediate(_delay):
            return None
        with patch.object(bridge,"GitHubClient",FakeClient),\
             patch.object(bridge,"async_build_source_inventory",unstable),\
             patch.object(bridge.asyncio,"sleep",immediate):
            result=await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual(calls,2)
        self.assertEqual(result.inventory.source_commit,SHA)
        self.assertEqual((self.target/"main.py").read_bytes(),b"original")

    async def test_persistent_rate_limit_fails_closed_after_bounded_attempts(self):
        attempts=0
        async def rate_limited(*args,**kwargs):
            nonlocal attempts
            attempts+=1
            try:
                raise bridge.GitHubRateLimitError("GitHub API rate limit exhausted")
            except bridge.GitHubRateLimitError as root:
                raise inventory_module.SourceInventoryError("cannot read directory") from root
        async def immediate(_delay):
            return None

        with patch.object(bridge,"GitHubClient",FakeClient),\
             patch.object(bridge,"async_build_source_inventory",rate_limited),\
             patch.object(bridge.asyncio,"sleep",immediate):
            with self.assertRaises(bridge.SourceBridgeError) as raised:
                await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual(str(raised.exception),"inventory_transient_exhausted")
        self.assertEqual(raised.exception.check_stage,"inventory")
        self.assertEqual(attempts,3)
        self.assertEqual((self.target/"main.py").read_bytes(),b"original")

    async def test_unsafe_inventory_never_retried_or_accepted(self):
        attempts=0
        async def unsafe(*args,**kwargs):
            nonlocal attempts
            attempts+=1
            raise inventory_module.SourceInventoryError(
                "unsafe source path returned by GitHub")
        async def forbidden(*args,**kwargs):
            nonlocal attempts
            attempts+=1
            try:
                from_exception=bridge.GitHubApiError("GitHub access forbidden")
                raise from_exception
            except bridge.GitHubApiError as root:
                raise inventory_module.SourceInventoryError("cannot read directory") from root
        with patch.object(bridge,"GitHubClient",FakeClient),\
             patch.object(bridge,"async_build_source_inventory",unsafe):
            with self.assertRaisesRegex(bridge.SourceBridgeError,"inventory_unsafe_path"):
                await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual(attempts,1)
        with patch.object(bridge,"GitHubClient",FakeClient),\
             patch.object(bridge,"async_build_source_inventory",forbidden):
            with self.assertRaisesRegex(bridge.SourceBridgeError,"inventory_read_unavailable"):
                await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual(attempts,2)

    async def test_unpinned_or_malformed_input_never_calls_github(self):
        for values in (
            {"source_commit":"main"},
            {"source_ref":""},
            {"repository":"https://invalid.example"},
            {"expected_project_id":"../../oops"},
            {"manifest_path":"secrets.yaml"},
            {"config_root":"config-as-string"},
        ):
            with self.subTest(values=values),self.assertRaises(bridge.SourceBridgeError):
                await bridge.prepare_frozen_v1_source(**(self.props|values))
        self.assertEqual(FakeClient.calls,[])

    async def test_different_resolved_commit_aborts_before_manifest(self):
        class Changed(FakeClient):
            async def async_resolve_commit(self,repository,ref):
                return "b"*40
        with patch.object(bridge,"GitHubClient",Changed):
            with self.assertRaisesRegex(bridge.SourceBridgeError,"moved"):
                await bridge.prepare_frozen_v1_source(**self.props)

    async def test_source_identity_mismatch_refused_without_project_change(self):
        class WrongRepo(FakeClient):
            async def async_get_file_bytes(self,*a,**kw):
                return json.dumps({"schema":"wrong"}).encode()
        with patch.object(bridge,"GitHubClient",WrongRepo):
            with self.assertRaises(bridge.SourceBridgeError):
                await bridge.prepare_frozen_v1_source(**self.props)
        self.assertEqual((self.target/"main.py").read_bytes(),b"original")

    async def test_symlink_root_fails_before_github(self):
        symlink=Path(self.tmp.name)/"linked"
        symlink.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(bridge.SourceBridgeError):
            await bridge.prepare_frozen_v1_source(
                **(self.props|{"config_root":symlink}))


if __name__=="__main__":
    unittest.main()
