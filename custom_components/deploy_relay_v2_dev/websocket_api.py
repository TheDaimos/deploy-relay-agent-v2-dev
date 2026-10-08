"""Admin-only read-only V2 DEV test commands; never access V1 deployment."""
from __future__ import annotations

import asyncio
import probatio
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION, READONLY_TEST_STEPS
from .operation_model import OperationContractError, OperationPhase
from .git_measurement_export import GitMeasurementError


def _runtime(hass: HomeAssistant):
    state = hass.data.get(DOMAIN)
    return state.get("runtime") if isinstance(state, dict) else None


@websocket_api.websocket_command({probatio.Required("type"): "deploy_relay_v2_dev/test/state"})
@websocket_api.require_admin
@websocket_api.async_response
async def async_state(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    current = await runtime.registry.list(limit=12)
    retained = await runtime.journal.list(limit=12)
    seen = {item["operation_id"] for item in current}
    operations = (current + [item for item in retained
                             if item["operation_id"] not in seen])[:12]
    connection.send_result(msg["id"], {
        "version": VERSION,
        "mode": "READ_ONLY_TEST",
        "operations": operations,
        "measurement": runtime.measurement.summary(),
        "suite": runtime.suite.summary(),
        "git_configured": runtime.git_export.configured,
        "git_available": runtime.git_export.available,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/start",
    probatio.Required("request_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_start(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return

    async def synthetic_preview(progress):
        # Exactly 40 measured 1-second steps; no network, Git or filesystem access.
        for index in range(1, READONLY_TEST_STEPS + 1):
            await asyncio.sleep(1)
            await progress(OperationPhase.INVENTORY, index, READONLY_TEST_STEPS)

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
    probatio.Required("type"): "deploy_relay_v2_dev/test/measure",
    probatio.Required("request_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_measure(hass, connection, msg):
    """Separate opt-in measurement; never authorize mutation or background idle work."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    try:
        receipt = await runtime.supervisor.start_preview(
            project_key="lab_readonly_preview",
            request_id=msg["request_id"],
            work=runtime.measurement.run,
        )
        runtime.measurement.claim(str(receipt["operation_id"]))
    except OperationContractError:
        connection.send_error(msg["id"], "busy", "Messlauf bereits aktiv oder ungueltig")
        return
    connection.send_result(msg["id"], receipt)




@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/multicore",
    probatio.Required("request_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_multicore(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    try:
        receipt = await runtime.supervisor.start_preview(
            project_key="lab_readonly_preview",
            request_id=msg["request_id"],
            work=runtime.suite.run_multicore,
        )
        runtime.suite.claim(str(receipt["operation_id"]))
    except OperationContractError:
        connection.send_error(msg["id"], "busy", "Leseauftrag aktiv oder ungueltig")
        return
    connection.send_result(msg["id"], receipt)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/all",
    probatio.Required("request_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_all(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    try:
        receipt = await runtime.supervisor.start_preview(
            project_key="lab_readonly_preview",
            request_id=msg["request_id"],
            work=runtime.suite.run_all,
        )
        runtime.suite.claim(str(receipt["operation_id"]))
    except OperationContractError:
        connection.send_error(msg["id"], "busy", "Gesamttest aktiv oder ungueltig")
        return
    connection.send_result(msg["id"], receipt)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/get",
    probatio.Required("operation_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
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
        record = await runtime.journal.get(msg["operation_id"])
    if record is None:
        connection.send_error(msg["id"], "not_found", "Auftrag nicht vorhanden")
        return
    connection.send_result(msg["id"], record)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/git_configure",
    probatio.Required("clear"): bool,
    probatio.Required("token"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_git_configure(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    try:
        await runtime.git_export.configure(
            token=msg["token"], clear=msg["clear"],
        )
    except GitMeasurementError:
        connection.send_error(msg["id"], "invalid_export", "Git-Zugang konnte nicht gespeichert werden")
        return
    connection.send_result(msg["id"], {
        "configured": runtime.git_export.configured,
        "repository": "TheDaimos/deploy-relay-agent-v2-dev",
        "branch": "main",
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/git_export",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_git_export(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    summary = runtime.measurement.summary()
    if summary is None:
        connection.send_error(msg["id"], "no_measurement", "Kein abgeschlossener Messlauf vorhanden")
        return
    try:
        operation = await runtime.registry.get(str(summary["operation_id"]))
    except OperationContractError:
        operation = None
    if operation is None or operation["status"] != "success":
        connection.send_error(msg["id"], "no_measurement", "Kein abgeschlossener Messlauf vorhanden")
        return
    try:
        result = await runtime.git_export.export(summary, version=VERSION)
    except GitMeasurementError:
        connection.send_error(msg["id"], "export_failed", "Git-Export nicht möglich; Zugang und Repository prüfen")
        return
    connection.send_result(msg["id"], result)


def async_register_commands(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(DOMAIN, {})
    if state.get("commands_registered"):
        return
    for handler in (async_state, async_start, async_measure, async_multicore,
                    async_all, async_get, async_git_configure, async_git_export):
        websocket_api.async_register_command(hass, handler)
    state["commands_registered"] = True
