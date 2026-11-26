"""Regression: V2 deployment approval must not get stuck on split UI/Python versions.

Same-line patch drift is compatible; different API lines fail closed.
Keep all existing safety/confirmation contracts intact.
"""
from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "custom_components" / "deploy_relay_v2_dev"


def python_version() -> str:
    tree = ast.parse((LAB / "const.py").read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "VERSION"
    )
    assert isinstance(assignment.value, ast.Constant)
    return assignment.value.value


class FrontendBackendVersionParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (LAB / "frontend" / "lab.js").read_text(encoding="utf-8")
        cls.api = (LAB / "websocket_api.py").read_text(encoding="utf-8")
        cls.panel = (LAB / "panel.py").read_text(encoding="utf-8")
        cls.manifest = json.loads((LAB / "manifest.json").read_text(encoding="utf-8"))

    def test_all_dra_v2_version_markers_are_identical(self):
        match = re.search(
            r'^const DRA_V2_UI_VERSION = "([0-9]+\.[0-9]+\.[0-9]+)";$',
            self.ui,
            re.MULTILINE,
        )
        self.assertIsNotNone(match, "Missing actual frontend build version")
        self.assertEqual(python_version(), match.group(1))
        self.assertEqual(self.manifest["version"], match.group(1))

    def test_server_version_is_derived_from_python_contract(self):
        self.assertIn("from .const import DOMAIN, VERSION", self.api)
        self.assertIn('"version": VERSION', self.api)
        self.assertIn("from .const import DOMAIN, NAME, PANEL_ELEMENT, PANEL_PATH, STATIC_PATH, VERSION", self.panel)
        self.assertIn('f"{STATIC_PATH}/lab.js?v={VERSION}"', self.panel)

    def test_patch_runtime_drift_is_permitted_only_within_same_api_line(self):
        # A changed major/minor or missing runtime must not enter installation.
        self.assertIn("_runtimeCompatible() {", self.ui)
        self.assertIn("ui[1] === backend[1] && ui[2] === backend[2]", self.ui)
        self.assertIn("!this._runtimeCompatible()", self.ui)
        self.assertIn("async _openSingleSelfUpdate(project)", self.ui)
        self.assertIn("A one-project HA batch uses the SAME immutable V1-backed implementation", self.ui)

    def test_installation_security_gates_are_not_bypassed(self):
        start = self.ui.index("  async _prepareInstallation(project) {")
        end = self.ui.index("  _releaseCompletedDeployment(project)", start)
        prepare = self.ui[start:end]
        self.assertIn("!this._runtimeCompatible()", prepare)
        self.assertIn("await this._syncController(project.repository)", prepare)
        self.assertIn("return !!(ui && backend && ui[1] === backend[1] && ui[2] === backend[2])", self.ui)
        self.assertIn("const backend = String(this._serverVersion || \"\").match", self.ui)
        self.assertNotIn("this._serverVersion !== DRA_V2_UI_VERSION", prepare)
        self.assertIn("await this._syncController(project.repository)", prepare)
        self.assertIn('type:"deploy_relay_v2_dev/deployment/prepare"', prepare)

        start = self.ui.index("  async _confirmInstallation() {")
        end = self.ui.index("  _refreshFrontendAfterInstallation()", start)
        confirm = self.ui[start:end]
        self.assertIn("await this._syncController(project.repository)", confirm)
        self.assertIn('type:"deploy_relay_v2_dev/deployment/start"', confirm)
        self.assertIn("confirm:true", confirm)
        self.assertIn("Never send a second installation request", confirm)
        self.assertIn("Ja, Update installieren", self.ui)


if __name__ == "__main__":
    unittest.main()
