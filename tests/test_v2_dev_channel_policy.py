"""Regression tests for explicit V2 DEV recommendation and V1 isolation.

DRA V1 resolves recommendations from the repository default branch.
This test verifies the policy payload before mirroring it there.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feature/v2-10-inventory-operation-contract"


class ExplicitDevChannelTests(unittest.TestCase):
    def test_channel_policy_points_at_safe_dev_branch(self):
        policy = json.loads((ROOT / "deploy-relay-channel.json").read_text(encoding="utf-8"))
        self.assertEqual(
            policy,
            {
                "schema": "deploy-relay.channel.v1",
                "project_id": "deploy_relay_agent_v2_dev",
                "recommended": {
                    "channel": "development",
                    "kind": "branch",
                    "ref": BRANCH,
                },
            },
        )

    def test_policy_matches_lab_deployment_not_v1(self):
        channel = json.loads((ROOT / "deploy-relay-channel.json").read_text(encoding="utf-8"))
        deployment = json.loads((ROOT / "deploy-relay.json").read_text(encoding="utf-8"))
        self.assertEqual(channel["project_id"], deployment["project"]["id"])
        self.assertEqual(len(deployment["deployment"]["groups"]), 1)
        self.assertEqual(
            deployment["deployment"]["groups"][0]["target"],
            "custom_components/deploy_relay_v2_dev",
        )
        self.assertNotEqual(
            deployment["deployment"]["groups"][0]["target"],
            "custom_components/deploy_relay",
        )

    def test_v1_recommendation_uses_default_branch_channel_policy(self):
        const = (ROOT / "custom_components/deploy_relay/const.py").read_text(
            encoding="utf-8"
        )
        resolver = (ROOT / "custom_components/deploy_relay/deployment_channel.py").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'DEFAULT_CHANNEL_POLICY_PATH: Final = "deploy-relay-channel.json"',
            const,
        )
        self.assertIn("ref=info.default_branch", resolver)
        self.assertIn("raw_policy", resolver)
        self.assertIn("ref=policy.ref", resolver)


if __name__ == "__main__":
    unittest.main()
