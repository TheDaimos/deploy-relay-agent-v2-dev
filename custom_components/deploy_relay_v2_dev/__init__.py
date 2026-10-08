"""DRA V2 development lab: harmless read-only tasks on an existing HA-DEV.

This integration is separate from the deploy_relay V1 integration.
No project installation, backup handling, source access or restore is provided.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .operation_registry import OperationRegistry
from .readonly_task_supervisor import ReadOnlyTaskSupervisor
from .ha_preview_task_factory import PreviewTaskFactory
from .panel import async_register_panel, async_remove_panel
from .websocket_api import async_register_commands


@dataclass(slots=True)
class LabRuntime:
    registry: OperationRegistry
    supervisor: ReadOnlyTaskSupervisor


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create a fresh, read-only lab for a single config entry."""
    store = hass.data.setdefault(DOMAIN, {})
    if "runtime" in store:
        return False
    registry = OperationRegistry(max_completed=12, max_readonly=1)
    supervisor = ReadOnlyTaskSupervisor(
        registry,
        PreviewTaskFactory(hass, entry),
    )
    runtime = LabRuntime(registry=registry, supervisor=supervisor)
    store["runtime"] = runtime
    try:
        async_register_commands(hass)
        await async_register_panel(hass)
    except Exception:
        await supervisor.close()
        store.pop("runtime", None)
        raise
    entry.runtime_data = runtime
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop only our read-only lab tasks; never touch V1 state."""
    store = hass.data.get(DOMAIN)
    runtime = store.get("runtime") if isinstance(store, dict) else None
    if runtime is not None:
        await runtime.supervisor.close()
    async_remove_panel(hass)
    if isinstance(store, dict):
        store.pop("runtime", None)
    return True
