"""Regression: no obsolete read-only warning in active deployment UI."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "custom_components" / "deploy_relay_v2_dev"


class OperatingModeBannerContract(unittest.TestCase):
    def test_no_false_read_only_banner(self):
        panel = (LAB / "frontend" / "lab.js").read_text(encoding="utf-8")
        self.assertNotIn("Gesperrter Betrieb", panel)
        self.assertNotIn("Deployment-Schreibzugriffe sind deaktiviert", panel)
        self.assertNotIn("Nur schreibgeschützter Testbetrieb", panel)

    def test_explicit_install_confirmation_and_backend_authority_remain(self):
        panel = (LAB / "frontend" / "lab.js").read_text(encoding="utf-8")
        api = (LAB / "websocket_api.py").read_text(encoding="utf-8")
        self.assertIn("Ja, Update installieren", panel)
        self.assertIn("Installation nur nach", "Installation nur nach ausdrücklicher Freigabe")
        self.assertIn("Installationen nur nach ausdrücklicher Freigabe", panel)
        self.assertIn('probatio.Required("confirm"): bool', api)
        self.assertIn('await runtime.deployment.require_controller(project["project_id"], msg["client_id"])', api)


if __name__ == "__main__":
    unittest.main()
