"""Diagnostics for Deploy Relay."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import DeployRelayConfigEntry
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
    SUBENTRY_TYPE_PROJECT,
    VERSION,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: DeployRelayConfigEntry,
) -> dict[str, Any]:
    """Return secret-free diagnostics including recent structured events."""
    del hass

    projects: list[dict[str, Any]] = []
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_TYPE_PROJECT:
            continue

        projects.append(
            {
                "title": subentry.title,
                "repository": subentry.data.get(CONF_REPOSITORY),
                "manifest_path": subentry.data.get(CONF_MANIFEST_PATH),
                "project_id": subentry.data.get("project_id"),
                "default_branch": subentry.data.get("default_branch"),
                "private": subentry.data.get("private"),
                "archived": subentry.data.get("archived"),
                "status": subentry.data.get("status"),
                "backup_retention": subentry.data.get(
                    CONF_BACKUP_RETENTION,
                    DEFAULT_BACKUP_RETENTION,
                ),
                "selected_source_kind": subentry.data.get(
                    CONF_SELECTED_SOURCE_KIND
                ),
                "selected_source_ref": subentry.data.get(
                    CONF_SELECTED_SOURCE_REF
                ),
                "selected_source_commit": subentry.data.get(
                    CONF_SELECTED_SOURCE_COMMIT
                ),
                "github_token_configured": bool(
                    subentry.data.get(CONF_GITHUB_TOKEN)
                ),
                "diagnostic_git_export_configured": bool(
                    subentry.data.get(CONF_DIAGNOSTIC_GIT_TOKEN)
                ),
            }
        )

    store = entry.runtime_data.diagnostics
    return {
        "version": VERSION,
        "deployment_mode": entry.runtime_data.deployment_mode.value,
        "deployment_writes_enabled": False,
        "background_checks_enabled": False,
        "project_count": len(projects),
        "projects": projects,
        "diagnostic_log": {
            "stats": store.stats() if store else None,
            "error_history": store.error_history() if store else [],
            "recent_events": store.query(limit=200) if store else [],
        },
    }
