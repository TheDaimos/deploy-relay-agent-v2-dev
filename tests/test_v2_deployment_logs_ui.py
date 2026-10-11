"""Read-only deployment logs UI: one compact gold pill, opt-in safe exports."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "custom_components" / "deploy_relay_v2_dev"


class DeploymentLogUiContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = (LAB / "frontend" / "lab.js").read_text(encoding="utf-8")
        cls.ws = (LAB / "websocket_api.py").read_text(encoding="utf-8")

    def test_small_gold_logs_badge_is_at_deployment_heading(self):
        js = self.frontend
        self.assertIn('class="dra-deployment-heading"', js)
        self.assertIn('id="dra-deployment-logs-toggle" class="dra-logs-pill"', js)
        self.assertIn('border:1px solid #a37b35', js)
        self.assertIn('border-radius:20px', js)
        self.assertIn('aria-expanded="${this._deploymentLogsOpen}"', js)
        self.assertIn('this._deploymentLogsOpen ? `', js)

    def test_github_json_and_clipboard_share_server_sanitization(self):
        js = self.frontend
        self.assertIn('id="dra-logs-git"', js)
        self.assertIn('id="dra-logs-json"', js)
        self.assertIn('id="dra-logs-copy"', js)
        self.assertIn("deploy_relay_v2_dev/deployment/logs/download", js)
        self.assertIn("deploy_relay_v2_dev/deployment/logs/export", js)
        self.assertIn('parsed?.snapshot?.schema !== "dra-v2-dev-git-source-diagnostic.v1"', js)
        self.assertIn('this._centralExport.configured', js)
        self.assertIn('await navigator.clipboard.writeText(result.content)', js)
        self.assertNotIn("github.com/TheDaimos/Project-Log-And-Export", js)

    def test_admin_only_source_log_routes_without_mutations(self):
        ws = self.ws
        for route in ("logs", "logs/download", "logs/export"):
            self.assertEqual(ws.count(f'"deploy_relay_v2_dev/deployment/{route}"'), 1)
        for name in ("async_deployment_logs", "async_deployment_logs_download",
                     "async_deployment_logs_export"):
            definition = ws.index("async def " + name + "(")
            self.assertIn("@websocket_api.require_admin", ws[max(0, definition-210):definition])
        self.assertNotIn('deploy_relay_v2_dev/deployment/install', ws)
        self.assertNotIn('deploy_relay_v2_dev/deployment/restart', ws)


if __name__ == "__main__":
    unittest.main()
