"""Regression: installation start must validate the controller identity in HA."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT / "custom_components" / "deploy_relay_v2_dev" / "websocket_api.py"
UI = ROOT / "custom_components" / "deploy_relay_v2_dev" / "frontend" / "lab.js"


class InstallationStartControllerContract(unittest.TestCase):
    def test_install_start_schema_requires_controller_id(self):
        module = ast.parse(WS.read_text(encoding="utf-8"))
        handler = next(node for node in module.body
                       if isinstance(node, ast.AsyncFunctionDef)
                       and node.name == "async_install_start")
        decorators = [d for d in handler.decorator_list
                      if isinstance(d, ast.Call)
                      and isinstance(d.func, ast.Attribute)
                      and d.func.attr == "websocket_command"]
        self.assertEqual(len(decorators), 1)
        schema = decorators[0].args[0]
        self.assertIsInstance(schema, ast.Dict)
        required = [key.args[0].value for key in schema.keys
                    if isinstance(key, ast.Call)
                    and isinstance(key.func, ast.Attribute)
                    and key.func.attr == "Required"
                    and len(key.args) == 1
                    and isinstance(key.args[0], ast.Constant)]
        self.assertIn("client_id", required)
        self.assertIn("challenge", required)
        self.assertIn("confirm", required)
        code = ast.get_source_segment(WS.read_text(encoding="utf-8"), handler)
        self.assertIn('require_controller(project["project_id"], msg["client_id"])', code)
        self.assertIn("await runtime.deployment.confirm(", code)

    def test_browser_sends_controller_identity_with_explicit_confirmation(self):
        source = UI.read_text(encoding="utf-8")
        beginning = source.index("  async _confirmInstallation() {")
        ending = source.index("  _refreshFrontendAfterInstallation()", beginning)
        handler = source[beginning:ending]
        self.assertIn('type:"deploy_relay_v2_dev/deployment/start"', handler)
        self.assertIn("client_id:this._controllerId", handler)
        self.assertIn("confirm:true", handler)
        self.assertIn("this._installStartUncertain = attempt", handler)
        self.assertIn("Never send a second installation request", handler)


if __name__ == "__main__":
    unittest.main()
