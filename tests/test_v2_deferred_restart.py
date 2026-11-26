"""Deferred restart remains HA-owned across distinct completed installations."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "custom_components" / "deploy_relay_v2_dev"


class DeferredRestartContract(unittest.TestCase):
    def test_only_successful_verified_backend_update_is_queued(self):
        source = (BASE / "server_deployment_jobs.py").read_text(encoding="utf-8")
        ast.parse(source)
        after = source.index("await self._registry.transition(identifier, OperationStatus.SUCCESS)")
        near = source[after:after + 400]
        self.assertIn("if post_restart:", near)
        self.assertIn("self._restart_due[identifier] = manifest.project_id", near)
        self.assertIn('async def restart_summary(self)', source)
        self.assertIn('"required": bool(self._restart_due)', source)
        self.assertNotIn("asyncio.create_task(self.restart", source)

    def test_server_status_exposes_read_only_restart_summary(self):
        ws = (BASE / "websocket_api.py").read_text(encoding="utf-8")
        ast.parse(ws)
        start = ws.index("async def async_install_status(")
        end = ws.index("async def async_deployment_restart(", start)
        status = ws[start:end]
        self.assertIn("await runtime.deployment.restart_summary()", status)
        self.assertIn('"restart_summary": restart_summary', status)
        self.assertIn('restart_summary["restart_requested"] = runtime.restart_pending', status)
        self.assertIn('msg["confirm"] is not True', ws[end:])

    def test_ui_requires_explicit_reconfirmation(self):
        js = (BASE / "frontend" / "lab.js").read_text(encoding="utf-8")
        self.assertIn("async _confirmDeferredRestart()", js)
        self.assertIn("this._restartSummary?.required", js)
        self.assertIn('id="dra-deferred-restart-open"', js)
        self.assertIn('id="dra-deferred-restart-confirm"', js)
        self.assertIn("this._installStatusError", js)
        self.assertIn('confirm:true,client_id:this._controllerId', js)


if __name__ == "__main__":
    unittest.main()
