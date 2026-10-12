"""Real audit data, bounded retention and no secret/file-path exposure."""
import importlib.util
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
spec = importlib.util.spec_from_file_location("_dra_v2_audit_unit", SRC / "deployment_audit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DeploymentAuditContracts(unittest.TestCase):
    def test_real_phase_sequence_and_utc(self):
        audit = module.DeploymentAudit()
        for phase in ("queued", "running", "staging", "backup", "install",
                      "verify_install", "success"):
            audit.record(operation_id="dra-123", project_key="test_repo_dra_v2",
                         stage=phase, status="success" if phase == "success" else "running")
        rows = audit.entries()
        self.assertEqual([r["stage"] for r in reversed(rows)],
                         ["queued", "running", "staging", "backup",
                          "install", "verify_install", "success"])
        self.assertTrue(all(r["captured_at"].endswith("Z") for r in rows))
        self.assertTrue(all(set(r) == {"sequence", "captured_at",
                                     "operation_id", "project_key", "stage", "status"}
                            for r in rows))

    def test_reject_unknown_stages_and_private_values(self):
        audit = module.DeploymentAudit()
        audit.record(operation_id="dra-123", project_key="test_repo_dra_v2",
                     stage="secrets.yaml")
        audit.record(operation_id="../../escape", project_key="test_repo_dra_v2",
                     stage="backup")
        self.assertEqual(audit.entries(), [])

    def test_bound_is_256_and_isolation(self):
        a, b = module.DeploymentAudit(), module.DeploymentAudit()
        for i in range(300):
            a.record(operation_id=f"dra-{i}", project_key="test_repo_dra_v2",
                     stage="backup")
        self.assertEqual(len(a.entries()), 256)
        self.assertEqual(b.entries(), [])
        self.assertEqual(a.entries()[0]["operation_id"], "dra-299")

    def test_connected_to_actual_v1_phases(self):
        jobs = (SRC / "server_deployment_jobs.py").read_text(encoding="utf-8")
        ws = (SRC / "websocket_api.py").read_text(encoding="utf-8")
        frontend = (SRC / "frontend" / "lab.js").read_text(encoding="utf-8")
        self.assertIn("self._audit.record(", jobs)
        self.assertIn("stage=stage", jobs)
        self.assertIn("async_execute_deployment(", jobs)
        self.assertIn('"deploy_relay_v2_dev/deployment/audit"', ws)
        self.assertIn("@websocket_api.require_admin", ws)
        self.assertIn("dra-v2-deployment-audit.v1", frontend)
        self.assertIn("installedAuditRows", frontend)



class AuditPersistenceContracts(unittest.IsolatedAsyncioTestCase):
    async def test_terminal_roundtrip_and_corrupt_fail_closed(self):
        class MemoryStore:
            def __init__(self):
                self.document = None
            async def async_load(self):
                return self.document
            async def async_save(self, value):
                import copy
                self.document = copy.deepcopy(value)

        store = MemoryStore()
        audit = module.DeploymentAudit(store)
        await audit.load()
        audit.record(operation_id="dra-123", project_key="test_repo_dra_v2",
                     stage="backup")
        audit.record(operation_id="dra-123", project_key="test_repo_dra_v2",
                     stage="success", status="success")
        await audit.save()
        restored = module.DeploymentAudit(store)
        await restored.load()
        self.assertEqual(restored.entries(), audit.entries())
        self.assertEqual(store.document["schema"], "dra-v2-deployment-audit.v1")

        store.document["records"][0]["project_key"] = "../../secrets.yaml"
        with self.assertRaises(ValueError):
            await module.DeploymentAudit(store).load()

    async def test_two_terminal_saves_preserve_order(self):
        class MemoryStore:
            async def async_load(self):
                return None
            async def async_save(self, value):
                import copy
                self.data = copy.deepcopy(value)
        store = MemoryStore()
        audit = module.DeploymentAudit(store)
        audit.record(operation_id="dra-1", project_key="test_repo_dra_v2",
                     stage="success", status="success")
        await audit.save()
        audit.record(operation_id="dra-2", project_key="test_repo_dra_v2",
                     stage="failed", status="failed")
        await audit.save()
        self.assertEqual(len(store.data["records"]), 2)

if __name__ == "__main__":
    unittest.main()
