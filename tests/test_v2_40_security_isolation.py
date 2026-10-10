"""V2-40 static protections for the only HA-DEV instance and V1."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "custom_components" / "deploy_relay_v2_dev"


class JournalIsolationContracts(unittest.TestCase):
    def test_fixed_unique_ha_storage_key(self):
        source = (LAB / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.journal")', source)
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.projects")', source)
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.settings")', source)
        self.assertIn("await journal.load()", source)
        self.assertIn("on_registered=journal.capture", source)
        self.assertIn("on_terminal=journal.capture", source)
        self.assertNotIn('Store(hass, 1, "deploy_relay.', source)

    def test_journal_module_has_no_filesystem_or_task_access(self):
        source = (LAB / "operation_journal.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [
            node.module if isinstance(node, ast.ImportFrom) else alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in (node.names if isinstance(node, ast.Import) else [None])
        ]
        names = {n for n in imports if n}
        for forbidden in ("os", "pathlib", "subprocess", "homeassistant",
                          "shutil", "requests", "httpx"):
            self.assertFalse(any(n == forbidden or n.startswith(forbidden + ".")
                                 for n in names))
        for forbidden in ("create_task(", "async_create_background_task(",
                          "asyncio.sleep(", "open(", "eval(", "exec("):
            self.assertNotIn(forbidden, source)
        self.assertIn('SCHEMA = "dra-v2-dev-journal.v1"', source)
        self.assertIn("MAX_RECORDS = 12", source)
        self.assertIn("MAX_EVENTS = 48", source)

    def test_deployment_still_only_targets_v2_testlab(self):
        manifest = json.loads((ROOT / "deploy-relay.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["deployment"]["groups"]), 1)
        self.assertEqual(manifest["deployment"]["groups"][0]["target"],
                         "custom_components/deploy_relay_v2_dev")
        self.assertTrue((ROOT / "custom_components/deploy_relay" / "manifest.json").exists())

    def test_admin_only_history_without_mutating_routes(self):
        source = (LAB / "websocket_api.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("@websocket_api.require_admin"), 25)
        self.assertEqual(source.count("@websocket_api.websocket_command("), 25)
        self.assertIn("await runtime.journal.list(limit=12)", source)
        self.assertIn('project_key="lab_readonly_preview"', source)
        self.assertNotIn("async_add_executor_job", source)
        self.assertIn('await runtime.journal.get(msg["operation_id"])', source)
        self.assertNotIn('deploy_relay/panel/', source)
        for word in ('"install"', '"restore"', '"restart"', '"delete"'):
            self.assertNotIn(word, source)


    def test_git_export_credentials_never_share_v1_or_journal_store(self):
        setup = (LAB / "__init__.py").read_text(encoding="utf-8")
        ws = (LAB / "websocket_api.py").read_text(encoding="utf-8")
        panel = (LAB / "frontend" / "lab.js").read_text(encoding="utf-8")
        writer = (LAB / "git_measurement_export.py").read_text(encoding="utf-8")
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.archive_queue")', setup)
        self.assertNotIn('Store(hass, 1, "deploy_relay_v2_dev.git_auth")', setup)
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.git_read_auth")', setup)
        self.assertIn("source_auth=source_auth", setup)
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.journal")', setup)
        self.assertNotIn('Store(hass, 1, "deploy_relay.git_auth")', setup)
        self.assertEqual(ws.count("@websocket_api.require_admin"), 25)
        self.assertIn("await runtime.git_export.export(summary, version=VERSION)", ws)
        self.assertNotIn("token", (LAB / "readonly_benchmark.py").read_text(encoding="utf-8"))
        self.assertIn("<h2>02 · Diagnoseexport</h2>", panel)
        self.assertIn('id="git-dialog-open"', panel)
        self.assertIn('role="dialog"', panel)
        self.assertNotIn('id="git-token"', panel)
        self.assertNotIn("deploy-relay-agent-v2-dev/blob/main/.deploy-relay", panel)
        self.assertIn('type="password"', panel)
        self.assertIn("asyncio.timeout(12)", writer)
        self.assertNotIn('REPOSITORY = "TheDaimos/Project-Log-And-Export"', writer)
        self.assertIn("validate_archive_repository", writer)
        self.assertIn("async def async_download_json", ws)
        self.assertIn("JSON herunterladen", panel)
        self.assertIn("git-dialog-repo", panel)
        self.assertIn("git-dialog-token", panel)
        self.assertIn('Store(hass, 1, "deploy_relay_v2_dev.archive_credentials")', setup)
        self.assertIn("kein Standardrepository", panel)
        self.assertIn("SERVER_TOKEN_ENV", writer)
        self.assertNotIn("deploy_relay_agent_v1", writer)
        self.assertNotIn("custom_components/deploy_relay/", writer)



if __name__ == "__main__":
    unittest.main()
