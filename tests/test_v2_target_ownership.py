"""Negative and positive checks of the read-only V2 target-ownership gate."""
from __future__ import annotations

import copy
import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PACKAGE = "_v2_target_ownership_test"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = pkg
m = importlib.import_module(f"{PACKAGE}.target_ownership")

SHA = "a" * 40


def preview(project="alpha", target=None, repo=None):
    root = target or "custom_components/" + project
    return {
        "schema": "dra-v2-dev-source-preview.v1",
        "project_id": project,
        "repository": repo or "Example/" + project,
        "source_commit": SHA,
        "groups": [{"source": "custom_components/" + project, "target": root}],
        "sources_verified": True,
        "local_inventory_readonly": True,
        "installation_enabled": False,
        "handover_required": True,
        "backup_verified": False,
    }


class TargetClaimsTests(unittest.TestCase):
    def test_unique_targets_still_never_authorize_install(self):
        examples = [preview("alpha"), preview("beta")]
        original = copy.deepcopy(examples)
        result = m.assess_target_claims(examples)
        self.assertEqual(result["project_count"], 2)
        self.assertEqual(result["target_count"], 2)
        self.assertEqual(result["conflicting_targets"], [])
        self.assertFalse(result["exclusive_ownership_verified"])
        self.assertFalse(result["cross_process_lock_verified"])
        self.assertFalse(result["backup_verified"])
        self.assertFalse(result["installation_enabled"])
        self.assertFalse(result["parallel_installation_enabled"])
        self.assertTrue(result["other_owners_must_be_checked"])
        self.assertEqual(examples, original)

    def test_same_root_in_two_projects_is_a_collision(self):
        result = m.assess_target_claims([
            preview("alpha", "custom_components/shared"),
            preview("beta", "custom_components/shared"),
        ])
        self.assertEqual(result["conflict_count"], 1)
        self.assertEqual(result["conflicting_targets"], ["custom_components/shared"])
        self.assertFalse(result["installation_enabled"])

    def test_case_variants_are_not_independent_targets(self):
        result = m.assess_target_claims([
            preview("alpha", "custom_components/Shared"),
            preview("beta", "custom_components/shared"),
        ])
        self.assertEqual(result["conflict_count"], 1)

    def test_external_claim_blocks_even_single_source(self):
        result = m.assess_target_claims(
            [preview("alpha")],
            externally_occupied_targets=["custom_components/ALPHA"],
        )
        self.assertEqual(result["conflicting_targets"], ["custom_components/alpha"])
        self.assertFalse(result["installation_enabled"])

    def test_external_occupancy_is_not_inferred_from_empty_list(self):
        result = m.assess_target_claims(
            [preview("alpha")], externally_occupied_targets=[],
        )
        self.assertEqual(result["conflict_count"], 0)
        self.assertFalse(result["exclusive_ownership_verified"])
        self.assertTrue(result["handover_required"])

    def test_duplicate_external_claim_and_unsafe_external_path_fail(self):
        for other in (
            ["custom_components/foo", "custom_components/FOO"],
            ["custom_components/deploy_relay"],
            ["secrets.yaml"],
            ["custom_components/../secret"],
            "custom_components/foo",
        ):
            with self.subTest(other=other), self.assertRaises(m.TargetClaimError):
                m.assess_target_claims(
                    [preview("alpha")], externally_occupied_targets=other,
                )

    def test_invalid_or_unsafe_source_snapshots_fail_closed(self):
        changes = [
            ("source_commit", "main"),
            ("sources_verified", False),
            ("local_inventory_readonly", False),
            ("installation_enabled", True),
            ("backup_verified", True),
            ("handover_required", False),
            ("groups", []),
            ("groups", [{"source": "safe", "target": ".storage"}]),
            ("groups", [{"source": "../unsafe", "target": "custom_components/foo"}]),
            ("schema", "other"),
            ("project_id", "other/project"),
        ]
        for key, value in changes:
            candidate = preview()
            candidate[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(m.TargetClaimError):
                m.assess_target_claims([candidate])

    def test_same_project_or_repo_twice_fails(self):
        for collection in (
            [preview("alpha"), preview("alpha", repo="Example/alternate")],
            [preview("alpha"), preview("beta", repo="example/ALPHA")],
        ):
            with self.assertRaises(m.TargetClaimError):
                m.assess_target_claims(collection)

    def test_duplicate_local_roots_differing_by_case_fail(self):
        candidate = preview()
        candidate["groups"].append({
            "source": "other", "target": "custom_components/ALPHA",
        })
        with self.assertRaises(m.TargetClaimError):
            m.assess_target_claims([candidate])

    def test_empty_or_oversized_batch_rejected(self):
        for collection in ([], [preview("alpha")] * 33, None):
            with self.assertRaises(m.TargetClaimError):
                m.assess_target_claims(collection)

    def test_unknown_extra_group_keys_rejected(self):
        candidate = preview()
        candidate["groups"][0]["write_permitted"] = True
        with self.assertRaises(m.TargetClaimError):
            m.assess_target_claims([candidate])


if __name__ == "__main__":
    unittest.main()
