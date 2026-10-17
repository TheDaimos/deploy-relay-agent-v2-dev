"""Immutable per-project version review, including missing/altered local targets."""
from __future__ import annotations
import asyncio
from dataclasses import replace
from hashlib import sha256
import tempfile
from pathlib import Path
import unittest

try:
    import aiohttp
except ImportError:
    import sys
    import types
    sys.modules["aiohttp"] = types.ModuleType("aiohttp")
    sys.modules["aiohttp"].ClientSession = object

import importlib
import sys
import types
BASE = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_review_test"
m = types.ModuleType(PKG)
m.__path__ = [str(BASE)]
sys.modules[PKG] = m
review = importlib.import_module(PKG + ".batch_version_summary")
manifest_mod = importlib.import_module(PKG + ".v1_engine.manifest")
source_mod = importlib.import_module(PKG + ".v1_engine.source_inventory")
preview_mod = importlib.import_module(PKG + ".v1_engine.preview")
bridge = importlib.import_module(PKG + ".v1_source_bridge")
marker_mod = importlib.import_module(PKG + ".v1_engine.version_markers")


class VersionReviewTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.dir = self.root / "custom_components" / "weather_router"
        self.dir.mkdir(parents=True)

    def prepared(self, local_version="0.10.151", *, remote_version="0.10.152", changed_local=False):
        remote = f'BUILD_VERSION = "{remote_version}"\n'.encode()
        target = self.dir / "build_info.py"
        payload = f'BUILD_VERSION = "{local_version}"\n'.encode()
        target.write_bytes(payload if not changed_local else b'BUILD_VERSION = "tampered"\n')
        mf = manifest_mod.parse_manifest({
            "schema":"deploy-relay.deployment.v1",
            "project":{"id":"weather_router","name":"WeatherRouter"},
            "source":{"repository":"TheDaimos/weather-router-dev","mode":"repository_contents"},
            "deployment":{"root":"/config","groups":[{
                "id":"main","source":"custom_components/weather_router",
                "target":"custom_components/weather_router","mode":"replace_directory"
            }]},
            "lifecycle":{"after_install":"home_assistant_restart"},
            "policy":{"allow_symlinks":False,"max_files":20,
                      "max_uncompressed_bytes":20000},
        })
        marks = marker_mod.extract_version_markers("main","build_info.py",remote)
        inventory=source_mod.SourceInventory(
            project_id="weather_router",repository="TheDaimos/weather-router-dev",
            source_ref="deploy/dev",source_commit="a"*40,
            groups=(source_mod.SourceGroupInventory("main",()),),
            total_files=1,total_bytes=len(remote),version_markers=marks,
        )
        old_digest = sha256(payload).hexdigest()
        preview=preview_mod.PreviewResult(
            "weather_router","TheDaimos/weather-router-dev","deploy/dev","a"*40,
            (preview_mod.PreviewFile(
                "main",preview_mod.PreviewOperation.CHANGE,
                "custom_components/weather_router/build_info.py",
                "custom_components/weather_router/build_info.py",
                sha256(remote).hexdigest(), old_digest, len(remote),len(payload),
            ),),
        )
        return bridge.PreparedV1Source(mf,inventory,preview)

    async def test_exact_verified_current_and_new_versions(self):
        data=await review.prepared_version_summary(self.prepared(),config_root=self.root)
        self.assertEqual(data,{"installed_version":"0.10.151",
                                "new_version":"0.10.152",
                                "version_marker":"BUILD_VERSION",
                                "version_status":"verified_pair"})

    async def test_changed_local_version_is_never_asserted(self):
        data=await review.prepared_version_summary(
            self.prepared(changed_local=True),config_root=self.root)
        self.assertIsNone(data["installed_version"])
        self.assertEqual(data["new_version"],"0.10.152")
        self.assertEqual(data["version_status"],"source_only")

    async def test_missing_local_version_does_not_invent_install(self):
        frozen=self.prepared()
        (self.dir/"build_info.py").unlink()
        data=await review.prepared_version_summary(frozen,config_root=self.root)
        self.assertIsNone(data["installed_version"])
        self.assertEqual(data["new_version"],"0.10.152")

    async def test_conflicting_source_markers_are_not_guessed(self):
        frozen=self.prepared()
        second=marker_mod.VersionMarker("main","const.py","BUILD_VERSION","0.10.153",120)
        inv=replace(frozen.inventory,version_markers=frozen.inventory.version_markers+(second,))
        data=await review.prepared_version_summary(replace(frozen,inventory=inv),config_root=self.root)
        self.assertIsNone(data["installed_version"])
        # Same rank, two contradictory source versions: cannot claim a new version.
        self.assertIsNone(data["new_version"])
        self.assertEqual(data["version_status"],"unknown")

    async def test_symlink_path_cannot_be_used_for_version(self):
        frozen=self.prepared()
        (self.dir/"build_info.py").unlink()
        try:
            (self.dir/"build_info.py").symlink_to(self.root/"other")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        data=await review.prepared_version_summary(frozen,config_root=self.root)
        self.assertIsNone(data["installed_version"])


if __name__=="__main__":
    unittest.main()
