"""Regression checks for the read-only Git source picker (no HA installation)."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"

class SourceChoicesContract(unittest.TestCase):
    def test_python_source_and_registration(self):
        remote = (ROOT / "remote_source.py").read_text(encoding="utf-8")
        socket = (ROOT / "websocket_api.py").read_text(encoding="utf-8")
        ast.parse(remote)
        ast.parse(socket)
        self.assertIn("async def inspect_source_choices(", remote)
        self.assertIn('("branch", "branches"), ("tag", "tags")', remote)
        self.assertIn("allow_list=True", remote)
        self.assertIn("len(rows) > 100", remote)
        self.assertIn('probatio.Required("type"): "deploy_relay_v2_dev/projects/source_choices"', socket)
        self.assertIn("@websocket_api.require_admin", socket)
        self.assertIn("async_projects_source_choices, async_projects_source_head", socket)
        self.assertIn("runtime.project_auth.token(repo) or runtime.source_auth.token", socket)
        self.assertIn("runtime.source_scan_lock", socket)

    def test_browser_selector_preserves_sha_bound_preview(self):
        js = (ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('id="dra-main-choice"', js)
        self.assertIn("async _loadSourceChoices()", js)
        self.assertIn("_applySourceChoice(ref)", js)
        self.assertIn('this._deploymentPreviewRef = null;', js)
        self.assertIn("this._mainSourceRef = ref;", js)
        self.assertIn('id="dra-main-ref"', js)  # Manual SHA/ref remains available.
        self.assertIn('this._deploymentPreviewRef === this._mainSourceRef.trim()', js)
        self.assertIn("this._sourcePreview?.sources_verified === true", js)

if __name__ == "__main__":
    unittest.main()
