"""Admin-only read-only V2 DEV test commands; never access V1 deployment."""
from __future__ import annotations

import asyncio
import probatio
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pathlib import Path

from .remote_source import inspect_public_repository, GitReadAuthError
from .source_preflight import PreflightError

from .const import DOMAIN, VERSION, READONLY_TEST_STEPS
from .operation_model import OperationContractError, OperationPhase
from .git_measurement_export import GitMeasurementError
from .project_catalog import CatalogError, v1_proposals
from .settings import SettingsError


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
        "central_export": runtime.git_export.status(),
        "git_available": runtime.git_export.available,
        "git_read_configured": runtime.source_auth.configured,
        "projects": runtime.projects.list(),
        "settings": runtime.settings.snapshot(),
        "settings_effective": runtime.settings.effective(),
        "cpu_status": runtime.settings.core_status(),
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
    probatio.Required("type"): "deploy_relay_v2_dev/archive_repository/check",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_archive_repository_check(hass, connection, msg):
    """Recheck saved private GitHub source; never return the secret."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Archivverwaltung nicht bereit")
        return
    try:
        status = await runtime.git_export.check_archive()
    except GitMeasurementError:
        connection.send_error(
            msg["id"], "archive_check_failed",
            "Privates Repository oder gespeicherter GitHub-Zugang nicht erreichbar.",
        )
        return
    connection.send_result(msg["id"], status)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/archive_repository/configure",
    probatio.Required("repository"): str,
    probatio.Required("token"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_archive_repository_configure(hass, connection, msg):
    """Accept secret only in one authenticated WS request; never echo it."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Archivverwaltung nicht bereit")
        return
    try:
        status = await runtime.git_export.configure_archive(
            msg["repository"], msg["token"],
        )
    except GitMeasurementError:
        connection.send_error(
            msg["id"], "archive_configuration_failed",
            "Privates Repository nicht erreichbar, Token ungueltig oder Speicherung fehlgeschlagen.",
        )
        return
    connection.send_result(msg["id"], status)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/archive_repository/set",
    probatio.Required("repository"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_archive_repository_set(hass, connection, msg):
    """Only admin-selected private archive; never choose a vendor default."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Archivverwaltung nicht bereit")
        return
    try:
        status = await runtime.git_export.set_repository(msg["repository"])
    except GitMeasurementError:
        connection.send_error(
            msg["id"], "invalid_archive_repository",
            "Export-Repository konnte nicht gespeichert werden. Laufenden Export prüfen.",
        )
        return
    connection.send_result(msg["id"], status)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/archive_repository/clear",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_archive_repository_clear(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Archivverwaltung nicht bereit")
        return
    try:
        status = await runtime.git_export.clear_repository()
    except GitMeasurementError:
        connection.send_error(
            msg["id"], "archive_repository_locked",
            "Archivziel nicht entfernt: ein Export wartet auf Wiederholung.",
        )
        return
    connection.send_result(msg["id"], status)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/download_json",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_download_json(hass, connection, msg):
    """Safe local download. No GitHub repository, token or queue is required."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Testlabor nicht gestartet")
        return
    current = await runtime.registry.list(limit=1)
    latest_id = current[0]["operation_id"] if current else None
    suite = runtime.suite.summary()
    solo = runtime.measurement.summary()
    summary = (suite if suite and suite.get("operation_id") == latest_id
               else solo if solo and solo.get("operation_id") == latest_id
               else None)
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
        document = runtime.git_export.local_download(summary, version=VERSION)
    except GitMeasurementError:
        connection.send_error(msg["id"], "invalid_diagnostics", "Diagnose nicht für den Download geeignet")
        return
    connection.send_result(msg["id"], document)


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
    current = await runtime.registry.list(limit=1)
    latest_id = current[0]["operation_id"] if current else None
    suite = runtime.suite.summary()
    solo = runtime.measurement.summary()
    summary = (suite if suite and suite.get("operation_id") == latest_id
               else solo if solo and solo.get("operation_id") == latest_id
               else None)
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
        connection.send_error(
            msg["id"], "archive_export_failed",
            "Privater Zentralexport fehlgeschlagen. Zugang/Schreibrechte prüfen. "
            "Ein vorbereiteter Export bleibt lokal für einen erneuten Versuch erhalten.",
        )
        return
    connection.send_result(msg["id"], result)




@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/test/git_retry",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_git_retry(hass, connection, msg):
    """Explicitly retry a locally retained report; never fabricate new export ID."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Zentralexport nicht bereit")
        return
    try:
        result = await runtime.git_export.retry_pending()
    except GitMeasurementError:
        connection.send_error(
            msg["id"], "archive_retry_failed",
            "Erneute private Übertragung fehlgeschlagen. Der lokale Export bleibt erhalten.",
        )
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/list",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_list(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    connection.send_result(msg["id"], {
        "projects": runtime.projects.list(),
        "deployment_enabled": False,
        "backup_mutation_enabled": False,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/v1_preview",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_v1_preview(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        candidates = v1_proposals(hass.config_entries)
    except CatalogError:
        connection.send_error(msg["id"], "invalid_inventory", "V1-Projektliste nicht lesbar")
        return
    connection.send_result(msg["id"], {
        "candidates": candidates,
        "requires_confirmation": True,
        "credentials_copied": False,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/import_v1",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_import_v1(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        result = await runtime.projects.import_v1(hass.config_entries)
    except CatalogError:
        connection.send_error(msg["id"], "import_failed", "Übernahme konnte nicht gespeichert werden")
        return
    connection.send_result(msg["id"], {**result, "projects": runtime.projects.list()})


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/add",
    probatio.Required("repository"): str,
    probatio.Required("name"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_add(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        record = await runtime.projects.add(msg["repository"], msg["name"])
    except CatalogError:
        connection.send_error(msg["id"], "invalid_project", "Projekt konnte nicht angelegt werden")
        return
    connection.send_result(msg["id"], {
        "project": record, "projects": runtime.projects.list()
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/retention",
    probatio.Required("repository"): str,
    probatio.Required("backup_retention"): int,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_retention(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        record = await runtime.projects.set_retention(
            msg["repository"], msg["backup_retention"],
        )
    except CatalogError:
        connection.send_error(msg["id"], "invalid_retention", "Sicherungsanzahl ungültig")
        return
    connection.send_result(msg["id"], {
        "project": record, "projects": runtime.projects.list(),
        "backups_deleted": 0,
    })



@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/settings/get",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_settings_get(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Einstellungen nicht bereit")
        return
    connection.send_result(msg["id"], {
        "settings": runtime.settings.snapshot(),
        "effective": runtime.settings.effective(),
        "cpu_status": runtime.settings.core_status(),
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/settings/save",
    probatio.Required("mode"): str,
    probatio.Required("max_readonly_jobs"): int,
    probatio.Required("max_worker_processes"): int,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_settings_save(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Einstellungen nicht bereit")
        return
    try:
        result = await runtime.settings.save({
            "mode": msg["mode"],
            "max_readonly_jobs": msg["max_readonly_jobs"],
            "max_worker_processes": msg["max_worker_processes"],
        })
    except SettingsError:
        connection.send_error(msg["id"], "invalid_settings", "Einstellungen nicht gespeichert")
        return
    connection.send_result(msg["id"], {
        "settings": result, "effective": runtime.settings.effective(),
        "cpu_status": runtime.settings.core_status()
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/settings/ack_cpu_warning",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_settings_ack_cpu_warning(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Einstellungen nicht bereit")
        return
    try:
        result = await runtime.settings.acknowledge_warning()
    except SettingsError:
        connection.send_error(msg["id"], "settings_failed", "Warnung konnte nicht bestätigt werden")
        return
    connection.send_result(msg["id"], {"cpu_status": result})


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/preselect",
    probatio.Required("repository"): str,
    probatio.Required("enabled"): bool,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_preselect(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        record = await runtime.projects.set_batch_preselect(
            msg["repository"], msg["enabled"])
    except CatalogError:
        connection.send_error(msg["id"], "invalid_project", "Vorauswahl nicht gespeichert")
        return
    connection.send_result(msg["id"], {
        "project": record, "projects": runtime.projects.list()
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/batch/preview",
    probatio.Required("repositories"): list,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_batch_preview(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        snapshot = runtime.projects.batch_preview(msg["repositories"])
    except CatalogError:
        connection.send_error(msg["id"], "invalid_selection", "Auswahl nicht gültig")
        return
    connection.send_result(msg["id"], snapshot)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/source_preview",
    probatio.Required("repository"): str,
    probatio.Required("ref"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_source_preview(hass, connection, msg):
    """Admin-only exact-commit public GitHub check; V1 and HA target unchanged."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    # No arbitrary GitHub URL or unregistered project can trigger a local scan.
    repo = msg["repository"]
    if type(repo) is not str or not any(
        project["repository"].casefold() == repo.casefold()
        for project in runtime.projects.list()
    ):
        connection.send_error(msg["id"], "not_registered", "Projekt nicht registriert")
        return
    # Do not spawn multiple network scans/filesystem enumerations simultaneously.
    if runtime.source_scan_lock.locked():
        connection.send_error(msg["id"], "busy", "Quellprüfung läuft bereits")
        return
    try:
        async with runtime.source_scan_lock:
            report = await asyncio.wait_for(
                inspect_public_repository(
                    async_get_clientsession(hass),
                    Path(hass.config.path()),
                    repo,
                    msg["ref"], token=runtime.source_auth.token,
                ),
                timeout=45,
            )
    except (PreflightError, TimeoutError, OSError, ValueError):
        connection.send_error(
            msg["id"], "source_unavailable",
            "Quellprüfung nicht möglich oder Quelle nicht vertrauenswürdig",
        )
        return
    connection.send_result(msg["id"], report)



@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/git_read/configure",
    probatio.Required("token"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_git_read_configure(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "V2-GitHub-Lesezugang nicht bereit")
        return
    try:
        await runtime.source_auth.configure(msg["token"])
    except GitReadAuthError:
        connection.send_error(msg["id"], "invalid_credential", "Lesezugang nicht gespeichert")
        return
    connection.send_result(msg["id"], {
        "configured": runtime.source_auth.configured
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/git_read/clear",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_git_read_clear(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "V2-GitHub-Lesezugang nicht bereit")
        return
    try:
        await runtime.source_auth.clear()
    except GitReadAuthError:
        connection.send_error(msg["id"], "credential_error", "Lesezugang nicht zurückgesetzt")
        return
    connection.send_result(msg["id"], {"configured": False})


def async_register_commands(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(DOMAIN, {})
    if state.get("commands_registered"):
        return
    for handler in (async_state, async_start, async_measure, async_multicore,
                    async_all, async_get, async_git_export, async_git_retry,
                    async_projects_list, async_projects_v1_preview,
                    async_projects_import_v1, async_projects_add,
                    async_projects_retention, async_projects_preselect,
                    async_settings_get, async_settings_save, async_settings_ack_cpu_warning,
                    async_batch_preview, async_projects_source_preview,
                    async_git_read_configure, async_git_read_clear,
                    async_archive_repository_set, async_archive_repository_clear,
                    async_archive_repository_configure,
                    async_archive_repository_check,
                    async_download_json):
        websocket_api.async_register_command(hass, handler)
    state["commands_registered"] = True
