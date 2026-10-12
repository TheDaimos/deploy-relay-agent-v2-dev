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
        self.assertIn('this._centralExport.repository !== "TheDaimos/Project-Log-And-Export"', js)
        self.assertIn('await navigator.clipboard.writeText(result.content)', js)
        self.assertNotIn("github.com/TheDaimos/Project-Log-And-Export", js)

    def test_failed_export_is_retried_without_replacing_queued_file(self):
        ws = self.ws
        js = self.frontend
        marker = ws.index('async def async_deployment_logs_export')
        handler = ws[marker:ws.index('@websocket_api.websocket_command', marker)]
        self.assertIn('and runtime.git_export.pending:', handler)
        self.assertIn('await runtime.git_export.retry_pending()', handler)
        self.assertIn('"pending_retried": True', handler)
        self.assertIn('"pending_retried": False', handler)
        self.assertLess(handler.index('and runtime.git_export.pending:'),
                        handler.index('record = runtime.source_diagnostics.latest()'))
        self.assertLess(handler.index('and runtime.git_export.pending:'),
                        handler.index('runtime.git_export.export('))
        self.assertIn('typeof result.pending_retried !== "boolean"', js)
        self.assertIn('Gespeicherten Git-Export erneut senden', js)
        self.assertIn('Für das aktuelle Prüfprotokoll Export nach Git erneut wählen.', js)
        self.assertIn('Ein vorbereiteter Bericht bleibt lokal erhalten.', js)

    def test_g2_retry_prepare_requires_explicit_admin_confirmation_and_private_target(self):
        js, ws = self.frontend, self.ws
        start = ws.index("async def async_deployment_logs_export")
        end = ws.index("@websocket_api.websocket_command", start)
        handler = ws[start:end]
        self.assertIn('probatio.Optional("g2_prepare", default=False): bool', ws)
        self.assertIn('probatio.Optional("g2_confirm", default=False): bool', ws)
        self.assertIn('if not msg["g2_confirm"] or runtime.git_export.pending:', handler)
        self.assertIn('runtime.git_export.prepare_retry_test(', handler)
        self.assertIn('runtime.git_export.repository != "TheDaimos/Project-Log-And-Export"', handler)
        self.assertLess(handler.index('and runtime.git_export.pending:'),
                        handler.index('if msg["g2_prepare"]:'))
        self.assertIn('if record is None:', handler)
        self.assertLess(handler.index('and runtime.git_export.pending:'),
                        handler.index('if record is None:'))
        self.assertIn('"g2_prepare"', js)
        self.assertIn('id="dra-g2-retry-yes"', js)
        self.assertIn('id="dra-g2-retry-no"', js)
        self.assertIn('g2_prepare:true,g2_confirm:true', js)
        self.assertIn('G2-Test vorbereiten', js)
        self.assertIn('nur lokal gesichert', js)

    def test_conditional_clear_has_confirmation_and_ids_for_screenshots(self):
        js = self.frontend
        self.assertIn('this._deploymentLogCount > 0 ? ', js)
        self.assertIn('id="dra-deployment-logs-clear"', js)
        self.assertIn('data.deployment_log_count', js)
        self.assertIn('result.count !== result.records.length', js)
        self.assertIn('id="dra-logs-clear-confirm"', js)
        self.assertIn('id="dra-logs-clear-cancel"', js)
        self.assertIn('Nur die letzten temporären V2-Protokolle leeren?', js)
        self.assertIn('expected_run_id:expected', js)
        self.assertIn('record.project_ref || "—"', js)
        self.assertIn('record.run_id || "").slice(0,12)', js)
        self.assertIn('Temporäre Logs geleert. Private Git-Exporte bleiben erhalten.', js)

    def test_admin_only_source_log_routes_without_mutations(self):
        ws = self.ws
        for route in ("logs", "logs/download", "logs/export", "logs/clear"):
            self.assertEqual(ws.count(f'"deploy_relay_v2_dev/deployment/{route}"'), 1)
        for name in ("async_deployment_logs", "async_deployment_logs_download",
                     "async_deployment_logs_export", "async_deployment_logs_clear"):
            definition = ws.index("async def " + name + "(")
            self.assertIn("@websocket_api.require_admin", ws[max(0, definition-210):definition])
        self.assertIn('runtime.git_export.repository != "TheDaimos/Project-Log-And-Export"', ws)
        self.assertIn('runtime.source_diagnostics.bind_project(trace, repo)', ws)
        self.assertIn('private_source_repository=source_repository', ws)
        self.assertIn('msg["confirm"] is not True', ws)
        self.assertIn('runtime.source_diagnostics.clear(expected_run_id=msg["expected_run_id"])', ws)
        self.assertNotIn('deploy_relay_v2_dev/deployment/install', ws)
        self.assertNotIn('deploy_relay_v2_dev/deployment/restart', ws)


if __name__ == "__main__":
    unittest.main()
