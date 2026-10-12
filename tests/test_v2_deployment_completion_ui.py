"""Static completion contracts for the V2 single-button four-stage workflow."""
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "custom_components" /
       "deploy_relay_v2_dev" / "frontend" / "lab.js")


class CompletionUiContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = SRC.read_text(encoding="utf-8")

    def test_server_receipt_controls_completion_not_source_preview(self):
        js = self.js
        self.assertIn('this._installJob?.status === "success" && this._installJob?.phase === "complete"', js)
        self.assertIn('this._installJob?.project_key === mainProject.project_id', js)
        self.assertNotIn('mainPreviewVerified && this._installJob?.project_key', js)
        self.assertIn('const deploymentStage = installFinished ? 4', js)
        self.assertIn('"4/4 · Abschluss – erfolgreich installiert"', js)

    def test_progress_and_four_steps_reach_completion(self):
        js = self.js
        self.assertIn('installFinished ? "completed"', js)
        self.assertIn('aria-valuenow="${installFinished ? 4', js)
        self.assertIn('.dra-deploy-progress.completed .dra-deploy-progress-fill {width:100%', js)
        self.assertIn('deploymentIcons[deploymentStage-1]', js)
        self.assertIn('.dra-deploy-step.green.current', js)

    def test_failed_and_running_are_not_marked_successful(self):
        js = self.js
        self.assertIn('"3/4 · Update läuft …"', js)
        self.assertIn('"3/4 · Update fehlgeschlagen – Audit prüfen"', js)
        self.assertIn('installFailed ? "failed"', js)
        self.assertIn('.dra-deploy-progress.failed .dra-deploy-progress-fill {width:75%', js)


if __name__ == "__main__":
    unittest.main()
