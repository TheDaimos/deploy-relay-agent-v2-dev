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
        self.assertIn('const deploymentStage = this._mainBatchMode', js)
        self.assertIn('upToDate ? 1 : displayFinished ? 4', js)
        self.assertIn('"4/4 · Abschluss – erfolgreich installiert"', js)

    def test_progress_and_four_steps_reach_completion(self):
        js = self.js
        self.assertIn('displayFinished ? "completed"', js)
        self.assertIn('aria-valuenow="${this._mainBatchMode', js)
        self.assertIn('.dra-deploy-progress.completed .dra-deploy-progress-fill {width:100%', js)
        self.assertIn('deploymentIcons[deploymentStage-1]', js)
        self.assertIn('.dra-deploy-step.green.current', js)

    def test_historical_completion_is_read_only_and_project_bound(self):
        js = self.js
        self.assertIn('this._refreshInstallAudit();', js)
        self.assertIn('event.project_key === mainProject.project_id', js)
        self.assertIn('event.stage === "success" && event.status === "success"', js)
        self.assertIn('!mainPreviewVerified', js)
        self.assertIn('const displayFinished = !upToDate && (installFinished || archivedFinish);', js)
        self.assertIn('"4/4 · Letzter Abschluss (gespeichert)"', js)
        self.assertIn('Historischer Abschluss – keine aktuelle Quellprüfung, keine neue Freigabe.', js)
        self.assertIn('aria-valuenow="${this._mainBatchMode', js)
        self.assertIn('displayFinished ? "completed"', js)

    def test_verified_no_change_is_informational_and_never_a_write_approval(self):
        js = self.js
        self.assertIn('const previewNoChanges = mainPreviewVerified', js)
        self.assertIn('this._sourcePreview.add.length === 0', js)
        self.assertIn('this._sourcePreview.change.length === 0', js)
        self.assertIn('this._sourcePreview.remove.length === 0', js)
        self.assertIn('const upToDate = previewNoChanges', js)
        self.assertIn('"Aktuell · Kein Update verfügbar"', js)
        self.assertIn('id="dra-up-to-date-recheck"', js)
        self.assertIn('upToDate || deploymentBusy || !deploymentCanPreview', js)
        self.assertIn('this._sourcePreview.remove.length === 0) return;', js)
        self.assertIn('Vorherige Installation · Historie', js)
        self.assertIn('.dra-deploy-action.up-to-date', js)

    def test_step_three_during_submission(self):
        js = self.js
        self.assertIn('this._installSubmissionActive = true;', js)
        self.assertIn('this._installSubmissionActive = false;', js)
        self.assertIn('this._installSubmissionActive || installActive || installFailed', js)
        self.assertIn('"3/4 · Auftrag wird an Home Assistant übergeben …"', js)

    def test_failed_and_running_are_not_marked_successful(self):
        js = self.js
        self.assertIn('"3/4 · Update läuft …"', js)
        self.assertIn('"3/4 · Update fehlgeschlagen – Audit prüfen"', js)
        self.assertIn('installFailed ? "failed"', js)
        self.assertIn('.dra-deploy-progress.failed .dra-deploy-progress-fill {width:75%', js)


if __name__ == "__main__":
    unittest.main()
