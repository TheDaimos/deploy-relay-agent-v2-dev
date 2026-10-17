"""Actual real-file V1 previews distributed across independently managed groups.

All files are synthetic and temporary. A controlled thread-backed stand-in
checks the exact scheduling and V1 results in stdlib-only CI; the runtime
executor is ProcessPoolExecutor(spawn).
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
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
    stub=types.ModuleType("aiohttp")
    stub.ClientSession=type("ClientSession", (), {})
    sys.modules["aiohttp"]=stub

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"deploy_relay_v2_dev"
PKG="_v2_multicore_preview_test"
package=types.ModuleType(PKG)
package.__path__=[str(ROOT)]
sys.modules[PKG]=package
multi=importlib.import_module(PKG+".parallel_preview")
manifest_mod=importlib.import_module(PKG+".v1_engine.manifest")
source_mod=importlib.import_module(PKG+".v1_engine.source_inventory")
preview_mod=importlib.import_module(PKG+".v1_engine.preview")
sha=__import__("hashlib").sha256


class PreviewParallelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"config"
        self.root.mkdir()
        self.source=[]
        for name in ("alpha", "beta"):
            target=self.root/"custom_components"/name
            target.mkdir(parents=True)
            (target/"main.py").write_bytes(b"old-"+name.encode())
            self.source.append(source_mod.SourceGroupInventory(
                name,(source_mod.SourceInventoryFile(
                    "main.py",f"custom_components/{name}/main.py",
                    len(b"new-"+name.encode()),sha(b"new-"+name.encode()).hexdigest()),)
            ))
        self.manifest=manifest_mod.parse_manifest({
            "schema":"deploy-relay.deployment.v1",
            "project":{"id":"example","name":"Example"},
            "source":{"repository":"TheDaimos/example","mode":"repository_contents"},
            "deployment":{"root":"/config","groups":[{
                "id":name,"source":f"custom_components/{name}",
                "target":f"custom_components/{name}",
                "mode":"replace_directory",
            } for name in ("alpha","beta")]},
            "lifecycle":{"after_install":"none"},
            "policy":{"allow_symlinks":False,"max_files":16,
                      "max_uncompressed_bytes":4096},
        })
        self.inventory=source_mod.SourceInventory(
            project_id="example",repository="TheDaimos/example",
            source_ref="deploy/dev",source_commit="b"*40,
            groups=tuple(self.source),total_files=2,total_bytes=16)

    async def test_two_real_groups_maintain_exact_v1_result_and_order(self):
        baseline=preview_mod.build_preview(self.manifest,self.inventory,
                                           config_root=self.root)
        created=[]
        class SpyProcessPool(ThreadPoolExecutor):
            def __init__(self,*,max_workers,mp_context):
                created.append((max_workers,mp_context.get_start_method()))
                super().__init__(max_workers=max_workers)
        with patch.object(multi,"ProcessPoolExecutor",SpyProcessPool), \
             patch.object(multi.os,"cpu_count",return_value=4):
            parallel=await multi.async_build_parallel_preview(
                self.manifest,self.inventory,config_root=self.root,max_workers=2)
        self.assertEqual(parallel,baseline)
        self.assertEqual(parallel.change_count,2)
        self.assertEqual(created,[(2,"spawn")])
        for name in ("alpha","beta"):
            self.assertEqual((self.root/"custom_components"/name/"main.py").read_bytes(),
                             b"old-"+name.encode())

    async def test_single_group_keeps_original_v1_path_without_subprocess(self):
        from dataclasses import replace
        manifest=replace(self.manifest,groups=(self.manifest.groups[0],))
        source=replace(self.inventory,groups=(self.inventory.groups[0],))
        with patch.object(multi,"ProcessPoolExecutor",
                          side_effect=AssertionError("process used")):
            result=await multi.async_build_parallel_preview(
                manifest,source,config_root=self.root,max_workers=4)
        self.assertEqual(result.change_count,1)

    async def test_no_multi_core_available_uses_v1_path(self):
        with patch.object(multi.os,"cpu_count",return_value=1), \
             patch.object(multi,"ProcessPoolExecutor",
                          side_effect=AssertionError("process used")):
            output=await multi.async_build_parallel_preview(
                self.manifest,self.inventory,config_root=self.root,max_workers=4)
        self.assertEqual(output.change_count,2)

    async def test_invalid_worker_limits_or_group_identity_fail(self):
        from dataclasses import replace
        for workers in (0,-1,5,True):
            with self.subTest(workers=workers), self.assertRaises(ValueError):
                await multi.async_build_parallel_preview(
                    self.manifest,self.inventory,config_root=self.root,
                    max_workers=workers)
        corrupt=replace(self.inventory,groups=(
            self.inventory.groups[0],self.inventory.groups[0]))
        with self.assertRaises(ValueError):
            await multi.async_build_parallel_preview(
                self.manifest,corrupt,config_root=self.root)
        overlapping=replace(self.manifest,groups=(
            self.manifest.groups[0],
            replace(self.manifest.groups[1],target="custom_components/alpha/sub")))
        with self.assertRaises(ValueError):
            await multi.async_build_parallel_preview(
                overlapping,self.inventory,config_root=self.root)

    async def test_process_startup_failure_falls_back_to_identical_v1_preview(self):
        from concurrent.futures.process import BrokenProcessPool
        with patch.object(multi,"ProcessPoolExecutor",
                          side_effect=BrokenProcessPool("unavailable")), \
             patch.object(multi.os,"cpu_count",return_value=4):
            result=await multi.async_build_parallel_preview(
                self.manifest,self.inventory,config_root=self.root)
        self.assertEqual(result,
            preview_mod.build_preview(self.manifest,self.inventory,config_root=self.root))

    async def test_symlinks_are_rejected_by_real_v1_in_worker(self):
        target=self.root/"custom_components"/"alpha"/"main.py"
        target.unlink()
        outside=Path(self.temp.name)/"outside"
        outside.write_bytes(b"unmodified")
        target.symlink_to(outside)
        with patch.object(multi,"ProcessPoolExecutor",ThreadPoolExecutor), \
             patch.object(multi.os,"cpu_count",return_value=4):
            # ThreadPoolExecutor accepts the extra mp_context? Not here: call
            # the same worker without changing the safety of V1 preview.
            with self.assertRaises(preview_mod.PreviewError):
                await asyncio.to_thread(
                    multi._group_preview,self.manifest,self.inventory,0,self.root)
        self.assertEqual(outside.read_bytes(),b"unmodified")


if __name__=="__main__":
    unittest.main()
