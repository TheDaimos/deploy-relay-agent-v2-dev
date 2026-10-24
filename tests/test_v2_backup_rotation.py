"""Conservative V2 backup rotation only for verified owned snapshots."""
from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_backup_policy_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
m = importlib.import_module(f"{PKG}.backup_policy")


def make(n, *, project="one", complete=True, verified=True, recovery=False):
    return {
        "backup_id": f"b_{n:03}", "project_id": project,
        "created_at": f"2026-10-{n + 1:02}T12:00:00Z",
        "complete": complete, "verified": verified,
        "active_recovery": recovery,
    }


class RetentionPolicyTests(unittest.TestCase):
    def test_rotation_preserves_three_verified_restore_points(self):
        points = [make(n) for n in range(8)]
        self.assertEqual(m.rotation_plan("one", points, keep=3),
                         tuple(f"b_{n:03}" for n in range(5)))

    def test_protection_always_wins_and_incomplete_is_untouched(self):
        points = [make(n) for n in range(7)]
        points[1]["complete"] = False
        points[2]["verified"] = False
        points[3]["active_recovery"] = True
        result = m.rotation_plan("one", points, keep=3, protected=frozenset({"b_000"}))
        self.assertNotIn("b_000", result)
        self.assertNotIn("b_001", result)
        self.assertNotIn("b_002", result)
        self.assertNotIn("b_003", result)

    def test_invalid_cross_project_or_duplicate_never_plans(self):
        for points in ([make(0), make(0)], [make(0), make(1, project="two")]):
            with self.assertRaises(m.BackupPolicyError):
                m.rotation_plan("one", points, keep=3)

    def test_retention_limits_and_bool(self):
        for keep in (0, 2, 101, True, "10"):
            with self.assertRaises(m.BackupPolicyError):
                m.rotation_plan("one", [], keep=keep)

    def test_empty_never_deletes(self):
        self.assertEqual(m.rotation_plan("one", [], keep=10), ())

    def test_failure_on_unverified_structure(self):
        points = [make(0)]
        points[0]["unknown_path"] = "/config"
        with self.assertRaises(m.BackupPolicyError):
            m.rotation_plan("one", points, keep=3)

    def test_out_of_order_is_sorted_by_utc(self):
        points = [make(n) for n in (7, 2, 4, 1, 6, 3, 5, 0)]
        result = m.rotation_plan("one", points, keep=4)
        self.assertEqual(result, ("b_000", "b_001", "b_002", "b_003"))


if __name__ == "__main__":
    unittest.main()
