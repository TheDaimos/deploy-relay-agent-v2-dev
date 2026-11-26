"""Isolation guards for adjustable HA-owned synthetic installation pacing."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "deploy_relay_v2_dev"


class TestFixturePacingContracts(unittest.TestCase):
    def test_fixed_test_repository_and_bounded_count(self):
        from_text = (COMP / "test_version_bump.py").read_text(encoding="utf-8")
        self.assertIn('REPOSITORY = "TheDaimos/Test-Repo-DRA-V2"', from_text)
        self.assertIn('not 1 <= file_count <= 7', from_text)
        self.assertIn('"base_tree": base_tree, "tree": tree', from_text)
        self.assertIn('"force": False', from_text)
        self.assertIn('payload/dra_test_{index:02d}.json', from_text)
        self.assertNotIn("force\": True", from_text)
        ast.parse(from_text)

    def test_delay_cannot_escape_isolated_project(self):
        coord = (COMP / "deployment_coordinator.py").read_text(encoding="utf-8")
        jobs = (COMP / "server_deployment_jobs.py").read_text(encoding="utf-8")
        ws = (COMP / "websocket_api.py").read_text(encoding="utf-8")
        ui = (COMP / "frontend" / "lab.js").read_text(encoding="utf-8")
        for source in (coord, jobs):
            self.assertIn('"TheDaimos/Test-Repo-DRA-V2"', source)
            self.assertIn('"test_repo_dra_v2"', source)
            self.assertIn("(0, 10, 20, 30, 60)", source)
            ast.parse(source)
        self.assertIn('await asyncio.sleep(test_delay_seconds)', jobs)
        self.assertIn('test_delay_seconds=candidate.test_delay_seconds', coord)
        self.assertIn('probatio.Optional("test_delay_seconds", default=0): int', ws)
        self.assertIn('test_delay_seconds=msg["test_delay_seconds"]', ws)
        self.assertIn('project.repository==="TheDaimos/Test-Repo-DRA-V2" ? this._testDelaySeconds : 0', ui)

    def test_no_browser_driven_file_paths_or_unbounded_wait(self):
        source = (COMP / "test_version_bump.py").read_text(encoding="utf-8")
        self.assertIn('for index in range(1, 7):', source)
        self.assertIn('"path": FILE_PATH', source)
        self.assertIn('api + "/git/refs/heads/main"', source)
        self.assertIn('allow_redirects=False', source)


if __name__ == "__main__":
    unittest.main()
