"""Admin-only read-only V2 DEV test commands; never access V1 deployment."""
from __future__ import annotations

import asyncio
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION
from .operation_model import OperationContractError, OperationPhase


def _runtime(hass: HomeAssistant):
    state = hass.data.get(DOMAIN)
    return state.get("runtime") if isinstance(state, dict) else None


@websocket_api.websocket_command({vol.Required("type"): "deploy_relay_v2_dev/test/state"})
@websocket_api.require_admin
async def async_state(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    operations = await runtime.registry.list(limit=12)
    connection.send_result(msg["id"], {
        "version": VERSION,
        "mode": "READ_ONLY_TEST",
        "operations": operations,
    })


@websocket_api.websocket_command({
    vol.Required("type"): "deploy_relay_v2_dev/test/start",
    vol.Required("request_id"): vol.All(str, vol.Length(min=16, max=128)),
})
@websocket_api.require_admin
async def async_start(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return

    async def synthetic_preview(progress):
        # Exactly 20 measured steps; no network, Git or filesystem access.
        for index in range(1, 21):
            await asyncio.sleep(1)
            await progress(OperationPhase.INVENTORY, index, 20)

    try:
        receipt = await runtime.supervisor.start_preview(
            project_key="lab_readonly_preview",
            request_id=msg["request_id"],
            work=synthetic_preview,
        )
    except OperationContractError:
        connection.send_error(msg["id"], "busy", "Testauftrag bereits aktiv oder ungueltig")
        return
    connection.send_result(msg["id"], receipt)


@websocket_api.websocket_command({
    vol.Required("type"): "deploy_relay_v2_dev/test/get",
    vol.Required("operation_id"): str,
})
@websocket_api.require_admin
async def async_get(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    try:
        record = await runtime.registry.get(msg["operation_id"])
    except OperationContractError:
        connection.send_error(msg["id"], "invalid_id", "Ungueltige Auftragskennung")
        return
    if record is None:
        connection.send_error(msg["id"], "not_found", "Auftrag nicht vorhanden")
        return
    connection.send_result(msg["id"], record)


def async_register_commands(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(DOMAIN, {})
    if state.get("commands_registered"):
        return
    for handler in (async_state, async_start, async_get):
        websocket_api.async_register_command(hass, handler)
    state["commands_registered"] = True
