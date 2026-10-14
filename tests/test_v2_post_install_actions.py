"""Run the real HA restart WebSocket handler against an isolated fake HA runtime.

No Home Assistant installation is ever touched during these tests.
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
import unittest

LAB = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"


def isolated_handler():
    source = (LAB / "websocket_api.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    handler = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                   and node.name == "async_deployment_restart")
    # Only strip HA decorators to execute the exact production function body
    # against synthetic service/job data.
    handler.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[handler], type_ignores=[]))
    globals_map = {
        "OperationContractError": type("OperationContractError", (ValueError,), {}),
        "_runtime": lambda hass: hass.runtime,
    }
    exec(compile(module, "<isolated-v2-restart-handler>", "exec"), globals_map)
    return globals_map[handler.name], source


class FakeConnection:
    def __init__(self):
        self.result = None
        self.error = None

    def send_result(self, identifier, result):
        self.result = (identifier, result)

    def send_error(self, identifier, code, message):
        self.error = (identifier, code, message)


class FakeDeployment:
    def __init__(self, job, active=False):
        self.job = job
        self.active = active

    async def get(self, operation_id):
        return self.job

    async def list(self):
        return [self.job] + ([{"status": "running"}] if self.active else [])


class FakeServices:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    async def async_call(self, domain, service, data, *, blocking):
        self.calls.append((domain, service, data, blocking))
        if self.fail:
            raise RuntimeError("synthetic service failure")


class FakeHA:
    def __init__(self, job, active=False, fail=False):
        self.runtime = type("Runtime", (), {})()
        self.runtime.restart_lock = asyncio.Lock()
        self.runtime.restart_pending = False
        self.runtime.deployment = FakeDeployment(job, active)
        self.services = FakeServices(fail)


GOOD_ID = "a" * 32
GOOD = {"operation_id": GOOD_ID, "status": "success", "phase": "complete",
        "restart_required": True}


class PostInstallTests(unittest.TestCase):
    def test_lifecycle_flags_are_from_verified_engine(self):
        source = (LAB / "server_deployment_jobs.py").read_text(encoding="utf-8")
        self.assertIn('result.lifecycle == "frontend_reload"', source)
        self.assertIn('result.lifecycle == "integration_reload"', source)
        self.assertIn('restart_required=post_restart', source)
        self.assertIn('and not post_restart', source)
        policy = (LAB / "v1_engine" / "lifecycle_policy.py").read_text(encoding="utf-8")
        self.assertIn("all(is_safe_frontend_target(item.target_path) for item in changed)", policy)

    def test_restart_handler_requires_admin_and_confirmed_real_job(self):
        handler, source = isolated_handler()
        self.assertIn('probatio.Required("confirm"): bool', source)
        p = source.index("async def async_deployment_restart(")
        self.assertIn("@websocket_api.require_admin", source[p-100:p])
        self.assertIn('"deploy_relay_v2_dev/deployment/restart"', source)
        self.assertIn("async_deployment_restart,", source)
        async def run():
            tests = [
                (dict(GOOD), False, False, False, "not_confirmed"),
                (dict(GOOD, status="failed"), True, False, False, "not_permitted"),
                (dict(GOOD, phase="install"), True, False, False, "not_permitted"),
                (dict(GOOD, restart_required=False), True, False, False, "not_permitted"),
                (dict(GOOD), True, True, False, "deployment_active"),
            ]
            for job, confirm, active, fail, expected_error in tests:
                hass=FakeHA(job, active, fail)
                conn=FakeConnection()
                await handler(hass, conn, {"id": 1, "operation_id": GOOD_ID, "confirm":confirm})
                assert conn.error[1] == expected_error, conn.error
                assert hass.services.calls == [], "no restart may be scheduled"
                assert not hass.runtime.restart_pending

            hass=FakeHA(dict(GOOD))
            conn=FakeConnection()
            await handler(hass,conn,{"id":4,"operation_id":"bad","confirm":True})
            assert conn.error[1] == "invalid_operation"
            assert hass.services.calls == []

            hass=FakeHA(dict(GOOD))
            conn=FakeConnection()
            await handler(hass,conn,{"id":5,"operation_id":GOOD_ID,"confirm":True})
            assert conn.result[1]["restart_requested"] is True
            assert conn.result[1]["operation_id"] == GOOD_ID
            assert hass.services.calls == [("homeassistant","restart",{},False)]
            assert hass.runtime.restart_pending
            conn2=FakeConnection()
            await handler(hass,conn2,{"id":6,"operation_id":GOOD_ID,"confirm":True})
            assert conn2.error[1] == "restart_pending"
            assert len(hass.services.calls) == 1

            hass=FakeHA(dict(GOOD),fail=True)
            conn=FakeConnection()
            await handler(hass,conn,{"id":7,"operation_id":GOOD_ID,"confirm":True})
            assert conn.error[1] == "restart_failed"
            assert not hass.runtime.restart_pending
        asyncio.run(run())

    def test_contextual_frontend_action_and_explicit_restart_dialog(self):
        ui = (LAB / "frontend" / "lab.js").read_text(encoding="utf-8")
        self.assertIn('id="dra-frontend-refresh"', ui)
        self.assertIn('id="dra-ha-restart-open"', ui)
        self.assertIn('id="dra-ha-restart-cancel"', ui)
        self.assertIn('id="dra-ha-restart-confirm"', ui)
        self.assertIn('"Ja, Home Assistant neu starten"', ui) if '"Ja, Home Assistant neu starten"' in ui else self.assertIn("Ja, Home Assistant neu starten", ui)
        self.assertIn('window.location.reload()', ui)
        self.assertIn('postInstallJob.frontend_reload_possible === true', ui)
        self.assertIn('postInstallJob.restart_required === true', ui)
        self.assertIn('!this._restartDialogOpen', ui)
        self.assertIn('this._serverVersion !== DRA_V2_UI_VERSION', ui)
        self.assertIn('type:"deploy_relay_v2_dev/deployment/restart"', ui)
        self.assertIn('operation_id:job.operation_id,confirm:true', ui)
        self.assertNotIn('type:"deploy_relay_v2_dev/deployment/restart",confirm:true,operation_id:undefined', ui)


if __name__ == "__main__":
    unittest.main()
