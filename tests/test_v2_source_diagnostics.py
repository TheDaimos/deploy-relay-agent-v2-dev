"""DRA V2 deployment diagnostics remain bounded, private and read-only."""
from __future__ import annotations

import copy
import importlib
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PACKAGE = "_v2_source_diagnostics_test"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = pkg
diagnostics = importlib.import_module(f"{PACKAGE}.source_diagnostics")
export = importlib.import_module(f"{PACKAGE}.git_measurement_export")


class MockSettings:
    def snapshot(self):
        return {"mode":"controlled", "max_readonly_jobs":4, "max_worker_processes":12}
    def core_status(self):
        return {"available_cores":8}
    def effective(self):
        return {"active_readonly_limit":1, "mutation_limit":0,
                "worker_budget_enforced":False}


def new_record(success=False):
    log = diagnostics.SourceDiagnosticLog()
    ctx = log.begin()
    log.stage(ctx, "repository")
    log.stage(ctx, "manifest")
    data = log.finish(ctx, success=success,
                      reason="none" if success else "manifest_invalid",
                      resources=diagnostics.resource_snapshot(MockSettings()))
    return data


class DiagnosticsContract(unittest.TestCase):
    def test_stage_timeline_and_cpu_not_false_parallel_claim(self):
        record = new_record()
        self.assertEqual([p["stage"] for p in record["steps"]],
                         ["admission", "repository", "manifest"])
        self.assertEqual(record["status"], "failed")
        self.assertFalse(record["sources_verified"])
        self.assertFalse(record["installation_enabled"])
        self.assertIsInstance(record["process_cpu_ms"], int)
        self.assertGreaterEqual(record["process_cpu_ms"], 0)
        self.assertEqual(record["resources"]["available_cores"], 8)
        self.assertEqual(record["resources"]["configured_worker_processes"], 12)
        self.assertEqual(record["resources"]["configured_readonly_jobs"], 4)
        self.assertEqual(record["resources"]["active_readonly_limit"], 1)
        self.assertEqual(record["resources"]["active_mutation_limit"], 0)
        self.assertFalse(record["resources"]["worker_budget_enforced"])
        self.assertTrue(all(0 <= t["elapsed_ms"] <= record["duration_ms"] for t in record["steps"]))

    def test_project_reference_is_opaque_and_stable_for_current_runtime(self):
        log = diagnostics.SourceDiagnosticLog()
        first = log.begin()
        ref = log.bind_project(first, "TheDaimos/gewitterradar")
        log.stage(first, "manifest")
        one = log.finish(first, success=False, reason="manifest_invalid",
                         resources=diagnostics.resource_snapshot(MockSettings()))
        second = log.begin()
        same_ref = log.bind_project(second, "thedaimos/GEWITTERRADAR")
        two = log.finish(second, success=False, reason="source_unavailable",
                         resources=diagnostics.resource_snapshot(MockSettings()))
        self.assertEqual(ref, same_ref)
        self.assertRegex(ref, r"^P-[0-9A-F]{12}$")
        self.assertEqual(one["project_ref"], two["project_ref"])
        self.assertNotIn("TheDaimos", str(log.entries()))
        self.assertNotIn("gewitterradar", str(log.entries()).casefold())
        self.assertEqual(log.private_repository_for(one["run_id"]), "TheDaimos/gewitterradar")
        self.assertEqual(log.private_repository_for(two["run_id"]), "thedaimos/GEWITTERRADAR")
        other = log.begin()
        other_ref = log.bind_project(other, "TheDaimos/weather-router-dev")
        self.assertNotEqual(other_ref, ref)
        with self.assertRaises(diagnostics.SourceDiagnosticsError):
            log.bind_project(other, "TheDaimos/gewitterradar")

    def test_clear_is_guarded_and_only_for_in_memory_logs(self):
        log = diagnostics.SourceDiagnosticLog()
        for repo in ("TheDaimos/gewitterradar", "TheDaimos/weather-router-dev"):
            ctx = log.begin()
            log.bind_project(ctx, repo)
            log.finish(ctx, success=False, reason="source_unavailable",
                       resources=diagnostics.resource_snapshot(MockSettings()))
        before = log.entries()
        with self.assertRaises(diagnostics.SourceDiagnosticsError):
            log.clear(expected_run_id=before[-1]["run_id"])
        self.assertEqual(len(log.entries()), 2)
        self.assertEqual(log.clear(expected_run_id=before[0]["run_id"]), 2)
        self.assertEqual(log.entries(), [])
        self.assertIsNone(log.private_repository_for(before[0]["run_id"]))
        self.assertIsNone(log.private_repository_for(before[1]["run_id"]))
        with self.assertRaises(diagnostics.SourceDiagnosticsError):
            log.clear(expected_run_id=before[0]["run_id"])

    def test_bounded_history_and_independent_snapshots(self):
        log = diagnostics.SourceDiagnosticLog()
        for _ in range(12):
            ctx = log.begin()
            log.stage(ctx, "tree")
            log.finish(ctx, success=False, reason="tree_invalid",
                       resources=diagnostics.resource_snapshot(MockSettings()))
        self.assertEqual(len(log.entries()), diagnostics.MAX_REPORTS)
        recent = log.latest()
        recent["steps"][0]["stage"] = "modified"
        self.assertNotEqual(log.latest()["steps"][0]["stage"], "modified")

    def test_rejects_secrets_unknown_fields_and_forged_success(self):
        record = new_record()
        attempts = [
            lambda x: x.update({"token":"github_pat_private"}),
            lambda x: x.update({"installation_enabled":True}),
            lambda x: x.update({"repository":"TheDaimos/private-repo"}),
            lambda x: x.update({"project_ref":"TheDaimos/private-repo"}),
            lambda x: x.update({"project_ref":"P-invalid"}),
            lambda x: x.update({"process_cpu_ms":-1}),
            lambda x: x.update({"process_cpu_ms":"shared:secret"}),
            lambda x: x.update({"status":"success"}),
            lambda x: x.update({"reason":"path /config/secrets.yaml"}),
            lambda x: x["resources"].update({"access_token":"bad"}),
            lambda x: x["resources"].update({"active_mutation_limit":1}),
            lambda x: x["resources"].update({"available_cores":4097}),
            lambda x: x["steps"].append({"stage":"files", "elapsed_ms":1}),
        ]
        for attempt in attempts:
            modified = copy.deepcopy(record)
            attempt(modified)
            with self.subTest(attempt=attempt), self.assertRaises(diagnostics.SourceDiagnosticsError):
                diagnostics.sanitize_source_diagnostic(modified)

    def test_classification_keeps_no_exception_messages(self):
        err = ValueError("token=github_pat_very_secret_path=/config/secrets.yaml")
        self.assertEqual(diagnostics.classify_source_failure("manifest", err), "manifest_invalid")
        self.assertEqual(diagnostics.classify_source_failure("local_inventory", err), "local_inventory_invalid")
        self.assertEqual(diagnostics.classify_source_failure("tree", TimeoutError()), "timeout")

    def test_manifest_error_categories_are_precise_and_never_disclose_raw_values(self):
        cases = {
            "github_http_authentication": "manifest_remote_authentication",
            "github_http_forbidden": "manifest_remote_forbidden",
            "github_http_not_found": "manifest_remote_not_found",
            "github_http_rate_limited": "manifest_remote_rate_limited",
            "GitHub request unsuccessful": "manifest_remote_http",
            "GitHub response could not be verified": "manifest_transport_invalid",
            "GitHub response exceeds size limit": "manifest_response_too_large",
            "invalid GitHub JSON": "manifest_json_invalid",
            "invalid manifest size": "manifest_size_invalid",
            "manifest is not an encoded file": "manifest_encoding_invalid",
            "manifest base64 invalid": "manifest_encoding_invalid",
            "invalid manifest encoding": "manifest_encoding_invalid",
            "manifest content integrity failed": "manifest_content_integrity",
            "unsupported manifest schema": "manifest_schema_invalid",
            "invalid project identity": "manifest_identity_invalid",
            "repository identity mismatch": "manifest_identity_invalid",
            "artifact source is not yet supported": "manifest_source_unsupported",
            "deployment root not approved": "manifest_policy_invalid",
            "symlinks not permitted": "manifest_policy_invalid",
            "invalid resource limit": "manifest_resource_limit",
            "invalid deployment groups": "manifest_groups_invalid",
            "overlapping deployment targets": "manifest_groups_invalid",
            "protected deployment target": "manifest_target_protected",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                code = diagnostics.classify_source_failure("manifest", ValueError(source))
                self.assertEqual(code, expected)
                self.assertIn(code, diagnostics.ALLOWED_REASONS)
        self.assertEqual(diagnostics.classify_source_failure(
            "manifest", ValueError("unknown private error detail")), "manifest_invalid")
        self.assertEqual(diagnostics.classify_source_failure(
            "manifest", TimeoutError()), "timeout")

    def test_precise_tree_reason_mapping_is_allowlisted_not_raw_error_text(self):
        examples = {
            "github_http_authentication": "tree_remote_authentication",
            "github_http_forbidden": "tree_remote_forbidden",
            "github_http_not_found": "tree_remote_not_found",
            "github_http_rate_limited": "tree_remote_rate_limited",
            "GitHub request unsuccessful": "tree_remote_http",
            "GitHub response could not be verified": "tree_transport_invalid",
            "GitHub response exceeds size limit": "tree_response_too_large",
            "invalid GitHub JSON": "tree_json_invalid",
            "GitHub tree is incomplete": "tree_incomplete",
            "repository tree incomplete or too large": "tree_entry_limit",
            "unsafe source path": "tree_path_invalid",
            "unsupported source entry (possibly symlink/submodule)": "tree_entry_invalid",
            "invalid source size": "tree_file_invalid",
            "source directory empty": "tree_source_empty",
            "source exceeds manifest budget": "tree_budget_exceeded",
        }
        for message, expected in examples.items():
            with self.subTest(message=message):
                classified = diagnostics.classify_source_failure("tree", ValueError(message))
                self.assertEqual(classified, expected)
                self.assertIn(classified, diagnostics.ALLOWED_REASONS)
        # Arbitrary HTTP bodies, local paths or secrets never become an export field.
        raw = "github_pat_super_secret /config/.storage private_project"
        classified = diagnostics.classify_source_failure("tree", ValueError(raw))
        self.assertEqual(classified, "tree_invalid")
        self.assertNotIn("github_pat_", classified)
        self.assertEqual(diagnostics.classify_source_failure("tree", TimeoutError()), "timeout")

    def test_export_uses_exact_existing_private_archive_envelope(self):
        record = new_record()
        result = export.archive_document(record, version="0.1.56",
                                         now=__import__("datetime").datetime.now(
                                             __import__("datetime").timezone.utc),
                                         export_id="a"*32)
        self.assertEqual(result["exportSchema"], "daimos-project-log-export-v1")
        self.assertEqual(result["test"]["id"], "V2-SOURCE-PREVIEW")
        self.assertEqual(result["snapshot"]["source_diagnostic"], record)
        self.assertNotIn("github_pat_", json.dumps(result))
        path = export.archive_path(result)
        self.assertTrue(path.startswith("exports/deploy-relay-agent-v2/"))
        rebuilt, test_id = export._validated_snapshot(result["snapshot"])
        self.assertEqual(rebuilt, result["snapshot"])
        self.assertEqual(test_id, "V2-SOURCE-PREVIEW")
        pending = {"path":path, "export_id":"a"*32,
                   "raw":json.dumps(result, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True)+"\n",
                   "repository":"TheDaimos/Project-Log-And-Export"}
        self.assertEqual(export._validate_pending(pending), pending)
        self.assertLess(len(pending["raw"].encode()), export.MAX_EXPORT_BYTES)

    def test_private_git_export_has_repository_but_local_json_does_not(self):
        log = diagnostics.SourceDiagnosticLog()
        ctx = log.begin()
        log.bind_project(ctx, "TheDaimos/gewitterradar")
        record = log.finish(ctx, success=False, reason="manifest_invalid",
                            resources=diagnostics.resource_snapshot(MockSettings()))
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        local = export.archive_document(record, version="0.1.59", now=now, export_id="b"*32)
        self.assertNotIn("private_source_repository", local["snapshot"])
        self.assertNotIn("TheDaimos/gewitterradar", json.dumps(local))
        private = export.archive_document(
            record, version="0.1.59", now=now, export_id="c"*32,
            private_source_repository=log.private_repository_for(record["run_id"]))
        self.assertEqual(private["snapshot"]["private_source_repository"], "TheDaimos/gewitterradar")
        self.assertEqual(private["snapshot"]["source_diagnostic"]["project_ref"], record["project_ref"])
        self.assertEqual(private["snapshot"]["source_diagnostic"]["run_id"], record["run_id"])
        rechecked, test_id = export._validated_snapshot(private["snapshot"])
        self.assertEqual(rechecked, private["snapshot"])
        self.assertEqual(test_id, "V2-SOURCE-PREVIEW")
        raw = json.dumps(private, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        pending = {
            "path": export.archive_path(private), "export_id": "c"*32,
            "raw": raw, "repository": "TheDaimos/Project-Log-And-Export",
        }
        self.assertEqual(export._validate_pending(pending), pending)
        wrong = {**pending, "repository":"TheDaimos/another-private-repo"}
        with self.assertRaises(export.GitMeasurementError):
            export._validate_pending(wrong)
        private["snapshot"]["private_source_repository"] = "https://external.test/example"
        with self.assertRaises(export.GitMeasurementError):
            export._validated_snapshot(private["snapshot"])
        # The server cannot attach a repository to an unbound record.
        with self.assertRaises(export.GitMeasurementError):
            export.archive_document(new_record(), version="0.1.59", now=now,
                                   export_id="d"*32,
                                   private_source_repository="TheDaimos/gewitterradar")

    def test_no_forged_backend_result_passes_archive_revalidation(self):
        record = new_record()
        result = export.archive_document(record, version="0.1.56",
                                         now=__import__("datetime").datetime.now(
                                             __import__("datetime").timezone.utc),
                                         export_id="a"*32)
        result["snapshot"]["source_diagnostic"]["resources"]["active_mutation_limit"] = 1
        with self.assertRaises(export.GitMeasurementError):
            export._validated_snapshot(result["snapshot"])


if __name__ == "__main__":
    unittest.main()
