"""Exercise the actual V1 install/backup/rollback engine in a V2-only namespace.

Only temporary synthetic filesystem targets are ever written. This is a
code-level integration test; it does NOT make a live V2 deployment available.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

try:
    from aiohttp import ClientSession
except ImportError:
    # GitHub Actions runs stdlib-only contract tests; no network client used.
    fake = types.ModuleType("aiohttp")
    fake.ClientSession = type("ClientSession", (), {})
    sys.modules["aiohttp"] = fake

ROOT = Path(__file__).resolve().parents[1] / "custom_components"
V1 = ROOT / "deploy_relay"
ENGINE = ROOT / "deploy_relay_v2_dev" / "v1_engine"
PKG = "_v2_v1_engine_isolated"
package = types.ModuleType(PKG)
package.__path__ = [str(ENGINE)]
sys.modules[PKG] = package
manifest_module = importlib.import_module(PKG + ".manifest")
preview_module = importlib.import_module(PKG + ".preview")
source_module = importlib.import_module(PKG + ".source_inventory")
deployment = importlib.import_module(PKG + ".deployment")
transaction = importlib.import_module(PKG + ".transaction")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class V1EngineReuseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.config = Path(self.folder.name) / "config"
        self.target = self.config / "custom_components" / "sample_component"
        self.target.mkdir(parents=True)
        self.existing = self.target / "main.py"
        self.existing.write_bytes(b"previous V1-install content")
        self.v1_private = self.config / "deploy_relay"
        self.v1_private.mkdir()
        (self.v1_private / "unchanged.txt").write_bytes(b"V1 MUST NOT BE TOUCHED")
        self.input_manifest = {
            "schema": "deploy-relay.deployment.v1",
            "project": {"id": "sample_component", "name": "Sample"},
            "source": {"repository": "TheDaimos/sample", "mode": "repository_contents"},
            "deployment": {
                "root": "/config",
                "groups": [{
                    "id": "sample_component", "mode": "replace_directory",
                    "source": "custom_components/sample_component",
                    "target": "custom_components/sample_component",
                }],
            },
            "lifecycle": {"after_install": "home_assistant_restart"},
            "policy": {"allow_symlinks": False, "max_files": 12,
                       "max_uncompressed_bytes": 100000},
        }
        self.manifest = manifest_module.parse_manifest(self.input_manifest,
                                                         expected_repository="TheDaimos/sample")
        self.new_bytes = b"replacement from fixed source commit"
        self.added_bytes = b"new entry"
        files = (
            source_module.SourceInventoryFile("main.py",
                "custom_components/sample_component/main.py",
                len(self.new_bytes), sha(self.new_bytes)),
            source_module.SourceInventoryFile("extra.py",
                "custom_components/sample_component/extra.py",
                len(self.added_bytes), sha(self.added_bytes)),
        )
        self.inventory = source_module.SourceInventory(
            project_id="sample_component", repository="TheDaimos/sample",
            source_ref="main", source_commit="a" * 40,
            groups=(source_module.SourceGroupInventory(
                group_id="sample_component", files=files),),
            total_files=2,total_bytes=len(self.new_bytes)+len(self.added_bytes),
        )
        self.preview = preview_module.build_preview(
            self.manifest, self.inventory, config_root=self.config)

    def _assert_v1_untouched(self):
        self.assertEqual((self.v1_private/"unchanged.txt").read_bytes(),
                         b"V1 MUST NOT BE TOUCHED")

    async def _stager(self, session, manifest, inventory, *, token, config_root,
                      transaction_id, progress, blocking_executor):
        stage = deployment._prepare_staging_root(config_root, transaction_id)
        for name, data in (("main.py", self.new_bytes),("extra.py",self.added_bytes)):
            dest = stage / "files" / "sample_component" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        return stage

    def test_reused_modules_match_existing_public_v1_source(self):
        names = ("repository.py", "version_markers.py", "runtime_policy.py",
                 "github_client.py", "source_inventory.py", "preview.py",
                 "manifest.py", "lifecycle_policy.py", "path_policy.py",
                 "planner.py", "transaction.py", "integrity.py")
        for name in names:
            with self.subTest(name=name):
                self.assertEqual((ENGINE/name).read_bytes(), (V1/name).read_bytes(),
                                 "do not quietly rewrite proven V1 algorithms")
        source=(V1/"deployment.py").read_text(encoding="utf-8")
        adapted=(ENGINE/"deployment.py").read_text(encoding="utf-8")
        self.assertEqual(adapted,
            source.replace("from .github_client import GitHubClient",
                           "from .const import DEPLOY_DATA_DIR\nfrom .github_client import GitHubClient")
                  .replace('"deploy_relay"', "DEPLOY_DATA_DIR"))
        self.assertEqual(deployment.DEPLOY_DATA_DIR,"deploy_relay_v2_dev")
        self.assertNotEqual(deployment.DEPLOY_DATA_DIR,"deploy_relay")

    def test_existing_v1_preview_in_v2_engine_is_real(self):
        self.assertEqual(self.preview.change_count,1)
        self.assertEqual(self.preview.add_count,1)
        self.assertEqual(self.preview.remove_count,0)
        self.assertEqual(self.preview.source_commit,"a"*40)
        self._assert_v1_untouched()

    async def test_real_v1_engine_executes_and_verifies_synthetic_update(self):
        statuses = []
        async def report(phase, details):
            statuses.append(phase)
        with patch.object(deployment,"async_materialize_staging",self._stager):
            out = await deployment.async_execute_deployment(
                None,self.manifest,self.inventory,self.preview,
                token=None,config_root=self.config,progress=report)
        self.assertIs(out.state,transaction.TransactionState.SUCCESS)
        self.assertEqual(out.changed_files,2)
        self.assertTrue(out.restart_required)
        self.assertEqual(self.existing.read_bytes(),self.new_bytes)
        self.assertEqual((self.target/"extra.py").read_bytes(),self.added_bytes)
        self.assertTrue(Path(out.backup_path).is_dir())
        self.assertTrue(Path(out.journal_path).is_file())
        self.assertTrue(str(out.backup_path).startswith(
            str(self.config/"deploy_relay_v2_dev"/"backups")))
        self.assertEqual(json.loads(Path(out.journal_path).read_text())["state"],
                         "success")
        self.assertIn("backup",statuses)
        self.assertIn("install",statuses)
        self._assert_v1_untouched()

    async def test_actual_rollback_restores_original_bytes_on_install_failure(self):
        statuses = []
        async def report(phase, details):
            statuses.append(phase)
        with patch.object(deployment,"async_materialize_staging",self._stager),\
             patch.object(deployment,"_verify_installed",
                          side_effect=deployment.DeploymentError("synthetic post-write failure")):
            with self.assertRaisesRegex(deployment.DeploymentError,
                                         "automatic rollback succeeded"):
                await deployment.async_execute_deployment(
                    None,self.manifest,self.inventory,self.preview,token=None,
                    config_root=self.config,progress=report)
        self.assertEqual(self.existing.read_bytes(), b"previous V1-install content")
        self.assertFalse((self.target/"extra.py").exists())
        self.assertIn("rollback",statuses)
        transactions=list((self.config/"deploy_relay_v2_dev"/"transactions").glob("*.json"))
        self.assertEqual(len(transactions),1)
        self.assertEqual(json.loads(transactions[0].read_text())["state"],"rolled_back")
        self._assert_v1_untouched()

    async def test_preflight_bad_staging_never_alters_target(self):
        async def broken_stager(*args, **kwargs):
            raise deployment.DeploymentError("synthetic source unavailable")
        with patch.object(deployment,"async_materialize_staging",broken_stager):
            with self.assertRaises(deployment.DeploymentError):
                await deployment.async_execute_deployment(
                    None,self.manifest,self.inventory,self.preview,token=None,
                    config_root=self.config)
        self.assertEqual(self.existing.read_bytes(),b"previous V1-install content")
        self.assertFalse((self.target/"extra.py").exists())
        self._assert_v1_untouched()

    def test_target_symlink_fails_preview_without_writes(self):
        self.existing.unlink()
        outside=Path(self.folder.name)/"outside.py"
        outside.write_bytes(b"do not change")
        self.existing.symlink_to(outside)
        with self.assertRaises(preview_module.PreviewError):
            preview_module.build_preview(self.manifest,self.inventory,
                                         config_root=self.config)
        self.assertEqual(outside.read_bytes(),b"do not change")
        self._assert_v1_untouched()


if __name__=="__main__":
    unittest.main()
