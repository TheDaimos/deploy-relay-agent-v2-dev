"""Admin-only read-only V2 DEV test commands; never access V1 deployment."""
from __future__ import annotations

import asyncio
import probatio
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pathlib import Path

from .remote_source import inspect_public_repository, inspect_repository_connection, source_ref, GitReadAuthError
from .source_preflight import PreflightError
from .source_diagnostics import (SourceDiagnosticsError, classify_source_failure, resource_snapshot)
from .target_ownership import TargetClaimError, assess_target_claims

from .const import DOMAIN, VERSION
from .operation_model import OperationContractError, OperationPhase
from .git_measurement_export import GitMeasurementError
from .project_catalog import CatalogError, v1_proposals
from .settings import SettingsError


def _runtime(hass: HomeAssistant):
    state = hass.data.get(DOMAIN)
    return state.get("runtime") if isinstance(state, dict) else None


def _project_list(runtime):
    return [{**row, "token_configured": runtime.project_auth.status(row["repository"])["configured"],
             "token_suffix": runtime.project_auth.status(row["repository"])["suffix"]}
            for row in runtime.projects.list()]


async def _exportable_diagnostic(runtime, operations=None):
    """Single source of truth for UI eligibility, JSON and Git export.

    A later non-measurement preview must not hide an earlier successfully
    completed measurement. Failed and running operations cannot be exported.
    """
    suite = runtime.suite.summary()
    solo = runtime.measurement.summary()
    choices = [
        result for result in (suite, solo)
        if isinstance(result, dict) and isinstance(result.get("operation_id"), str)
    ]
    if not choices:
        return None
    if operations is None:
        operations = await runtime.registry.list(limit=12)
    # Prefer the newest completed diagnostic whose ID remains in registry.
    candidates = {result["operation_id"]: result for result in reversed(choices)}
    for record in operations:
        op_id = record.get("operation_id")
        if record.get("status") == "success" and op_id in candidates:
            # Defend against stale/unrelated in-memory data.
            live = await runtime.registry.get(str(op_id))
            if live is not None and live["status"] == "success":
                return candidates[op_id]
    return None


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
    eligible = await _exportable_diagnostic(runtime, current)
    connection.send_result(msg["id"], {
        "version": VERSION,
        "mode": "READ_ONLY_TEST",
        "operations": operations,
        "measurement": runtime.measurement.summary(),
        "suite": runtime.suite.summary(),
        "git_configured": runtime.git_export.configured,
        "central_export": runtime.git_export.status(),
        "diagnostics_export_ready": eligible is not None,
        "deployment_log_count": runtime.source_diagnostics.count(),
        "diagnostics_export_kind": eligible.get("mode") if eligible else None,
        "git_available": runtime.git_export.available,
        "git_read_configured": runtime.source_auth.configured,
        "projects": _project_list(runtime),
        "picker_batch_position": runtime.projects.picker_batch_position,
        "settings": runtime.settings.snapshot(),
        "settings_effective": runtime.settings.effective(),
        "cpu_status": runtime.settings.core_status(),
    })


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
    summary = await _exportable_diagnostic(runtime)
    if summary is None:
        connection.send_error(
            msg["id"], "no_measurement",
            "Noch keine erfolgreich abgeschlossene exportierbare Diagnose vorhanden",
        )
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
    summary = await _exportable_diagnostic(runtime)
    if summary is None:
        connection.send_error(
            msg["id"], "no_measurement",
            "Noch keine erfolgreich abgeschlossene exportierbare Diagnose vorhanden",
        )
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
        "projects": _project_list(runtime),
        "picker_batch_position": runtime.projects.picker_batch_position,
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
    probatio.Required("repositories"): list,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_import_v1(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        result = await runtime.projects.import_v1(hass.config_entries, msg["repositories"])
    except CatalogError:
        connection.send_error(msg["id"], "import_failed", "Übernahme konnte nicht gespeichert werden")
        return
    connection.send_result(msg["id"], {**result, "projects": _project_list(runtime)})


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/add",
    probatio.Required("repository"): str,
    probatio.Required("name"): str,
    probatio.Optional("note"): str,
    probatio.Optional("active"): bool,
    probatio.Optional("access_mode"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_add(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        record = await runtime.projects.add(msg["repository"], msg["name"],
                                            msg.get("note", ""), msg.get("active", True),
                                            msg.get("access_mode", "read_only"))
    except CatalogError:
        connection.send_error(msg["id"], "invalid_project", "Projekt konnte nicht angelegt werden")
        return
    connection.send_result(msg["id"], {
        "project": record, "projects": _project_list(runtime)
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/manage",
    probatio.Required("action"): str,
    probatio.Required("repository"): str,
    probatio.Optional("direction"): int,
    probatio.Optional("new_repository"): str,
    probatio.Optional("name"): str,
    probatio.Optional("note"): str,
    probatio.Optional("active"): bool,
    probatio.Optional("access_mode"): str,
    probatio.Optional("confirmed"): bool,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_manage(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        action = msg["action"]
        if action == "move":
            await runtime.projects.move(msg["repository"], msg.get("direction", 0))
        elif action == "move_batch":
            if msg["repository"] != "__batch_picker__":
                raise CatalogError("invalid batch picker identity")
            await runtime.projects.move_picker_batch(msg.get("direction", 0))
        elif action == "configure":
            if not all(k in msg for k in ("new_repository", "name", "note", "active")):
                raise CatalogError("incomplete settings")
            old_repo = msg["repository"]
            new_repo = msg["new_repository"]
            if old_repo.casefold() != new_repo.casefold():
                # Reject unknown identities and check the new Git source before changing metadata.
                previous = next((p for p in runtime.projects.list()
                                 if p["repository"].casefold() == old_repo.casefold()), None)
                if previous is None:
                    raise CatalogError("unknown project")
                if runtime.source_scan_lock.locked():
                    raise CatalogError("source check busy")
                async with runtime.source_scan_lock:
                    try:
                        report = await asyncio.wait_for(inspect_public_repository(
                            async_get_clientsession(hass), Path(hass.config.path()), new_repo, "",
                            token=runtime.project_auth.token(old_repo) or runtime.source_auth.token), timeout=45)
                    except (PreflightError, TimeoutError, OSError, ValueError):
                        raise CatalogError("new repository unverified") from None
                if report.get("sources_verified") is not True or report.get("installation_enabled") is not False:
                    raise CatalogError("new repository unverified")
                await runtime.projects.configure(old_repo, new_repo,
                                                 msg["name"], msg["note"], msg["active"],
                                                 msg.get("access_mode"))
                try:
                    await runtime.project_auth.rename(old_repo, new_repo)
                except GitReadAuthError:
                    await runtime.projects.configure(new_repo, old_repo, previous["name"],
                                                     previous.get("note", ""), previous.get("active", True))
                    raise
            else:
                await runtime.projects.configure(old_repo, new_repo,
                                                 msg["name"], msg["note"], msg["active"],
                                                 msg.get("access_mode"))
        elif action == "remove":
            if msg.get("confirmed") is not True:
                raise CatalogError("confirmation required")
            if not any(p["repository"].casefold() == msg["repository"].casefold() for p in runtime.projects.list()):
                raise CatalogError("unknown project")
            await runtime.project_auth.delete(msg["repository"])
            await runtime.projects.remove(msg["repository"])
        else:
            raise CatalogError("unsupported action")
    except (CatalogError, GitReadAuthError):
        connection.send_error(msg["id"], "invalid_project_action", "Projektaktion abgelehnt")
        return
    connection.send_result(msg["id"], {"projects": _project_list(runtime),
                                       "picker_batch_position": runtime.projects.picker_batch_position,
                                       "installation_enabled": False})


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/token",
    probatio.Required("repository"): str,
    probatio.Required("token"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_token(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    repository = msg["repository"]
    if not any(p["repository"].casefold() == repository.casefold() for p in runtime.projects.list()):
        connection.send_error(msg["id"], "not_registered", "Projekt nicht registriert")
        return
    try:
        await runtime.project_auth.save(repository, msg["token"])
    except (CatalogError, GitReadAuthError):
        connection.send_error(msg["id"], "invalid_credential", "Projekttoken nicht gespeichert")
        return
    connection.send_result(msg["id"], {"projects": _project_list(runtime)})


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
        "project": record, "projects": _project_list(runtime),
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
        "project": record, "projects": _project_list(runtime)
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
    probatio.Required("type"): "deploy_relay_v2_dev/projects/connection_check",
    probatio.Required("repository"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_connection_check(hass, connection, msg):
    """GET /repos for selected registered project. Never tests or enables writes."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    repo = msg["repository"]
    if not any(p["repository"].casefold() == repo.casefold() for p in runtime.projects.list()):
        connection.send_error(msg["id"], "not_registered", "Projekt nicht registriert")
        return
    if runtime.source_scan_lock.locked():
        connection.send_error(msg["id"], "busy", "Eine GitHub-Prüfung läuft bereits")
        return
    try:
        async with runtime.source_scan_lock:
            result = await asyncio.wait_for(
                inspect_repository_connection(
                    async_get_clientsession(hass), repo,
                    token=runtime.project_auth.token(repo) or runtime.source_auth.token,
                ), timeout=20)
    except (PreflightError, TimeoutError, OSError, ValueError):
        connection.send_result(msg["id"], {
            "connected": False, "repository": repo,
            "reason": "Repository nicht erreichbar oder Zugriff verweigert",
            "write_tested": False,
        })
        return
    connection.send_result(msg["id"], result)


async def _inspect_source_preview(hass, runtime, repo: str, ref: str) -> dict:
    """Shared internal read-only source inspection; no connection ownership."""
    trace = runtime.source_diagnostics.begin()
    resources = resource_snapshot(runtime.settings)
    if (type(repo) is not str or not any(
        project["repository"].casefold() == repo.casefold()
        for project in _project_list(runtime)
    )):
        runtime.source_diagnostics.finish(
            trace, success=False, reason="source_unavailable", resources=resources)
        raise PreflightError("not_registered")
    runtime.source_diagnostics.bind_project(trace, repo)
    if runtime.source_scan_lock.locked():
        runtime.source_diagnostics.finish(
            trace, success=False, reason="source_unavailable", resources=resources)
        raise PreflightError("busy")
    try:
        async with runtime.source_scan_lock:
            report = await asyncio.wait_for(
                inspect_public_repository(
                    async_get_clientsession(hass),
                    Path(hass.config.path()),
                    repo,
                    ref, token=runtime.project_auth.token(repo) or runtime.source_auth.token,
                    stage_hook=lambda stage: runtime.source_diagnostics.stage(trace, stage),
                ),
                timeout=45,
            )
            runtime.source_diagnostics.stage(trace, "target_claims")
            report["target_claims"] = assess_target_claims([report])
    except asyncio.CancelledError:
        # ConfigEntry unloading cancels the task; no success and no mutation.
        runtime.source_diagnostics.finish(
            trace, success=False, reason="source_unavailable", resources=resources)
        raise
    except (PreflightError, TargetClaimError, TimeoutError, OSError, ValueError) as exc:
        runtime.source_diagnostics.finish(
            trace, success=False,
            reason=classify_source_failure(trace["stage"], exc), resources=resources)
        raise PreflightError("source_unavailable") from None
    except Exception:
        runtime.source_diagnostics.finish(
            trace, success=False, reason="unexpected_error", resources=resources)
        raise PreflightError("source_unavailable") from None
    runtime.source_diagnostics.finish(trace, success=True, resources=resources)
    return report


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/source_preview",
    probatio.Required("repository"): str,
    probatio.Required("ref"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_projects_source_preview(hass, connection, msg):
    """Legacy read-only endpoint retained during controlled G2 transition."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Projektverwaltung nicht bereit")
        return
    try:
        report = await _inspect_source_preview(
            hass, runtime, msg["repository"], msg["ref"])
    except PreflightError:
        connection.send_error(
            msg["id"], "source_unavailable", "Quellprüfung nicht möglich")
        return
    connection.send_result(msg["id"], report)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/source_job/start",
    probatio.Required("repository"): str,
    probatio.Required("ref"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_source_job_start(hass, connection, msg):
    """Accept a registered source and return a HA-owned read-only job ID."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Auftragsverwaltung nicht bereit")
        return
    repo = msg["repository"]
    if type(repo) is not str or not any(
        project["repository"].casefold() == repo.casefold()
        for project in _project_list(runtime)
    ):
        connection.send_error(msg["id"], "not_registered", "Projekt nicht registriert")
        return
    try:
        ref = source_ref(msg["ref"])
        snapshot = await runtime.source_preview_jobs.start(
            repo, ref, inspect=lambda: _inspect_source_preview(hass, runtime, repo, ref),
        )
    except (PreflightError, ValueError):
        connection.send_error(msg["id"], "preview_unavailable", "Leseauftrag nicht möglich")
        return
    connection.send_result(msg["id"], snapshot)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/source_job/status",
    probatio.Optional("operation_id", default=""): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_source_job_status(hass, connection, msg):
    """Return latest or exact bounded snapshot, independent of browser session."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Auftragsverwaltung nicht bereit")
        return
    try:
        identifier = msg["operation_id"]
        snapshot = (await runtime.source_preview_jobs.get(identifier)
                    if identifier else await runtime.source_preview_jobs.latest())
    except ValueError:
        connection.send_error(msg["id"], "invalid_operation", "Auftragskennung ungültig")
        return
    connection.send_result(msg["id"], {
        "schema": "dra-v2-source-preview-job-status.v1",
        "job": snapshot, "installation_enabled": False,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/projects/source_job/history",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_source_job_history(hass, connection, msg):
    """History metadata only, NEVER reusable reports or Git identifiers."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Auftragshistorie nicht bereit")
        return
    try:
        records = await runtime.source_job_history.list()
    except Exception:
        connection.send_error(msg["id"], "history_unavailable", "Auftragshistorie nicht lesbar")
        return
    connection.send_result(msg["id"], {
        "schema": "dra-v2-source-job-history-result.v1",
        "records": records,
        "installation_enabled": False,
        "resume_allowed": False,
        "source_preview_saved": False,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/deployment/logs",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_deployment_logs(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Diagnose nicht bereit")
        return
    connection.send_result(msg["id"], {
        "schema": "dra-v2-dev-deployment-logs.v1",
        "version": VERSION,
        "records": runtime.source_diagnostics.entries(),
        "count": runtime.source_diagnostics.count(),
        "installation_enabled": False,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/deployment/logs/clear",
    probatio.Required("confirm"): bool,
    probatio.Required("expected_run_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_deployment_logs_clear(hass, connection, msg):
    """Explicit administrative CAS clear of V2 in-memory preview logs only."""
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Diagnose nicht bereit")
        return
    if msg["confirm"] is not True:
        connection.send_error(msg["id"], "confirmation_required", "Löschen nicht bestätigt")
        return
    try:
        count = runtime.source_diagnostics.clear(expected_run_id=msg["expected_run_id"])
    except SourceDiagnosticsError:
        connection.send_error(msg["id"], "logs_changed", "Protokolle geändert – bitte neu laden")
        return
    connection.send_result(msg["id"], {
        "cleared": count, "remaining": 0, "archive_unchanged": True,
        "installation_enabled": False,
    })


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/deployment/logs/download",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_deployment_logs_download(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Diagnose nicht bereit")
        return
    record = runtime.source_diagnostics.latest()
    if record is None:
        connection.send_error(msg["id"], "no_logs", "Noch keine Deployment-Prüfung vorhanden")
        return
    try:
        result = runtime.git_export.local_download(record, version=VERSION)
    except GitMeasurementError:
        connection.send_error(msg["id"], "invalid_logs", "Diagnose nicht exportierbar")
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({
    probatio.Required("type"): "deploy_relay_v2_dev/deployment/logs/export",
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_deployment_logs_export(hass, connection, msg):
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], "not_ready", "Diagnose nicht bereit")
        return
    record = runtime.source_diagnostics.latest()
    if record is None:
        connection.send_error(msg["id"], "no_logs", "Noch keine Deployment-Prüfung vorhanden")
        return
    # User-mandated exclusive private diagnostic destination.
    # No implicit configuration, fallback repository, or public upload.
    if runtime.git_export.repository != "TheDaimos/Project-Log-And-Export":
        connection.send_error(msg["id"], "archive_not_approved",
                              "Privates zentrales Diagnosearchiv nicht ausgewählt")
        return
    try:
        source_repository = runtime.source_diagnostics.private_repository_for(record["run_id"])
        result = await runtime.git_export.export(
            record, version=VERSION, private_source_repository=source_repository)
    except GitMeasurementError:
        connection.send_error(msg["id"], "archive_export_failed",
                              "Privater Diagnoseexport fehlgeschlagen")
        return
    connection.send_result(msg["id"], result)


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
    for handler in (async_state, async_measure, async_multicore,
                    async_all, async_get, async_git_export, async_git_retry,
                    async_projects_list, async_projects_v1_preview,
                    async_projects_import_v1, async_projects_add, async_projects_manage,
                    async_projects_token,
                    async_projects_retention, async_projects_preselect,
                    async_settings_get, async_settings_save, async_settings_ack_cpu_warning,
                    async_batch_preview, async_projects_connection_check,
                    async_projects_source_preview,
                    async_source_job_start, async_source_job_status,
                    async_source_job_history,
                    async_deployment_logs, async_deployment_logs_download,
                    async_deployment_logs_export, async_deployment_logs_clear,
                    async_git_read_configure, async_git_read_clear,
                    async_archive_repository_set, async_archive_repository_clear,
                    async_archive_repository_configure,
                    async_archive_repository_check,
                    async_download_json):
        websocket_api.async_register_command(hass, handler)
    state["commands_registered"] = True
