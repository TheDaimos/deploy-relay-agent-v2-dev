"""Admin-only WebSocket API for the Deploy Relay sidebar app."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from types import MappingProxyType
from typing import Any

import probatio

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BACKUP_RETENTION,
    CONF_DIAGNOSTIC_GIT_TOKEN,
    CONF_GITHUB_TOKEN,
    CONF_MANIFEST_PATH,
    CONF_REPOSITORY,
    CONF_SELECTED_SOURCE_COMMIT,
    CONF_SELECTED_SOURCE_KIND,
    CONF_SELECTED_SOURCE_REF,
    DEFAULT_BACKUP_RETENTION,
    DEFAULT_MANIFEST_PATH,
    DIAGNOSTIC_GIT_ROOT,
    MAX_BACKUP_RETENTION,
    MIN_BACKUP_RETENTION,
    DOMAIN,
    DeploymentMode,
    SUBENTRY_TYPE_PROJECT,
    VERSION,
)
from .deployment import (
    DeploymentError,
    RecoveryRequiredError,
    async_execute_deployment,
    list_project_backups,
    prune_project_backups,
    restore_project_backup,
)
from .deployment_channel import (
    DeploymentChannelError,
    async_resolve_recommended_deployment,
    unavailable_recommendation,
)
from .diagnostic_store import DiagnosticStore
from .github_export import DiagnosticGitExportClient
from .github_client import (
    GitHubAccessError,
    GitHubApiError,
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubClient,
)
from .lifecycle_policy import assess_lifecycle
from .preview import PreviewError, build_preview
from .project_import import ProjectImportError, async_probe_project
from .source_discovery import (
    SourceDiscoveryError,
    SourceKind,
    SourceManifestNotFound,
    async_discover_sources,
    async_load_frozen_manifest,
    async_resolve_source,
)
from .source_inventory import SourceInventoryError, async_build_source_inventory
from .version_guard import assess_version_guard


_MAX_SOURCE_FILE_DIAGNOSTICS = 100
_MAX_PREVIEW_FILE_DIAGNOSTICS = 250
_MAX_REMOVAL_PATH_DIAGNOSTICS = 100


def _build_preview_assessment(
    manifest,
    inventory,
    config_root: Path,
):
    """Run local directory walking, checksums and version reads off the event loop."""
    result = build_preview(
        manifest,
        inventory,
        config_root=config_root,
    )
    counts = {
        "add": 0,
        "change": 0,
        "remove": 0,
        "unchanged": 0,
    }
    for item in result.files:
        counts[item.operation.value] += 1
    version_guard = assess_version_guard(
        manifest,
        inventory,
        result,
        config_root=config_root,
    )
    lifecycle = assess_lifecycle(manifest, result)
    return result, counts, version_guard, lifecycle


def _entry(hass: HomeAssistant):
    """Return the single Deploy Relay config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise LookupError("Deploy Relay is not configured")
    return entries[0]


def _project(entry, subentry_id: str):
    """Return one project subentry."""
    subentry = entry.subentries.get(subentry_id)
    if subentry is None or subentry.subentry_type != SUBENTRY_TYPE_PROJECT:
        raise LookupError("Project not found")
    return subentry


def _diagnostics(entry) -> DiagnosticStore:
    """Return diagnostics and refresh the secret-redaction set."""
    store = entry.runtime_data.diagnostics
    if store is None:
        raise RuntimeError("Deploy Relay diagnostics are not initialized")

    for subentry in entry.subentries.values():
        for key in (CONF_GITHUB_TOKEN, CONF_DIAGNOSTIC_GIT_TOKEN):
            token = subentry.data.get(key)
            if token:
                store.register_secret(str(token))

    return store


def _project_id(subentry) -> str | None:
    value = subentry.data.get("project_id")
    return str(value) if value else None


def _backup_retention(subentry) -> int:
    """Return one project's bounded backup retention setting."""

    value = subentry.data.get(CONF_BACKUP_RETENTION, DEFAULT_BACKUP_RETENTION)
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not MIN_BACKUP_RETENTION <= value <= MAX_BACKUP_RETENTION
    ):
        return DEFAULT_BACKUP_RETENTION
    return value


def _require_development(entry) -> None:
    """Fail closed unless deployment writes were explicitly unlocked this runtime."""
    if entry.runtime_data.deployment_mode is not DeploymentMode.DEVELOPMENT:
        raise DeploymentError(
            "Deployment mode is LOCKED. Enable DEVELOPMENT explicitly first."
        )


def _restart_pending_projects(hass: HomeAssistant) -> set[str]:
    """Return runtime-only projects that require a full HA restart.

    The set intentionally lives only in hass.data. A real Home Assistant restart
    clears it automatically, which is exactly the lifecycle boundary represented
    by this state.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    pending = domain_data.get("restart_pending_projects")
    if not isinstance(pending, set):
        pending = set()
        domain_data["restart_pending_projects"] = pending
    return pending


def _safe_project(subentry, *, restart_pending: bool = False) -> dict[str, Any]:
    """Serialize one project without secret material."""
    data = subentry.data
    return {
        "subentry_id": subentry.subentry_id,
        "title": subentry.title,
        "project_id": data.get("project_id"),
        "project_name": data.get("project_name"),
        "repository": data.get(CONF_REPOSITORY),
        "manifest_path": data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH),
        "status": data.get("status"),
        "private": data.get("private"),
        "archived": data.get("archived"),
        "default_branch": data.get("default_branch"),
        "token_configured": bool(data.get(CONF_GITHUB_TOKEN)),
        "git_export_configured": bool(data.get(CONF_DIAGNOSTIC_GIT_TOKEN)),
        "git_export_root": DIAGNOSTIC_GIT_ROOT,
        "git_export_branch": data.get("default_branch"),
        "selected_source_kind": data.get(CONF_SELECTED_SOURCE_KIND),
        "selected_source_ref": data.get(CONF_SELECTED_SOURCE_REF),
        "selected_source_commit": data.get(CONF_SELECTED_SOURCE_COMMIT),
        "backup_retention": _backup_retention(subentry),
        "restart_pending": restart_pending,
    }


def _safe_projects(
    entry,
    *,
    restart_pending_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    pending_ids = restart_pending_ids or set()
    projects = [
        _safe_project(
            subentry,
            restart_pending=subentry.subentry_id in pending_ids,
        )
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_PROJECT
    ]
    projects.sort(key=lambda item: (item["title"] or "").casefold())
    return projects


def _send_exception(
    connection: websocket_api.ActiveConnection,
    msg_id: int,
    err: Exception,
) -> None:
    """Map backend errors to stable, non-secret WebSocket errors."""
    if isinstance(err, GitHubAuthenticationError):
        connection.send_error(msg_id, "invalid_auth", "GitHub authentication failed")
    elif isinstance(err, GitHubRateLimitError):
        connection.send_error(msg_id, "rate_limited", "GitHub API rate limit reached")
    elif isinstance(err, GitHubAccessError):
        connection.send_error(msg_id, "access_denied", "GitHub access denied")
    elif isinstance(err, GitHubNotFoundError):
        connection.send_error(msg_id, "not_found", "GitHub resource not found")
    elif isinstance(err, SourceManifestNotFound):
        connection.send_error(msg_id, "manifest_missing", "Deployment manifest not found")
    elif isinstance(err, RecoveryRequiredError):
        connection.send_error(msg_id, "recovery_required", str(err))
    elif isinstance(err, DeploymentError):
        connection.send_error(msg_id, "deployment_failed", str(err))
    elif isinstance(
        err,
        (
            ProjectImportError,
            SourceDiscoveryError,
            SourceInventoryError,
            PreviewError,
            DeploymentChannelError,
        ),
    ):
        connection.send_error(msg_id, "validation_failed", str(err))
    elif isinstance(err, GitHubApiError):
        connection.send_error(msg_id, "github_error", str(err))
    elif isinstance(err, LookupError):
        connection.send_error(msg_id, "not_found", str(err))
    else:
        connection.send_error(msg_id, "unknown", "Unexpected Deploy Relay error")


@websocket_api.websocket_command(
    {probatio.Required("type"): "deploy_relay/panel/state"}
)
@websocket_api.require_admin
def websocket_panel_state(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return secret-free panel state."""
    try:
        entry = _entry(hass)
    except LookupError as err:
        _send_exception(connection, msg["id"], err)
        return

    runtime = entry.runtime_data
    diagnostics = runtime.diagnostics
    connection.send_result(
        msg["id"],
        {
            "version": VERSION,
            "deployment_mode": runtime.deployment_mode.value,
            "deployment_writes_enabled": (
                runtime.deployment_mode is DeploymentMode.DEVELOPMENT
            ),
            "diagnostics": diagnostics.stats() if diagnostics else None,
            "projects": _safe_projects(
                entry,
                restart_pending_ids=_restart_pending_projects(hass),
            ),
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/set_mode",
        probatio.Required("mode"): probatio.In(
            [mode.value for mode in DeploymentMode]
        ),
        probatio.Optional("confirm", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_set_mode(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Explicitly change the runtime-only deployment lock."""
    try:
        entry = _entry(hass)
        runtime = entry.runtime_data
        if runtime.deployment_lock.locked():
            raise DeploymentError("A deployment transaction is currently active")

        requested = DeploymentMode(str(msg["mode"]))
        if (
            requested is DeploymentMode.DEVELOPMENT
            and not bool(msg.get("confirm", False))
        ):
            raise DeploymentError(
                "Explicit confirmation is required to enable DEVELOPMENT"
            )

        previous = runtime.deployment_mode
        runtime.deployment_mode = requested
        diagnostics = _diagnostics(entry)
        await diagnostics.async_event(
            "WARNING" if requested is DeploymentMode.DEVELOPMENT else "INFO",
            "security",
            "Deployment mode changed",
            operation="deployment_mode",
            phase="set_mode",
            details={
                "previous": previous.value,
                "current": requested.value,
                "runtime_only": True,
            },
        )
    except Exception as err:  # noqa: BLE001
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "deployment_mode": entry.runtime_data.deployment_mode.value,
            "deployment_writes_enabled": (
                entry.runtime_data.deployment_mode is DeploymentMode.DEVELOPMENT
            ),
            "runtime_only": True,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/import_project",
        probatio.Required("repository"): str,
        probatio.Optional("manifest_path", default=DEFAULT_MANIFEST_PATH): str,
        probatio.Optional("github_token", default=""): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_import_project(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Import one GitHub project without exposing its credential."""
    entry = None
    run = None
    phase = "prepare"
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        repository = str(msg["repository"])
        manifest_path = str(msg.get("manifest_path", DEFAULT_MANIFEST_PATH))
        token = str(msg.get("github_token", "")).strip() or None
        diagnostics.register_secret(token)

        run = await diagnostics.async_start_run(
            "project_import",
            repository=repository,
            context={
                "manifest_path": manifest_path,
                "token_configured": bool(token),
            },
        )

        phase = "repository_probe"
        run.start_phase(phase)
        result = await async_probe_project(
            async_get_clientsession(hass),
            repository,
            token=token,
            manifest_path=manifest_path,
        )
        await run.info(
            "github",
            "Repository and default manifest probed",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "normalized_repository": result.repository,
                "default_branch": result.default_branch,
                "private": result.private,
                "archived": result.archived,
                "status": result.status.value,
                "manifest_found": result.manifest is not None,
                "project_id": result.project_id,
                "project_name": result.project_name,
            },
        )

        phase = "duplicate_check"
        repository_unique_id = result.repository.casefold()
        for existing in entry.subentries.values():
            if (
                existing.subentry_type == SUBENTRY_TYPE_PROJECT
                and existing.unique_id == repository_unique_id
            ):
                raise ProjectImportError("Repository is already imported")
        await run.debug(
            "project",
            "Repository duplicate check passed",
            phase=phase,
            details={"repository_unique_id": repository_unique_id},
        )

        phase = "persist"
        data = result.as_subentry_data()
        if token:
            data[CONF_GITHUB_TOKEN] = token

        subentry = ConfigSubentry(
            data=MappingProxyType(data),
            subentry_type=SUBENTRY_TYPE_PROJECT,
            title=result.project_name,
            unique_id=repository_unique_id,
        )
        if not hass.config_entries.async_add_subentry(entry, subentry):
            raise ProjectImportError("Could not add project subentry")

        run.project_id = result.project_id
        await run.info(
            "home_assistant",
            "Project subentry persisted",
            phase=phase,
            details={
                "subentry_id": subentry.subentry_id,
                "project_id": result.project_id,
                "status": result.status.value,
            },
        )
        await run.success(
            summary={
                "project_id": result.project_id,
                "repository": result.repository,
                "status": result.status.value,
            }
        )
    except Exception as err:  # noqa: BLE001
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(msg["id"], _safe_project(subentry))


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/remove_project",
        probatio.Required("subentry_id"): str,
        probatio.Required("expected_repository"): str,
        probatio.Required("confirm"): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_remove_project(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove one configured project, never its deployed target files."""
    run = None
    phase = "prepare"
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        subentry = _project(entry, msg["subentry_id"])
        repository = str(subentry.data.get(CONF_REPOSITORY, ""))
        project_id = _project_id(subentry)

        if msg.get("confirm") is not True:
            raise ProjectImportError("Project removal confirmation is required")
        if str(msg.get("expected_repository", "")).casefold() != repository.casefold():
            raise ProjectImportError("Project removal identity confirmation does not match")

        run = await diagnostics.async_start_run(
            "project_remove",
            project_id=project_id,
            repository=repository,
            context={"subentry_id": subentry.subentry_id},
        )
        phase = "remove_subentry"
        run.start_phase(phase)

        removed = hass.config_entries.async_remove_subentry(
            entry,
            subentry.subentry_id,
        )
        if not removed:
            raise ProjectImportError("Could not remove project subentry")

        _restart_pending_projects(hass).discard(subentry.subentry_id)
        await run.info(
            "home_assistant",
            "Project subentry removed",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "subentry_id": subentry.subentry_id,
                "project_id": project_id,
                "repository": repository,
                "deployed_files_removed": False,
            },
        )
        await run.success(
            summary={
                "project_id": project_id,
                "repository": repository,
                "removed": True,
                "deployed_files_removed": False,
            }
        )
    except Exception as err:  # noqa: BLE001
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "removed": True,
            "subentry_id": msg["subentry_id"],
            "repository": repository,
            "deployed_files_removed": False,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/sources",
        probatio.Required("subentry_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_sources(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return branch/tag/release choices for one project."""
    run = None
    phase = "prepare"
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        subentry = _project(entry, msg["subentry_id"])
        data = subentry.data
        repository = str(data[CONF_REPOSITORY])

        run = await diagnostics.async_start_run(
            "source_discovery",
            project_id=_project_id(subentry),
            repository=repository,
            context={"subentry_id": subentry.subentry_id},
        )

        session = async_get_clientsession(hass)
        token = (
            str(data[CONF_GITHUB_TOKEN])
            if data.get(CONF_GITHUB_TOKEN)
            else None
        )

        phase = "github_source_listing"
        run.start_phase(phase)
        result = await async_discover_sources(
            session,
            repository,
            token=token,
        )

        counts = {
            kind.value: sum(item.kind is kind for item in result.candidates)
            for kind in SourceKind
        }
        await run.info(
            "github",
            "Source candidates discovered",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "default_branch": result.default_branch,
                "candidate_count": len(result.candidates),
                "counts": counts,
                "truncated": result.truncated,
            },
        )
        for item in result.candidates:
            await run.debug(
                "github",
                "Source candidate",
                phase="candidate",
                details={
                    "kind": item.kind.value,
                    "ref": item.ref,
                    "commit_sha": item.commit_sha,
                    "label": item.label,
                    "prerelease": item.prerelease,
                },
            )

        phase = "deployment_channel"
        expected_project_id = (
            str(data["project_id"])
            if data.get("project_id")
            else None
        )
        try:
            recommended = await async_resolve_recommended_deployment(
                session,
                repository,
                expected_project_id=expected_project_id or "",
                token=token,
                manifest_path=str(
                    data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
                ),
            )
            recommendation = recommended.as_dict(
                selected_kind=(
                    str(data[CONF_SELECTED_SOURCE_KIND])
                    if data.get(CONF_SELECTED_SOURCE_KIND)
                    else None
                ),
                selected_ref=(
                    str(data[CONF_SELECTED_SOURCE_REF])
                    if data.get(CONF_SELECTED_SOURCE_REF)
                    else None
                ),
                selected_commit=(
                    str(data[CONF_SELECTED_SOURCE_COMMIT])
                    if data.get(CONF_SELECTED_SOURCE_COMMIT)
                    else None
                ),
            )
            await run.info(
                "deployment_channel",
                "Recommended deployment resolved",
                phase=phase,
                details=recommendation,
            )
        except Exception as recommendation_err:  # noqa: BLE001
            recommendation = unavailable_recommendation(recommendation_err)
            await run.warning(
                "deployment_channel",
                "Recommended deployment unavailable",
                phase=phase,
                details=recommendation,
            )

        await run.success(
            summary={
                "candidate_count": len(result.candidates),
                "truncated": result.truncated,
            }
        )
    except Exception as err:  # noqa: BLE001
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "default_branch": result.default_branch,
            "truncated": result.truncated,
            "recommended": recommendation,
            "candidates": [
                {
                    "kind": item.kind.value,
                    "ref": item.ref,
                    "commit_sha": item.commit_sha,
                    "label": item.label,
                    "prerelease": item.prerelease,
                }
                for item in result.candidates
            ],
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/select_source",
        probatio.Required("subentry_id"): str,
        probatio.Required("kind"): probatio.In(
            [kind.value for kind in SourceKind]
        ),
        probatio.Required("ref"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_select_source(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Resolve and persist one source selection."""
    run = None
    phase = "prepare"
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        subentry = _project(entry, msg["subentry_id"])
        data = subentry.data
        repository = str(data[CONF_REPOSITORY])
        kind = str(msg["kind"])
        ref = str(msg["ref"])

        run = await diagnostics.async_start_run(
            "source_selection",
            project_id=_project_id(subentry),
            repository=repository,
            context={"kind": kind, "ref": ref},
        )

        expected_project_id = (
            str(data["project_id"])
            if data.get("status") == "ready" and data.get("project_id")
            else None
        )

        phase = "resolve_commit"
        run.start_phase(phase)
        resolved = await async_resolve_source(
            async_get_clientsession(hass),
            repository,
            kind=kind,
            ref=ref,
            token=(
                str(data[CONF_GITHUB_TOKEN])
                if data.get(CONF_GITHUB_TOKEN)
                else None
            ),
            manifest_path=str(
                data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
            ),
            expected_project_id=expected_project_id,
        )
        await run.info(
            "github",
            "Source resolved to canonical commit",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "kind": resolved.kind.value,
                "requested_ref": resolved.requested_ref,
                "commit_sha": resolved.commit_sha,
                "manifest_project_id": resolved.manifest.project_id,
                "manifest_project_name": resolved.manifest.project_name,
                "source_mode": resolved.manifest.source_mode,
                "group_count": len(resolved.manifest.groups),
            },
        )

        phase = "persist"
        updated = dict(data)
        updated.update(
            {
                "project_id": resolved.manifest.project_id,
                "project_name": resolved.manifest.project_name,
                "status": "ready",
                CONF_SELECTED_SOURCE_KIND: resolved.kind.value,
                CONF_SELECTED_SOURCE_REF: resolved.requested_ref,
                CONF_SELECTED_SOURCE_COMMIT: resolved.commit_sha,
            }
        )
        hass.config_entries.async_update_subentry(
            entry,
            subentry,
            title=resolved.manifest.project_name,
            data=updated,
        )
        await run.info(
            "home_assistant",
            "Frozen source identity persisted",
            phase=phase,
            details={
                "subentry_id": subentry.subentry_id,
                "kind": resolved.kind.value,
                "ref": resolved.requested_ref,
                "commit_sha": resolved.commit_sha,
            },
        )
        await run.success(
            summary={
                "kind": resolved.kind.value,
                "ref": resolved.requested_ref,
                "commit_sha": resolved.commit_sha,
            }
        )
    except Exception as err:  # noqa: BLE001
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "kind": resolved.kind.value,
            "ref": resolved.requested_ref,
            "commit_sha": resolved.commit_sha,
            "project_name": resolved.manifest.project_name,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/preview",
        probatio.Required("subentry_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_preview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Build and return a fresh read-only preview with full diagnostics."""
    run = None
    phase = "prepare"
    resource_lock_acquired = False
    try:
        entry = _entry(hass)
        await entry.runtime_data.resource_lock.acquire()
        resource_lock_acquired = True
        diagnostics = _diagnostics(entry)
        subentry = _project(entry, msg["subentry_id"])
        data = subentry.data

        commit = data.get(CONF_SELECTED_SOURCE_COMMIT)
        selected_ref = data.get(CONF_SELECTED_SOURCE_REF)
        selected_kind = data.get(CONF_SELECTED_SOURCE_KIND)
        if not commit or not selected_ref:
            raise SourceDiscoveryError("Select a source/version first")

        repository = str(data[CONF_REPOSITORY])
        run = await diagnostics.async_start_run(
            "preview",
            project_id=_project_id(subentry),
            repository=repository,
            context={
                "source_kind": selected_kind,
                "source_ref": selected_ref,
                "source_commit": commit,
                "manifest_path": data.get(
                    CONF_MANIFEST_PATH,
                    DEFAULT_MANIFEST_PATH,
                ),
            },
        )

        token = (
            str(data[CONF_GITHUB_TOKEN])
            if data.get(CONF_GITHUB_TOKEN)
            else None
        )
        project_id = (
            str(data["project_id"])
            if data.get("project_id")
            else None
        )
        session = async_get_clientsession(hass)

        phase = "manifest"
        run.start_phase(phase)
        manifest = await async_load_frozen_manifest(
            session,
            repository,
            commit_sha=str(commit),
            token=token,
            manifest_path=str(
                data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
            ),
            expected_project_id=project_id,
        )
        await run.info(
            "manifest",
            "Frozen deployment manifest loaded and validated",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "project_id": manifest.project_id,
                "project_name": manifest.project_name,
                "repository": manifest.repository,
                "source_mode": manifest.source_mode,
                "lifecycle": manifest.after_install.value,
                "max_files": manifest.max_files,
                "max_uncompressed_bytes": manifest.max_uncompressed_bytes,
                "groups": [
                    {
                        "id": group.id,
                        "source": group.source,
                        "target": group.target,
                        "mode": group.mode,
                        "files": list(group.files),
                    }
                    for group in manifest.groups
                ],
            },
        )

        phase = "source_inventory"
        run.start_phase(phase)
        inventory = await async_build_source_inventory(
            session,
            manifest,
            source_ref=str(selected_ref),
            source_commit=str(commit),
            token=token,
        )
        await run.info(
            "source_inventory",
            "Frozen source inventory completed",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "total_files": inventory.total_files,
                "total_bytes": inventory.total_bytes,
                "group_count": len(inventory.groups),
            },
        )
        source_diagnostics_emitted = 0
        for group in inventory.groups:
            await run.debug(
                "source_inventory",
                "Source group inventory",
                phase="source_group",
                details={
                    "group_id": group.group_id,
                    "file_count": len(group.files),
                },
            )
            for file in group.files:
                if source_diagnostics_emitted >= _MAX_SOURCE_FILE_DIAGNOSTICS:
                    continue
                await run.debug(
                    "source_inventory",
                    "Managed source file sample",
                    phase="source_file",
                    details={
                        "group_id": group.group_id,
                        "relative_path": file.relative_path,
                        "source_path": file.source_path,
                        "size": file.size,
                        "sha256": file.sha256,
                    },
                )
                source_diagnostics_emitted += 1
        if inventory.total_files > source_diagnostics_emitted:
            await run.info(
                "source_inventory",
                "Per-file source diagnostics capped for resource safety",
                phase="source_summary",
                details={
                    "emitted": source_diagnostics_emitted,
                    "omitted": inventory.total_files - source_diagnostics_emitted,
                    "total_files": inventory.total_files,
                },
            )

        phase = "target_compare"
        run.start_phase(phase)
        result, counts, version_guard, lifecycle = await hass.async_add_executor_job(
            partial(
                _build_preview_assessment,
                manifest,
                inventory,
                Path(hass.config.config_dir),
            )
        )

        phase = "deployment_channel"
        try:
            recommended = await async_resolve_recommended_deployment(
                session,
                repository,
                expected_project_id=project_id or manifest.project_id,
                token=token,
                manifest_path=str(
                    data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
                ),
            )
            recommendation = recommended.as_dict(
                selected_kind=str(selected_kind) if selected_kind else None,
                selected_ref=str(selected_ref) if selected_ref else None,
                selected_commit=str(commit) if commit else None,
            )
            await run.info(
                "deployment_channel",
                "Preview source checked against recommended deployment",
                phase=phase,
                details=recommendation,
            )
        except Exception as recommendation_err:  # noqa: BLE001
            recommendation = unavailable_recommendation(recommendation_err)
            await run.warning(
                "deployment_channel",
                "Preview could not verify recommended deployment",
                phase=phase,
                details=recommendation,
            )

        await run.info(
            "version_guard",
            "Selected Git build compared with local managed target",
            phase="version_compare",
            details=version_guard.as_dict(),
        )
        if version_guard.warning:
            await run.warning(
                "version_guard",
                "Version/regression warning detected",
                phase="version_compare",
                details=version_guard.as_dict(),
            )
        await run.info(
            "preview",
            "Target comparison completed",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "counts": counts,
                "file_count": len(result.files),
            },
        )

        preview_diagnostics_emitted = 0
        for include_unchanged in (False, True):
            for item in result.files:
                if preview_diagnostics_emitted >= _MAX_PREVIEW_FILE_DIAGNOSTICS:
                    break
                if (item.operation.value == "unchanged") != include_unchanged:
                    continue
                await run.debug(
                    "preview",
                    "Preview file classification sample",
                    phase="file_compare",
                    details={
                        "group_id": item.group_id,
                        "operation": item.operation.value,
                        "target_path": item.target_path,
                        "source_path": item.source_path,
                        "source_sha256": item.source_sha256,
                        "target_sha256": item.target_sha256,
                        "source_size": item.source_size,
                        "target_size": item.target_size,
                    },
                )
                preview_diagnostics_emitted += 1

        if len(result.files) > preview_diagnostics_emitted:
            await run.info(
                "preview",
                "Per-file preview diagnostics capped for resource safety",
                phase="file_compare_summary",
                details={
                    "emitted": preview_diagnostics_emitted,
                    "omitted": len(result.files) - preview_diagnostics_emitted,
                    "total_files": len(result.files),
                    "counts": counts,
                },
            )

        if counts["remove"]:
            removal_paths = [
                item.target_path
                for item in result.files
                if item.operation.value == "remove"
            ][:_MAX_REMOVAL_PATH_DIAGNOSTICS]
            await run.warning(
                "preview",
                "Preview contains removal candidates",
                phase="summary",
                details={
                    "remove_count": counts["remove"],
                    "paths": removal_paths,
                    "paths_omitted": max(0, counts["remove"] - len(removal_paths)),
                },
            )

        await run.info(
            "lifecycle",
            "Effective post-install lifecycle classified",
            phase="summary",
            details=lifecycle.as_dict(),
        )
        await run.success(summary={"counts": counts, "lifecycle": lifecycle.as_dict()})
        source_files_hashed = inventory.total_files
        del inventory
    except Exception as err:  # noqa: BLE001
        if resource_lock_acquired:
            entry.runtime_data.resource_lock.release()
            resource_lock_acquired = False
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    if resource_lock_acquired:
        entry.runtime_data.resource_lock.release()
        resource_lock_acquired = False

    connection.send_result(
        msg["id"],
        {
            "run_id": run.run_id if run else None,
            "project_id": result.project_id,
            "repository": result.repository,
            "source_ref": result.source_ref,
            "source_commit": result.source_commit,
            "counts": counts,
            "integrity": {
                "algorithm": "sha256",
                "checksums_complete": True,
                "source_files_hashed": source_files_hashed,
                "target_files_hashed": sum(
                    item.target_sha256 is not None for item in result.files
                ),
            },
            "version_guard": version_guard.as_dict(),
            "lifecycle": lifecycle.as_dict(),
            "recommendation": recommendation,
            "files": [
                {
                    "group_id": item.group_id,
                    "operation": item.operation.value,
                    "target_path": item.target_path,
                    "source_path": item.source_path,
                    "source_sha256": item.source_sha256,
                    "target_sha256": item.target_sha256,
                    "source_size": item.source_size,
                    "target_size": item.target_size,
                }
                for item in result.files
            ],
        },
    )




@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/install",
        probatio.Required("subentry_id"): str,
        probatio.Optional("confirm", default=False): bool,
        probatio.Optional("allow_regression", default=False): bool,
        probatio.Optional("allow_unrecommended", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_install(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a fresh staged, backed-up deployment bound to the frozen commit."""
    entry = None
    run = None
    phase = "prepare"
    resource_lock_acquired = False
    try:
        entry = _entry(hass)
        _require_development(entry)
        if not bool(msg.get("confirm", False)):
            raise DeploymentError("Explicit deployment confirmation is required")

        runtime = entry.runtime_data
        async with runtime.deployment_lock:
            _require_development(entry)
            await runtime.resource_lock.acquire()
            resource_lock_acquired = True
            diagnostics = _diagnostics(entry)
            subentry = _project(entry, msg["subentry_id"])
            data = subentry.data

            commit = data.get(CONF_SELECTED_SOURCE_COMMIT)
            selected_ref = data.get(CONF_SELECTED_SOURCE_REF)
            selected_kind = data.get(CONF_SELECTED_SOURCE_KIND)
            if not commit or not selected_ref or not selected_kind:
                raise SourceDiscoveryError("Select a source/version first")

            repository = str(data[CONF_REPOSITORY])
            token = (
                str(data[CONF_GITHUB_TOKEN])
                if data.get(CONF_GITHUB_TOKEN)
                else None
            )
            project_id = (
                str(data["project_id"])
                if data.get("project_id")
                else None
            )
            run = await diagnostics.async_start_run(
                "deployment_install",
                project_id=project_id,
                repository=repository,
                context={
                    "source_kind": selected_kind,
                    "source_ref": selected_ref,
                    "source_commit": commit,
                    "deployment_mode": runtime.deployment_mode.value,
                },
            )
            session = async_get_clientsession(hass)

            phase = "manifest"
            run.start_phase(phase)
            manifest = await async_load_frozen_manifest(
                session,
                repository,
                commit_sha=str(commit),
                token=token,
                manifest_path=str(
                    data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
                ),
                expected_project_id=project_id,
            )
            await run.info(
                "manifest",
                "Frozen deployment manifest loaded for install",
                phase=phase,
                duration_ms=run.phase_duration_ms(phase),
                details={
                    "project_id": manifest.project_id,
                    "source_mode": manifest.source_mode,
                    "lifecycle": manifest.after_install.value,
                    "group_count": len(manifest.groups),
                },
            )

            phase = "deployment_channel"
            recommended = await async_resolve_recommended_deployment(
                session,
                repository,
                expected_project_id=project_id or manifest.project_id,
                token=token,
                manifest_path=str(
                    data.get(CONF_MANIFEST_PATH, DEFAULT_MANIFEST_PATH)
                ),
            )
            recommendation = recommended.as_dict(
                selected_kind=str(selected_kind) if selected_kind else None,
                selected_ref=str(selected_ref) if selected_ref else None,
                selected_commit=str(commit) if commit else None,
            )
            allow_unrecommended = bool(msg.get("allow_unrecommended", False))
            if (
                (not recommendation["safe_selected"])
                and not allow_unrecommended
            ):
                if not recommendation["explicit_policy"]:
                    raise DeploymentError(
                        "Recommended deployment guard blocked install: project has "
                        "no explicit deploy-relay-channel.json policy. Explicit "
                        "non-recommended confirmation is required."
                    )
                raise DeploymentError(
                    "Recommended deployment guard blocked install: selected source "
                    f"{selected_kind}:{selected_ref}@{str(commit)[:12]} is not the "
                    "current recommended deployment "
                    f"{recommendation['kind']}:{recommendation['ref']}@"
                    f"{recommendation['commit_sha'][:12]}."
                )
            await run.info(
                "deployment_channel",
                "Pre-install recommended deployment verified",
                phase=phase,
                details={
                    **recommendation,
                    "unrecommended_override": allow_unrecommended,
                },
            )
            if not recommendation["safe_selected"]:
                await run.warning(
                    "deployment_channel",
                    "Installing a non-recommended deployment by explicit override",
                    phase=phase,
                    details={
                        **recommendation,
                        "unrecommended_override": True,
                    },
                )

            phase = "source_inventory"
            run.start_phase(phase)
            inventory = await async_build_source_inventory(
                session,
                manifest,
                source_ref=str(selected_ref),
                source_commit=str(commit),
                token=token,
            )
            await run.info(
                "source_inventory",
                "Frozen source inventory rebuilt for install",
                phase=phase,
                duration_ms=run.phase_duration_ms(phase),
                details={
                    "total_files": inventory.total_files,
                    "total_bytes": inventory.total_bytes,
                },
            )

            phase = "target_compare"
            run.start_phase(phase)
            preview, counts, version_guard, _lifecycle = (
                await hass.async_add_executor_job(
                    partial(
                        _build_preview_assessment,
                        manifest,
                        inventory,
                        Path(hass.config.config_dir),
                    )
                )
            )
            await run.info(
                "version_guard",
                "Fresh pre-install Git/local version comparison completed",
                phase="version_compare",
                details=version_guard.as_dict(),
            )
            if version_guard.regression and not bool(msg.get("allow_regression", False)):
                raise DeploymentError(
                    "Regression guard blocked install: selected Git version "
                    f"{version_guard.source_version} is older than local version "
                    f"{version_guard.local_version}. Explicit regression confirmation is required."
                )
            if version_guard.warning:
                await run.warning(
                    "version_guard",
                    "Pre-install version/regression warning",
                    phase="version_compare",
                    details={
                        **version_guard.as_dict(),
                        "regression_override": bool(msg.get("allow_regression", False)),
                    },
                )
            await run.info(
                "preview",
                "Fresh pre-install target comparison completed",
                phase=phase,
                duration_ms=run.phase_duration_ms(phase),
                details={"counts": counts},
            )

            async def deployment_progress(
                progress_phase: str,
                details: dict[str, Any],
            ) -> None:
                await run.info(
                    "deployment",
                    f"Deployment phase: {progress_phase}",
                    phase=progress_phase,
                    details=details,
                )

            phase = "deployment"
            result = await async_execute_deployment(
                session,
                manifest,
                inventory,
                preview,
                token=token,
                config_root=Path(hass.config.config_dir),
                progress=deployment_progress,
                backup_context={
                    "previous_version": version_guard.local_version,
                    "target_version": version_guard.source_version,
                    "version_marker": version_guard.marker,
                },
                blocking_executor=hass.async_add_executor_job,
            )

            try:
                protected = (
                    {Path(result.backup_path).name}
                    if result.backup_path
                    else set()
                )
                removed_backups = await hass.async_add_executor_job(
                    partial(
                        prune_project_backups,
                        Path(hass.config.config_dir),
                        manifest.project_id,
                        _backup_retention(subentry),
                        protected_ids=protected,
                    )
                )
                if removed_backups:
                    await run.info(
                        "backup_retention",
                        "Older project backups pruned after successful deployment",
                        phase="backup_retention",
                        details={
                            "retention": _backup_retention(subentry),
                            "removed": removed_backups,
                        },
                    )
            except Exception as retention_err:  # noqa: BLE001
                await run.warning(
                    "backup_retention",
                    "Backup retention cleanup failed; deployment remains successful",
                    phase="backup_retention",
                    details={"error": str(retention_err)},
                )

            if result.restart_required:
                _restart_pending_projects(hass).add(subentry.subentry_id)

            await run.success(
                summary={
                    "transaction_id": result.transaction_id,
                    "state": result.state.value,
                    "changed_files": result.changed_files,
                    "backup_path": result.backup_path,
                    "lifecycle": result.lifecycle,
                    "restart_required": result.restart_required,
                    "counts": counts,
                    "version_guard": version_guard.as_dict(),
                    "recommendation": recommendation,
                }
            )
            del preview, inventory
            if resource_lock_acquired:
                runtime.resource_lock.release()
                resource_lock_acquired = False
    except Exception as err:  # noqa: BLE001
        if resource_lock_acquired and entry is not None:
            entry.runtime_data.resource_lock.release()
            resource_lock_acquired = False
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "transaction_id": result.transaction_id,
            "state": result.state.value,
            "source_ref": selected_ref,
            "source_commit": commit,
            "counts": counts,
            "version_guard": version_guard.as_dict(),
            "recommendation": recommendation,
            "changed_files": result.changed_files,
            "backup_path": result.backup_path,
            "journal_path": result.journal_path,
            "lifecycle": result.lifecycle,
            "restart_required": result.restart_required,
        },
    )



@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/backups",
        probatio.Required("subentry_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_backups(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """List verified DRA-owned backups for one project."""

    try:
        entry = _entry(hass)
        subentry = _project(entry, msg["subentry_id"])
        project_id = _project_id(subentry)
        if not project_id:
            raise LookupError("Project has no trusted project id")
        async with entry.runtime_data.resource_lock:
            backups = await hass.async_add_executor_job(
                partial(
                    list_project_backups,
                    Path(hass.config.config_dir),
                    project_id,
                )
            )
    except Exception as err:  # noqa: BLE001
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "project_id": project_id,
            "retention": _backup_retention(subentry),
            "minimum": MIN_BACKUP_RETENTION,
            "maximum": MAX_BACKUP_RETENTION,
            "backups": backups,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/set_backup_retention",
        probatio.Required("subentry_id"): str,
        probatio.Required("retention"): int,
        probatio.Optional("confirm", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_set_backup_retention(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist one project's retention count and prune only verified old backups."""

    try:
        if not bool(msg.get("confirm", False)):
            raise DeploymentError("Explicit backup retention confirmation is required")
        retention = int(msg["retention"])
        if not MIN_BACKUP_RETENTION <= retention <= MAX_BACKUP_RETENTION:
            raise DeploymentError(
                f"Backup retention must be between {MIN_BACKUP_RETENTION} and "
                f"{MAX_BACKUP_RETENTION}"
            )

        entry = _entry(hass)
        subentry = _project(entry, msg["subentry_id"])
        project_id = _project_id(subentry)
        if not project_id:
            raise LookupError("Project has no trusted project id")

        data = dict(subentry.data)
        data[CONF_BACKUP_RETENTION] = retention
        hass.config_entries.async_update_subentry(
            entry,
            subentry,
            data=data,
        )

        cleanup_warning = None
        async with entry.runtime_data.deployment_lock:
            async with entry.runtime_data.resource_lock:
                try:
                    removed = await hass.async_add_executor_job(
                        partial(
                            prune_project_backups,
                            Path(hass.config.config_dir),
                            project_id,
                            retention,
                        )
                    )
                except Exception as cleanup_err:  # noqa: BLE001
                    removed = []
                    cleanup_warning = str(cleanup_err)
                backups = await hass.async_add_executor_job(
                    partial(
                        list_project_backups,
                        Path(hass.config.config_dir),
                        project_id,
                    )
                )
    except Exception as err:  # noqa: BLE001
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "retention": retention,
            "removed": removed,
            "cleanup_warning": cleanup_warning,
            "backups": backups,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/restore_backup",
        probatio.Required("subentry_id"): str,
        probatio.Required("transaction_id"): str,
        probatio.Optional("confirm", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_restore_backup(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Restore one backup behind the normal runtime write gate."""

    run = None
    phase = "prepare_restore"
    resource_lock_acquired = False
    try:
        entry = _entry(hass)
        _require_development(entry)
        if not bool(msg.get("confirm", False)):
            raise DeploymentError("Explicit backup restore confirmation is required")

        runtime = entry.runtime_data
        async with runtime.deployment_lock:
            _require_development(entry)
            await runtime.resource_lock.acquire()
            resource_lock_acquired = True
            subentry = _project(entry, msg["subentry_id"])
            project_id = _project_id(subentry)
            if not project_id:
                raise LookupError("Project has no trusted project id")
            repository = str(subentry.data.get(CONF_REPOSITORY, ""))
            diagnostics = _diagnostics(entry)
            run = await diagnostics.async_start_run(
                "backup_restore",
                project_id=project_id,
                repository=repository,
                context={
                    "backup_transaction_id": msg["transaction_id"],
                    "deployment_mode": runtime.deployment_mode.value,
                },
            )

            phase = "restore"
            run.start_phase(phase)
            result = await hass.async_add_executor_job(
                partial(
                    restore_project_backup,
                    config_root=Path(hass.config.config_dir),
                    project_id=project_id,
                    repository=repository,
                    backup_transaction_id=str(msg["transaction_id"]),
                )
            )

            if result.restart_required:
                _restart_pending_projects(hass).add(subentry.subentry_id)

            try:
                protected = {
                    result.restored_backup_id,
                    Path(result.safety_backup_path).name,
                }
                removed = await hass.async_add_executor_job(
                    partial(
                        prune_project_backups,
                        Path(hass.config.config_dir),
                        project_id,
                        _backup_retention(subentry),
                        protected_ids=protected,
                    )
                )
            except Exception as retention_err:  # noqa: BLE001
                removed = []
                await run.warning(
                    "backup_retention",
                    "Backup retention cleanup failed after restore",
                    phase="backup_retention",
                    details={"error": str(retention_err)},
                )

            await run.success(
                summary={
                    "transaction_id": result.transaction_id,
                    "restored_backup_id": result.restored_backup_id,
                    "safety_backup_path": result.safety_backup_path,
                    "changed_files": result.changed_files,
                    "lifecycle": result.lifecycle,
                    "restart_required": result.restart_required,
                    "retention": _backup_retention(subentry),
                    "removed_backups": removed,
                }
            )
            if resource_lock_acquired:
                runtime.resource_lock.release()
                resource_lock_acquired = False
    except Exception as err:  # noqa: BLE001
        if resource_lock_acquired:
            runtime.resource_lock.release()
            resource_lock_acquired = False
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "transaction_id": result.transaction_id,
            "restored_backup_id": result.restored_backup_id,
            "safety_backup_path": result.safety_backup_path,
            "journal_path": result.journal_path,
            "changed_files": result.changed_files,
            "lifecycle": result.lifecycle,
            "restart_required": result.restart_required,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/configure_git_export",
        probatio.Required("subentry_id"): str,
        probatio.Optional("github_token", default=""): str,
        probatio.Optional("clear", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_configure_git_export(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Configure the narrow write token used only for diagnostic Git exports."""
    run = None
    phase = "prepare"
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        subentry = _project(entry, msg["subentry_id"])
        data = dict(subentry.data)
        repository = str(data[CONF_REPOSITORY])
        clear = bool(msg.get("clear", False))
        supplied_token = str(msg.get("github_token", "")).strip()

        run = await diagnostics.async_start_run(
            "git_export_config",
            project_id=_project_id(subentry),
            repository=repository,
            context={
                "clear": clear,
                "token_supplied": bool(supplied_token),
                "export_root": DIAGNOSTIC_GIT_ROOT,
            },
        )

        if clear:
            data.pop(CONF_DIAGNOSTIC_GIT_TOKEN, None)
            phase = "persist"
            hass.config_entries.async_update_subentry(entry, subentry, data=data)
            await run.info(
                "home_assistant",
                "Diagnostic Git export token removed",
                phase=phase,
                details={"export_root": DIAGNOSTIC_GIT_ROOT},
            )
            await run.success(summary={"configured": False})
            connection.send_result(
                msg["id"],
                {
                    "configured": False,
                    "repository": repository,
                    "branch": data.get("default_branch"),
                    "root": DIAGNOSTIC_GIT_ROOT,
                },
            )
            return

        if not supplied_token:
            raise ProjectImportError("A diagnostic Git export token is required")

        diagnostics.register_secret(supplied_token)

        phase = "repository_probe"
        run.start_phase(phase)
        repository_info = await GitHubClient(
            async_get_clientsession(hass),
            supplied_token,
        ).async_get_repository(repository)
        await run.info(
            "github",
            "Diagnostic Git export token can access repository metadata",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "repository": repository_info.full_name,
                "default_branch": repository_info.default_branch,
                "private": repository_info.private,
                "archived": repository_info.archived,
            },
        )

        phase = "persist"
        data[CONF_DIAGNOSTIC_GIT_TOKEN] = supplied_token
        data["default_branch"] = repository_info.default_branch
        hass.config_entries.async_update_subentry(entry, subentry, data=data)
        await run.info(
            "home_assistant",
            "Diagnostic Git export credential persisted",
            phase=phase,
            details={
                "branch": repository_info.default_branch,
                "export_root": DIAGNOSTIC_GIT_ROOT,
            },
        )
        await run.success(summary={"configured": True})

    except Exception as err:  # noqa: BLE001
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "configured": True,
            "repository": repository_info.full_name,
            "branch": repository_info.default_branch,
            "root": DIAGNOSTIC_GIT_ROOT,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/export_git",
        probatio.Required("subentry_id"): str,
        probatio.Optional("limit", default=3000): int,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_export_git(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Commit one sanitized project-scoped support bundle to GitHub."""
    run = None
    phase = "prepare"
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        subentry = _project(entry, msg["subentry_id"])
        data = subentry.data

        export_token = str(data.get(CONF_DIAGNOSTIC_GIT_TOKEN, "")).strip()
        if not export_token:
            raise ProjectImportError("Configure a diagnostic Git export token first")

        diagnostics.register_secret(export_token)

        repository = str(data[CONF_REPOSITORY])
        branch = str(data.get("default_branch") or "").strip()
        if not branch:
            raise ProjectImportError("Repository default branch is missing")

        project_id = _project_id(subentry) or subentry.title
        source_ref = (
            str(data[CONF_SELECTED_SOURCE_REF])
            if data.get(CONF_SELECTED_SOURCE_REF)
            else None
        )
        source_commit = (
            str(data[CONF_SELECTED_SOURCE_COMMIT])
            if data.get(CONF_SELECTED_SOURCE_COMMIT)
            else None
        )

        run = await diagnostics.async_start_run(
            "diagnostic_git_export",
            project_id=_project_id(subentry),
            repository=repository,
            context={
                "branch": branch,
                "export_root": DIAGNOSTIC_GIT_ROOT,
                "source_ref": source_ref,
                "source_commit": source_commit,
            },
        )

        phase = "support_bundle"
        bundle = diagnostics.support_bundle(
            projects=[_safe_project(subentry)],
            deployment_mode=entry.runtime_data.deployment_mode.value,
            project_id=_project_id(subentry),
            limit=msg.get("limit", 3000),
        )
        await run.info(
            "diagnostics",
            "Project-scoped support bundle prepared for Git export",
            phase=phase,
            details={
                "event_count": len(bundle["json"].get("events", [])),
                "format": bundle["json"].get("format"),
            },
        )

        phase = "github_commit"
        run.start_phase(phase)
        result = await DiagnosticGitExportClient(
            async_get_clientsession(hass),
            export_token,
        ).async_export(
            repository=repository,
            branch=branch,
            project_id=str(project_id),
            source_ref=source_ref,
            source_commit=source_commit,
            support_bundle=bundle,
        )
        await run.info(
            "github",
            "Diagnostic support bundle committed to Git",
            phase=phase,
            duration_ms=run.phase_duration_ms(phase),
            details={
                "repository": result.repository,
                "branch": result.branch,
                "path": result.path,
                "commit_sha": result.commit_sha,
                "file_url": result.file_url,
                "commit_url": result.commit_url,
            },
        )
        await run.success(
            summary={
                "path": result.path,
                "commit_sha": result.commit_sha,
            }
        )
    except Exception as err:  # noqa: BLE001
        if run is not None:
            await run.fail(err, phase=phase)
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "repository": result.repository,
            "branch": result.branch,
            "path": result.path,
            "commit_sha": result.commit_sha,
            "commit_url": result.commit_url,
            "file_url": result.file_url,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/logs",
        probatio.Optional("limit", default=1000): int,
        probatio.Optional("levels", default=[]): [str],
        probatio.Optional("operation", default=""): str,
        probatio.Optional("run_id", default=""): str,
        probatio.Optional("project_id", default=""): str,
    }
)
@websocket_api.require_admin
def websocket_panel_logs(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return already-redacted structured diagnostics."""
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        events = diagnostics.query(
            limit=msg.get("limit", 1000),
            levels=set(msg.get("levels") or []) or None,
            operation=msg.get("operation") or None,
            run_id=msg.get("run_id") or None,
            project_id=msg.get("project_id") or None,
        )
    except Exception as err:  # noqa: BLE001
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(
        msg["id"],
        {
            "stats": diagnostics.stats(),
            "error_history": diagnostics.error_history(
                project_id=msg.get("project_id") or None
            ),
            "events": events,
        },
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): "deploy_relay/panel/support_bundle",
        probatio.Optional("subentry_id", default=""): str,
        probatio.Optional("limit", default=2000): int,
    }
)
@websocket_api.require_admin
def websocket_panel_support_bundle(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return a copy-ready text and JSON support bundle."""
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        project_id = None
        if msg.get("subentry_id"):
            project_id = _project_id(_project(entry, msg["subentry_id"]))

        bundle = diagnostics.support_bundle(
            projects=_safe_projects(entry),
            deployment_mode=entry.runtime_data.deployment_mode.value,
            project_id=project_id,
            limit=msg.get("limit", 2000),
        )
    except Exception as err:  # noqa: BLE001
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(msg["id"], bundle)


@websocket_api.websocket_command(
    {probatio.Required("type"): "deploy_relay/panel/clear_logs"}
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_panel_clear_logs(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Clear only Deploy Relay-owned diagnostic logs."""
    try:
        entry = _entry(hass)
        diagnostics = _diagnostics(entry)
        await diagnostics.async_clear()
    except Exception as err:  # noqa: BLE001
        _send_exception(connection, msg["id"], err)
        return

    connection.send_result(msg["id"], diagnostics.stats())


def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register Deploy Relay panel commands once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("websocket_registered"):
        return

    websocket_api.async_register_command(hass, websocket_panel_state)
    websocket_api.async_register_command(hass, websocket_panel_set_mode)
    websocket_api.async_register_command(hass, websocket_panel_import_project)
    websocket_api.async_register_command(hass, websocket_panel_remove_project)
    websocket_api.async_register_command(hass, websocket_panel_sources)
    websocket_api.async_register_command(hass, websocket_panel_select_source)
    websocket_api.async_register_command(hass, websocket_panel_preview)
    websocket_api.async_register_command(hass, websocket_panel_install)
    websocket_api.async_register_command(hass, websocket_panel_backups)
    websocket_api.async_register_command(hass, websocket_panel_set_backup_retention)
    websocket_api.async_register_command(hass, websocket_panel_restore_backup)
    websocket_api.async_register_command(hass, websocket_panel_configure_git_export)
    websocket_api.async_register_command(hass, websocket_panel_export_git)
    websocket_api.async_register_command(hass, websocket_panel_logs)
    websocket_api.async_register_command(hass, websocket_panel_support_bundle)
    websocket_api.async_register_command(hass, websocket_panel_clear_logs)
    domain_data["websocket_registered"] = True
