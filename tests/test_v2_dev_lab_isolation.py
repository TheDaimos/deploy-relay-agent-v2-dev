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
        self.assertEqual(len(re.findall(r'probatio.Required\("type"\): "deploy_relay_v2_dev/projects/', sockets)), 9)
        self.assertEqual(sockets.count("@websocket_api.require_admin"), 27)
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
        self.assertIn('store["runtime"]', (LAB_ROOT / "__init__.py").read_text(encoding="utf-8"))

    def test_async_ws_handlers_are_scheduled_and_admin_guarded(self):
        sockets = (LAB_ROOT / "websocket_api.py").read_text(encoding="utf-8")
        self.assertEqual(sockets.count("@websocket_api.async_response"), 27)
        self.assertEqual(sockets.count("@websocket_api.require_admin"), 27)
        self.assertEqual(sockets.count("@websocket_api.websocket_command("), 27)
        self.assertIn("import probatio", sockets)
        self.assertNotIn("import voluptuous", sockets)
        for handler in ("async_state", "async_measure", "async_multicore",
                        "async_all", "async_get", "async_archive_repository_check",
                        "async_git_export", "async_git_retry", "async_download_json",
                        "async_projects_list", "async_projects_v1_preview",
                        "async_projects_import_v1", "async_projects_add",
                        "async_projects_retention", "async_projects_preselect",
                        "async_projects_source_preview", "async_git_read_configure",
                        "async_git_read_clear",
                        "async_settings_get", "async_settings_save",
                        "async_settings_ack_cpu_warning",
                        "async_batch_preview"):
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

    def test_responsive_diagnostics_are_grouped_without_duplicate_actions(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('class="dashboard-grid"', frontend)
        self.assertIn('class="inner-panel status-panel"', frontend)
        self.assertIn('class="section-card export-card"', frontend)
        self.assertIn('class="diagnostic-results section-card"', frontend)
        self.assertIn("@media (min-width:1100px)", frontend)
        self.assertIn("@media (max-width:600px)", frontend)
        self.assertEqual(frontend.count('id="refresh"'), 1)
        self.assertEqual(frontend.count('id="git-export"'), 1)
        self.assertEqual(frontend.count('id="json-download"'), 1)
        self.assertLess(frontend.index("02 · Diagnoseexport"), frontend.index("04 · Auftragsverarbeitung"))
        self.assertLess(frontend.index("03 · Messergebnisse"), frontend.index("05 · Sammelaktualisierung"))

    def test_source_check_has_visible_per_project_feedback_and_columns(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('this._sourceRepository = repository;', frontend)
        self.assertIn('class="project-management-table"', frontend)
        self.assertIn('Prüfung läuft …', frontend)
        self.assertIn('Nicht verfügbar', frontend)
        self.assertIn('<th>Projekt</th><th>Git-Status</th><th>Einstellungen</th><th>Reihenfolge</th>', frontend)
        self.assertNotIn('class="preselect-toggle"', frontend)
        self.assertIn('class="batch-choice"', frontend)
        self.assertIn('@media (max-width:760px)', frontend)

    def test_batch_selection_uses_save_cancel_dialog(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('id="batch-open"', frontend)
        self.assertIn('id="batch-dialog"', frontend)
        self.assertIn('id="batch-save"', frontend)
        self.assertIn('id="batch-cancel"', frontend)
        self.assertNotIn('id="batch-preview"', frontend)
        self.assertIn('this._batchDialogOpen = false', frontend)
        self.assertIn('projects/preselect', frontend)
        self.assertIn('batch_preselect === enabled', frontend)

    def test_backup_retention_dialog_is_separate_and_fail_closed(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('id="backup-dialog-open"', frontend)
        self.assertIn('id="backup-dialog"', frontend)
        self.assertIn('class="backup-entry"', frontend)
        self.assertIn('button disabled title="Erst nach Einführung echter V2-Sicherungen verfügbar"', frontend)
        self.assertIn('this._projectAction("retention"', frontend)
        self.assertIn('button.closest(".backup-entry")', frontend)
        self.assertIn('<th>Projekt</th><th>Git-Status</th><th>Einstellungen</th><th>Reihenfolge</th>', frontend)
        self.assertNotIn('<th>Sicherungen behalten</th>', frontend)

    def test_operation_settings_have_responsive_grid(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('class="settings-fields"', frontend)
        self.assertIn('grid-template-columns:repeat(3,minmax(0,1fr))', frontend)
        self.assertIn('@media (max-width:850px)', frontend)
        for field in ('settings-mode', 'settings-readonly', 'settings-workers'):
            self.assertEqual(frontend.count('id="' + field + '"'), 1)

    def test_all_buttons_have_visible_press_and_focus_states(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('button:not(:disabled):active', frontend)
        self.assertIn('button:not(:disabled):hover', frontend)
        self.assertIn('button:focus-visible', frontend)
        self.assertIn('prefers-reduced-motion:reduce', frontend)
        self.assertIn('id="settings-save"', frontend)
        self.assertNotIn('>Vorgaben speichern</button>', frontend)

    def test_diagnostics_sections_are_collapsible(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('this._expandedSections = new Set()', frontend)
        self.assertEqual(frontend.count('class="section-toggle"'), 5)
        self.assertEqual(frontend.count('class="section-body"'), 5)
        self.assertIn('class="section-body" ', frontend)
        self.assertIn('this._expandedSections.has(id)', frontend)
        self.assertIn('>Import aus DRA-V1</button>', frontend)
        self.assertIn('id="project-import-all"', frontend)
        self.assertIn('class="import-choice"', frontend)
        self.assertIn('this._submitProjectImport()', frontend)

    def test_project_management_is_a_modal_outside_diagnostics(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('this._projectDialogOpen = false;', frontend)
        self.assertIn('id="project-management-dialog" role="dialog" aria-modal="true"', frontend)
        self.assertIn('id="project-management-close"', frontend)
        self.assertIn('id="project-management-dismiss"', frontend)
        self.assertIn('id="project-management-title">Projektverwaltung', frontend)
        self.assertIn('this._openProjectDialog()', frontend)
        self.assertIn('id="project-add-open"', frontend)
        self.assertIn('id="backup-dialog-open"', frontend)
        self.assertNotIn('05 · Projektverwaltung', frontend)
        self.assertNotIn('<article class="section-card project-card">', frontend)
        self.assertIn('05 · Sammelaktualisierung', frontend)
        self.assertLess(frontend.index('id="dra-settings-view"'),
                        frontend.index('id="project-management-dialog"'))
        self.assertLess(frontend.index('this._projectDialogOpen ?'),
                        frontend.index('id="project-management-dialog"'))

    def test_v1_inspired_dashboard_preserves_separate_diagnostics(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('this._view = "main"', frontend)
        self.assertIn('id="dra-main-view"', frontend)
        self.assertIn('id="dra-settings-view"', frontend)
        self.assertIn('id="dra-toggle"', frontend)
        self.assertIn('id="dra-select"', frontend)
        self.assertIn('Geführter Ablauf', frontend)
        self.assertIn('3 · Schreibzugriff freigeben</button>', frontend)
        self.assertIn('Diagnose & Einstellungen', frontend)
        self.assertIn('@media(max-width:760px)', frontend)
        self.assertIn('id="dra-main-ref"', frontend)
        self.assertIn('this._mainSourceRef = ""', frontend)
        self.assertIn('this._sourceCheck({dataset:{repo:mainProject.repository}})', frontend)

    def test_mobile_header_and_project_settings_actions_stay_on_one_row(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('class="dialog-actions manage-dialog-actions', frontend)
        self.assertIn('grid-template-columns:minmax(0,1.5fr) repeat(2,minmax(0,1fr))', frontend)
        self.assertIn('.dra-actions #dra-refresh {grid-column:1;}', frontend)
        self.assertIn('.dra-actions #dra-toggle {grid-column:2;}', frontend)
        self.assertIn('.git-dialog .manage-dialog-actions button', frontend)
        self.assertIn('white-space:nowrap;', frontend)
        self.assertIn('@media (max-width:360px)', frontend)
        self.assertEqual(frontend.count('id="manage-remove-start"'), 1)
        self.assertEqual(frontend.count('id="manage-cancel"'), 1)
        self.assertEqual(frontend.count('id="manage-save"'), 1)

    def test_mobile_project_cards_are_compact_and_controls_share_a_row(self):
        frontend = (LAB_ROOT / "frontend/lab.js").read_text(encoding="utf-8")
        self.assertIn('grid-template-areas:"number project project project" "status status settings order"', frontend)
        self.assertIn('grid-area:status;', frontend)
        self.assertIn('grid-area:settings;', frontend)
        self.assertIn('grid-area:order;', frontend)
        self.assertIn('.project-card td::before { content:none !important;', frontend)
        self.assertIn('.project-card td:nth-child(5) {', frontend)
        self.assertIn('.project-management-table .source-check.note', frontend)
        self.assertNotIn('content:"Git-Status"; display:block', frontend)

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
        self.assertNotIn("READONLY_TEST_STEPS", const)
        self.assertNotIn("deploy_relay_v2_dev/test/start", sockets)
        self.assertNotIn("async def async_start(", sockets)
        self.assertNotIn('id="start"', frontend)
        self.assertNotIn('querySelector("#start")', frontend)
        self.assertIn("CPU-/RAM-Messung", frontend)
        self.assertIn("Messlauf starten (40 s)", frontend)
        self.assertIn("Alle Tests nacheinander starten", frontend)
        self.assertIn("Mehrkern-Diagnose (1 / 2 / 4 / 6 / 8 / 10 / 12)", frontend)
        self.assertIn("No project or file access", (LAB_ROOT / "readonly_benchmark.py").read_text(encoding="utf-8"))
        self.assertNotIn("20-Sekunden-Test", frontend)
        self.assertNotIn("for index in range(1, 21):", sockets)
        self.assertEqual(sockets.count("@websocket_api.require_admin"), 27)


if __name__ == "__main__":
    unittest.main()
