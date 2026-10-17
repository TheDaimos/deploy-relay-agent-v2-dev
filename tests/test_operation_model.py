"""V2-20 isolated state-contract tests (no Home Assistant needed)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay"))
from operation_model import (  # noqa: E402
    OperationContractError, OperationPhase, OperationRecord,
    OperationStatus, OperationType, ErrorFamily, TERMINAL,
)


class ModelContractTests(unittest.TestCase):
    def make(self, **kwargs):
        options = {"operation_type": OperationType.PREVIEW, "project_key": "project_1"}
        options.update(kwargs)
        return OperationRecord(**options)

    def test_queued_by_default_and_unique(self):
        a, b = self.make(), self.make()
        self.assertEqual(a.status, OperationStatus.QUEUED)
        self.assertNotEqual(a.operation_id, b.operation_id)
        self.assertIsNone(a.progress_percent)

    def test_reject_project_identifiers_containing_paths(self):
        for item in ("../secrets.yaml", "p/a", "", "a" * 129, "with space", "\n"):
            with self.subTest(item=item), self.assertRaises(OperationContractError):
                self.make(project_key=item)

    def test_source_commit_is_exact_hash(self):
        r = self.make(source_commit="a" * 40)
        self.assertEqual(r.source_commit, "a" * 40)
        self.assertEqual(self.make(source_commit="b" * 64).source_commit, "b" * 64)
        for item in ("main", "a" * 39, "A" * 40, "a" * 41, "../../src"):
            with self.subTest(item=item), self.assertRaises(OperationContractError):
                self.make(source_commit=item)

    def test_wait_then_run_then_success(self):
        r = self.make()
        r.transition(OperationStatus.WAITING_FOR_RESOURCE)
        self.assertEqual(r.phase, OperationPhase.WAITING)
        r.transition(OperationStatus.RUNNING)
        r.update_progress(phase=OperationPhase.INVENTORY, current=4, total=8, overall=True)
        self.assertEqual(r.progress_percent, 50)
        r.transition(OperationStatus.SUCCESS)
        self.assertTrue(r.terminal)
        self.assertEqual(r.progress_percent, 100)
        self.assertEqual(r.phase, OperationPhase.COMPLETE)
        self.assertIsNotNone(r.started_at)
        self.assertIsNotNone(r.finished_at)

    def test_terminal_states_cannot_move(self):
        for terminal in (OperationStatus.SUCCESS, OperationStatus.FAILED, OperationStatus.INTERRUPTED):
            r = self.make()
            r.transition(OperationStatus.RUNNING)
            r.transition(terminal)
            with self.subTest(terminal=terminal), self.assertRaises(OperationContractError):
                r.transition(OperationStatus.RUNNING)

    def test_impossible_transition_rejected_without_mutation(self):
        r = self.make()
        with self.assertRaises(OperationContractError):
            r.transition(OperationStatus.SUCCESS)
        self.assertEqual(r.status, OperationStatus.QUEUED)

    def test_invalid_error_family_does_not_set_failed(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        with self.assertRaises(ValueError):
            r.transition(OperationStatus.FAILED, error_family="my token x")
        self.assertEqual(r.status, OperationStatus.RUNNING)

    def test_only_failed_can_have_error_family(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        with self.assertRaises(OperationContractError):
            r.transition(OperationStatus.SUCCESS, error_family=ErrorFamily.SOURCE)
        self.assertEqual(r.status, OperationStatus.RUNNING)

    def test_failure_preserves_last_percent_below_100(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.update_progress(phase=OperationPhase.STAGING, current=10, total=10, overall=True)
        self.assertEqual(r.progress_percent, 99)
        self.assertFalse(r.progress_exact)
        r.transition(OperationStatus.FAILED, error_family=ErrorFamily.VERIFICATION)
        self.assertNotEqual(r.progress_percent, 100)
        self.assertEqual(r.error_family, ErrorFamily.VERIFICATION)

    def test_recovery_required_is_distinct(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.transition(OperationStatus.RECOVERY_REQUIRED, error_family=ErrorFamily.ROLLBACK)
        self.assertTrue(r.snapshot()["recovery_required"])
        self.assertEqual(r.phase, OperationPhase.RECOVERY)

    def test_same_phase_progress_monotonic(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.update_progress(phase=OperationPhase.INVENTORY, current=4, total=8, overall=True)
        with self.assertRaises(OperationContractError):
            r.update_progress(phase=OperationPhase.INVENTORY, current=3, total=8)
        with self.assertRaises(OperationContractError):
            r.update_progress(phase=OperationPhase.INVENTORY, current=5, total=10)
        self.assertEqual(r.progress_percent, 50)

    def test_new_phase_may_restart_counter_without_decreasing_percentage(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.update_progress(phase=OperationPhase.INVENTORY, current=8, total=10, overall=True)
        r.update_progress(phase=OperationPhase.VERIFY, current=1, total=10)
        self.assertEqual(r.progress_percent, 80)
        self.assertFalse(r.progress_exact)
        self.assertEqual(r.phase_percent, 10)

    def test_phase_completion_does_not_fake_overall_completion(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.update_progress(phase=OperationPhase.BACKUP, current=30, total=30)
        self.assertEqual(r.phase_percent, 100)
        self.assertIsNone(r.progress_percent)
        r.transition(OperationStatus.SUCCESS)
        self.assertEqual(r.progress_percent, 100)

    def test_no_post_action_mutation_after_terminal(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.transition(OperationStatus.SUCCESS)
        with self.assertRaises(OperationContractError):
            r.mark_post_action(restart_required=True, frontend_reload_possible=False)

    def test_progress_rejects_invalid_counts(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        for current, total in ((-1, 10), (11, 10), (2, 0), (True, 10), (2, 1.5)):
            with self.subTest(c=current, t=total), self.assertRaises(OperationContractError):
                r.update_progress(phase=OperationPhase.INVENTORY, current=current, total=total)

    def test_cancel_request_may_finish_safely(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.transition(OperationStatus.CANCEL_REQUESTED)
        r.transition(OperationStatus.SUCCESS)
        self.assertEqual(r.progress_percent, 100)

    def test_cancelled_before_start(self):
        r = self.make()
        r.transition(OperationStatus.CANCELLED)
        self.assertTrue(r.terminal)
        self.assertIsNone(r.started_at)

    def test_post_action_valid_only_on_active_or_success(self):
        r = self.make()
        with self.assertRaises(OperationContractError):
            r.mark_post_action(restart_required=True, frontend_reload_possible=False)
        r.transition(OperationStatus.RUNNING)
        r.mark_post_action(restart_required=True, frontend_reload_possible=True)
        self.assertTrue(r.snapshot()["restart_required"])
        self.assertFalse(r.snapshot()["frontend_reload_possible"])

    def test_item_counts_monotonic(self):
        r = self.make()
        r.transition(OperationStatus.RUNNING)
        r.update_item_counts(completed=3, failed=1)
        with self.assertRaises(OperationContractError):
            r.update_item_counts(completed=2, failed=2)
        self.assertEqual(r.completed_items, 3)

    def test_json_snapshot_contains_only_allowlisted_fields(self):
        r = self.make(source_commit="c" * 40, run_id="run-1")
        raw = json.dumps(r.snapshot(), sort_keys=True)
        self.assertEqual(json.loads(raw)["source_commit"], "c" * 40)
        self.assertNotIn("token", raw)
        self.assertNotIn("repository", raw)
        self.assertNotIn("path", raw)
        self.assertNotIn("message", raw)
        self.assertEqual(set(r.snapshot()).intersection({"headers", "credentials", "detail"}), set())

    def test_all_terminal_states_defined_as_immutable(self):
        self.assertEqual(len(TERMINAL), 5)


if __name__ == "__main__":
    unittest.main()
