"""Deploy Relay custom integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DIAGNOSTIC_GIT_TOKEN,
    CONF_GITHUB_TOKEN,
    CONF_SHOW_SIDEBAR_PANEL,
    DEFAULT_SHOW_SIDEBAR_PANEL,
    LEGACY_CONF_SHOW_SIDEBAR,
    LEGACY_NAME,
    NAME,
    DeploymentMode,
    PLATFORMS,
)
from .diagnostic_store import DiagnosticStore
from .panel import async_remove_panel, async_setup_panel
from .websocket_api import async_register_websocket_commands


@dataclass(slots=True)
class DeployRelayRuntimeData:
    """Non-persistent per-entry runtime state.

    Every setup/restart begins LOCKED. DEVELOPMENT is runtime-only and must be
    explicitly re-enabled by an administrator before deployment writes.
    """

    deployment_mode: DeploymentMode = DeploymentMode.LOCKED
    diagnostics: DiagnosticStore | None = None
    deployment_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    resource_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


type DeployRelayConfigEntry = ConfigEntry[DeployRelayRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeployRelayConfigEntry,
) -> bool:
    """Set up Deploy Relay from a Config Entry."""
    if entry.title == LEGACY_NAME:
        hass.config_entries.async_update_entry(entry, title=NAME)

    options = dict(entry.options)
    if CONF_SHOW_SIDEBAR_PANEL not in options:
        options[CONF_SHOW_SIDEBAR_PANEL] = bool(
            options.pop(
                LEGACY_CONF_SHOW_SIDEBAR,
                DEFAULT_SHOW_SIDEBAR_PANEL,
            )
        )
    else:
        options.pop(LEGACY_CONF_SHOW_SIDEBAR, None)

    if options != entry.options:
        hass.config_entries.async_update_entry(entry, options=options)

    diagnostics = DiagnosticStore(hass)

    for subentry in entry.subentries.values():
        for key in (CONF_GITHUB_TOKEN, CONF_DIAGNOSTIC_GIT_TOKEN):
            token = subentry.data.get(key)
            if token:
                diagnostics.register_secret(str(token))

    entry.runtime_data = DeployRelayRuntimeData(
        diagnostics=diagnostics,
    )
    await diagnostics.async_initialize()
    await diagnostics.async_event(
        "INFO",
        "integration",
        "Deploy Relay config entry setup",
        operation="runtime",
        phase="setup_entry",
        details={
            "entry_id": entry.entry_id,
            "project_count": len(entry.subentries),
            "deployment_mode": entry.runtime_data.deployment_mode.value,
        },
    )

    async_register_websocket_commands(hass)
    if options[CONF_SHOW_SIDEBAR_PANEL]:
        await async_setup_panel(hass)
    else:
        async_remove_panel(hass)

    if PLATFORMS:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: DeployRelayConfigEntry,
) -> bool:
    """Unload Deploy Relay."""
    diagnostics = entry.runtime_data.diagnostics
    if diagnostics is not None:
        await diagnostics.async_event(
            "INFO",
            "integration",
            "Deploy Relay config entry unloading",
            operation="runtime",
            phase="unload_entry",
        )

    if PLATFORMS and not await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    ):
        if diagnostics is not None:
            await diagnostics.async_event(
                "ERROR",
                "integration",
                "Platform unload failed",
                operation="runtime",
                phase="unload_entry",
            )
        return False

    async_remove_panel(hass)
    return True
