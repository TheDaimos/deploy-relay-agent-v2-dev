"""Guard against accidentally deploying V2 over DRA V1 on the same HA-DEV."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = "custom_components/deploy_relay"
LAB_PATH = "custom_components/deploy_relay_v2_dev"
LAB_ROOT = ROOT / LAB_PATH


class LabIsolationContracts(unittest.TestCase):
    def test_manifest_only_installs_separate_test_directory(self):
        manifest = json.loads((ROOT / "deploy-relay.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "deploy-relay.deployment.v1")
        self.assertEqual(manifest["source"]["repository"], "TheDaimos/deploy-relay-agent-v2-dev")
        self.assertEqual(manifest["source"]["mode"], "repository_contents")
        self.assertEqual(manifest["deployment"]["root"], "/config")
        groups = manifest["deployment"]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["source"], LAB_PATH)
        self.assertEqual(groups[0]["target"], LAB_PATH)
        self.assertEqual(groups[0]["mode"], "replace_directory")
        self.assertEqual(manifest["project"]["id"], "deploy_relay_agent_v2_dev")
        self.assertIs(manifest["policy"]["allow_symlinks"], False)
        self.assertEqual(manifest["lifecycle"]["after_install"], "home_assistant_restart")
        self.assertTrue(all(not g["target"].startswith(V1_PATH + "/") for g in groups))

    def test_ha_integration_domain_is_not_v1_domain(self):
        manifest = json.loads((LAB_ROOT / "manifest.json").read_text(encoding="utf-8"))
        v1 = json.loads((ROOT / V1_PATH / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain"], "deploy_relay_v2_dev")
        self.assertNotEqual(manifest["domain"], v1["domain"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertEqual(manifest["requirements"], [])

    def test_frontend_and_websocket_namespace_is_unique(self):
        const = (LAB_ROOT / "const.py").read_text(encoding="utf-8")
        sockets = (LAB_ROOT / "websocket_api.py").read_text(encoding="utf-8")
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('PANEL_PATH: Final = "dra-v2-dev-lab"', const)
        self.assertIn('STATIC_PATH: Final = "/dra_v2_dev_static"', const)
        self.assertIn('PANEL_ELEMENT: Final = "dra-v2-dev-lab-panel"', const)
        self.assertEqual(len(re.findall(r'probatio.Required\("type"\): "deploy_relay_v2_dev/test/', sockets)), 8)
        self.assertEqual(len(re.findall(r'probatio.Required\("type"\): "deploy_relay_v2_dev/projects/', sockets)), 5)
        self.assertEqual(sockets.count("@websocket_api.require_admin"), 13)
        self.assertNotIn('"deploy_relay/panel/', sockets)
        self.assertNotIn('"deploy_relay/panel/', frontend)
        self.assertNotIn("deploy-relay-panel", frontend)
        self.assertNotIn("deploy-relay-diagnostics-panel", frontend)

    def test_no_other_integration_can_be_deployed_by_this_manifest(self):
        manifest = json.loads((ROOT / "deploy-relay.json").read_text(encoding="utf-8"))
        approved_files = list(LAB_ROOT.rglob("*"))
        self.assertTrue(approved_files)
        self.assertLessEqual(len([f for f in approved_files if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc"]), manifest["policy"]["max_files"])
        self.assertLessEqual(sum(f.stat().st_size for f in approved_files if f.is_file()),
                             manifest["policy"]["max_uncompressed_bytes"])
        for item in approved_files:
            self.assertFalse(item.is_symlink())
            self.assertTrue(item.resolve().is_relative_to(LAB_ROOT.resolve()))

    def test_no_mutating_ws_or_v1_registry_access(self):
        source = (LAB_ROOT / "websocket_api.py").read_text(encoding="utf-8")
        for forbidden in (
            "deployment_lock", "async_execute_deployment",
            "restore_backup", "set_mode", "select_source",
            "install_project", "async_update_subentry",
            "async_add_executor_job", "GitHubClient",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn('project_key="lab_readonly_preview"', source)
        self.assertIn("await asyncio.sleep(1)", source)
        self.assertIn('store["runtime"]', (LAB_ROOT / "__init__.py").read_text(encoding="utf-8"))

    def test_async_ws_handlers_are_scheduled_and_admin_guarded(self):
        sockets = (LAB_ROOT / "websocket_api.py").read_text(encoding="utf-8")
        self.assertEqual(sockets.count("@websocket_api.async_response"), 13)
        self.assertEqual(sockets.count("@websocket_api.require_admin"), 13)
        self.assertEqual(sockets.count("@websocket_api.websocket_command("), 13)
        self.assertIn("import probatio", sockets)
        self.assertNotIn("import voluptuous", sockets)
        for handler in ("async_state", "async_start", "async_measure", "async_multicore",
                        "async_all", "async_get",
                        "async_git_configure", "async_git_export",
                        "async_projects_list", "async_projects_v1_preview",
                        "async_projects_import_v1", "async_projects_add",
                        "async_projects_retention"):
            self.assertIn(
                chr(10).join((
                    "@websocket_api.require_admin",
                    "@websocket_api.async_response",
                    "async def " + handler + "(",
                )),
                sockets,
            )

    def test_config_flow_uses_same_ha_schema_contract_as_v1(self):
        flow = (LAB_ROOT / "config_flow.py").read_text(encoding="utf-8")
        self.assertIn("import probatio", flow)
        self.assertIn("probatio.Schema({})", flow)
        self.assertNotIn("import voluptuous", flow)

    def test_idle_panel_has_no_recurring_timer(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn("if (this.isConnected && this._active())", frontend)
        self.assertNotIn("setInterval(", frontend)
        self.assertIn("this._observeCountdown(this._operation)", frontend)
        self.assertIn("this._syncCountdownTimer()", frontend)
        self.assertIn("id=\"remaining\"", frontend)
        self.assertIn("Math.max(1, (op.total_count === 87 ? 80 : 40) - step - elapsed)", frontend)
        self.assertIn("disconnectedCallback()", frontend)

    def test_config_flow_uses_test_domain_not_v1_domain(self):
        source = (LAB_ROOT / "config_flow.py").read_text(encoding="utf-8")
        self.assertIn("ConfigFlow, domain=DOMAIN", source)
        self.assertIn("self._abort_if_unique_id_configured()", source)
        self.assertNotIn("deploy_relay/panel", source)

    def test_readonly_trial_duration_is_40_seconds(self):
        """Longer synthetic-only HA restart window, no new write routes."""
        const = (LAB_ROOT / "const.py").read_text(encoding="utf-8")
        sockets = (LAB_ROOT / "websocket_api.py").read_text(encoding="utf-8")
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn("READONLY_TEST_STEPS: Final = 40", const)
        self.assertIn("for index in range(1, READONLY_TEST_STEPS + 1):", sockets)
        self.assertIn("await asyncio.sleep(1)", sockets)
        self.assertIn("await progress(OperationPhase.INVENTORY, index, READONLY_TEST_STEPS)", sockets)
        self.assertIn("40-Sekunden-Test", frontend)
        self.assertIn("Messlauf starten (40 s)", frontend)
        self.assertIn("Alle Tests nacheinander starten", frontend)
        self.assertIn("Mehrkern-Diagnose (1 / 2 / 4 / 6 / 8 / 10 / 12)", frontend)
        self.assertIn("No project or file access", (LAB_ROOT / "readonly_benchmark.py").read_text(encoding="utf-8"))
        self.assertNotIn("20-Sekunden-Test", frontend)
        self.assertNotIn("for index in range(1, 21):", sockets)
        self.assertEqual(sockets.count("@websocket_api.require_admin"), 13)


if __name__ == "__main__":
    unittest.main()
