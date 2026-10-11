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
