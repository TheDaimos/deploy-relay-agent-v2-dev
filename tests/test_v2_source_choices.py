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

    def test_unmanaged_artwork_does_not_break_tree(self):
        source = (ROOT / "source_preflight.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "inspect_tree")
        self.assertIn('managed = any(raw_path.startswith(group["source"] + "/")', source)
        self.assertIn('path = safe_path(raw_path)', source)
        # The actual data-tree case: unrelated artwork contains spaces/Umlauts.
        self.assertIn("if not managed:", source)

    def test_version_guard_uses_parsed_group_fields(self):
        source = (ROOT / "remote_source.py").read_text(encoding="utf-8")
        self.assertIn('extract_version_markers(group["target"], relative, remote_bytes)', source)
        self.assertIn('extract_version_markers(group["target"], relative, local_bytes)', source)
        self.assertNotIn('extract_version_markers(group["id"]', source)

    def test_self_inventory_is_readonly_and_installer_target_still_denied(self):
        preflight = (ROOT / "source_preflight.py").read_text(encoding="utf-8")
        remote = (ROOT / "remote_source.py").read_text(encoding="utf-8")
        socket = (ROOT / "websocket_api.py").read_text(encoding="utf-8")
        self.assertIn('readonly_self and text == "custom_components/deploy_relay_v2_dev"', preflight)
        self.assertIn('target_path(g.get("target"), readonly_self=readonly_self)', preflight)
        self.assertIn('manifest["project_id"] != "deploy_relay_agent_v2_dev"', remote)
        self.assertIn('report["self_preview_readonly"] = True', remote)
        self.assertIn('"self_target_protected": True', socket)
        self.assertIn('"installation_enabled": False', socket)
        self.assertIn('assess_target_claims([report])', socket)
        # All ordinary deployment validation paths keep readonly_self=False.
        self.assertIn('def target_path(path: object, *, readonly_self: bool = False)', preflight)

    def test_second_browser_reconciles_server_side_preview(self):
        frontend = (ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn("await this._pollSourceJob(true)", frontend)
        self.assertIn("async _pollSourceJob(latest = false)", frontend)
        self.assertIn("!latest && this._sourceJobId", frontend)
        self.assertIn("if (!this._sourceJobId) this._sourceJobId = job.operation_id", frontend)

    def test_version_guard_reuses_v1_semantics(self):
        remote = (ROOT / "remote_source.py").read_text(encoding="utf-8")
        tree = ast.parse(remote)
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_version_order")
        scope = {"re": __import__("re")}
        fn.decorator_list = []
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                     "<version-guard>", "exec"), scope)
        compare = scope["_version_order"]
        self.assertEqual(compare("4.11.76", "4.11.75"), "upgrade")
        self.assertEqual(compare("4.11.75", "4.11.76"), "downgrade")
        self.assertEqual(compare("4.11.76", "4.11.76"), "same")
        self.assertEqual(compare("n/a", "unknown"), "unknown")
        self.assertIn("git_blob_sha(remote_bytes) != item", remote)
        self.assertIn("await asyncio.to_thread(\n                _read_local_version_file", remote)
        self.assertIn('report["version_guard"] = await _preview_version_guard(', remote)
        js = (ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn("Versions- und Regressionsprüfung", js)
        self.assertIn("Lokal installiert:", js)
        self.assertIn("Rückschritt erkannt", js)

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
