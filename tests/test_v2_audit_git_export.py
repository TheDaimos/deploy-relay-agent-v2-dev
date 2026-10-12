"""Audit export reuses private central archive and rejects untrusted payloads."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"


class AuditGitExportContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exporter = (ROOT / "git_measurement_export.py").read_text(encoding="utf-8")
        cls.ws = (ROOT / "websocket_api.py").read_text(encoding="utf-8")
        cls.ui = (ROOT / "frontend" / "lab.js").read_text(encoding="utf-8")

    def test_audit_has_allowlisted_schema_and_private_queue(self):
        source = self.exporter
        self.assertIn('AUDIT_SCHEMA = "dra-v2-deployment-audit.v1"', source)
        self.assertIn('def sanitized_audit(value: object)', source)
        self.assertIn('set(row) != {"sequence","captured_at"', source)
        self.assertIn('len(value["records"]) <= 256', source)
        self.assertIn('test_id = "V2-DEPLOYMENT-AUDIT"', source)
        self.assertIn('{"schema", "created_at", "component", "version", "mode", "audit", "note"}', source)
        self.assertIn('rebuilt, expected_test = _validated_snapshot(snap)', source)
        self.assertIn('await self._persist(self._repository, data)', source)

    def test_route_is_admin_only_private_and_server_owned(self):
        source = self.ws
        start = source.index('async def async_deployment_audit_export(')
        preceding = source[max(0,start-250):start]
        body = source[start:source.index('@websocket_api.websocket_command(',start)]
        self.assertIn('@websocket_api.require_admin', preceding)
        self.assertIn('TheDaimos/Project-Log-And-Export', body)
        self.assertIn('runtime.deployment_audit.entries()', body)
        self.assertIn('runtime.git_export.retry_pending()', body)
        self.assertIn('runtime.git_export.export(', body)
        self.assertNotIn('msg["token"]', body)

    def test_inline_button_is_independent_from_local_json(self):
        self.assertIn('id="dra-audit-git"', self.ui)
        self.assertIn('deploy_relay_v2_dev/deployment/audit/export', self.ui)
        self.assertIn('id="dra-audit-json"', self.ui)
        self.assertIn('this._centralExport.configured !== true', self.ui)


if __name__ == "__main__":
    unittest.main()
