"""The only permitted GitHub write is the synthetic teststatus file."""
import importlib.util
from pathlib import Path
import unittest

src = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
spec = importlib.util.spec_from_file_location("v2_teststand",src/"test_version_bump.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FixedTestStand(unittest.TestCase):
    def test_safe_one_step_only(self):
        raw = b'{"schema":"dra-v2-safe-test.v1","teststand":2,"projekt":"Test-Repo-DRA-V2","installation":"synthetische Testdaten","erwarteter_zielordner":"/config/dra_v2_testprojekt","home_assistant_neustart_erforderlich":false,"vertrauliche_daten":false}'
        before, after, updated = module.next_test_status(raw)
        self.assertEqual((before,after),(2,3))
        self.assertEqual(module.json.loads(updated)["teststand"],3)
        self.assertEqual(set(module.json.loads(updated)),module.ALLOWED_KEYS)

    def test_reject_malicious_input(self):
        valid = {"schema":"dra-v2-safe-test.v1","teststand":2,
                 "projekt":"Test-Repo-DRA-V2","installation":"synthetische Testdaten",
                 "erwarteter_zielordner":"/config/dra_v2_testprojekt",
                 "home_assistant_neustart_erforderlich":False,"vertrauliche_daten":False}
        for key,value in [("teststand",True),("teststand",99999),
                          ("erwarteter_zielordner","/config/custom_components"),
                          ("vertrauliche_daten",True)]:
            item=dict(valid);item[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(module.TestVersionError):
                module.next_test_status(module.json.dumps(item).encode())
        item=dict(valid);item["token"]="secret"
        with self.assertRaises(module.TestVersionError):
            module.next_test_status(module.json.dumps(item).encode())

    def test_no_client_controlled_destination(self):
        js=(src/"frontend"/"lab.js").read_text(encoding="utf-8")
        ws=(src/"websocket_api.py").read_text(encoding="utf-8")
        self.assertIn('REPOSITORY = "TheDaimos/Test-Repo-DRA-V2"', (src/"test_version_bump.py").read_text())
        self.assertIn('FILE_PATH = "payload/teststatus.json"', (src/"test_version_bump.py").read_text())
        self.assertIn('probatio.Required("confirm"): bool', ws)
        self.assertIn('@websocket_api.require_admin',ws)
        self.assertIn('runtime.project_auth.token(TEST_REPO)',ws)
        self.assertIn('id="dra-test-version-confirm"',js)
        self.assertIn('id="dra-test-version-increment"',js)
        self.assertIn('id="dra-tests-expander" ${this._testsOpen ? "open" : ""}',js)
        self.assertIn('project-batch-settings-open project-settings-open-style project-metal-button',js)


if __name__ == "__main__":
    unittest.main()
