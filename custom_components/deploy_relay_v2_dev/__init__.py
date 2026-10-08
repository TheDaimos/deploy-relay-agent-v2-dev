"""DRA V2 development lab: harmless read-only tasks on an existing HA-DEV.

This integration is separate from the deploy_relay V1 integration.
No project installation, backup handling, source access or restore is provided.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .operation_registry import OperationRegistry
from .operation_journal import JournalError, OperationJournal
from .readonly_task_supervisor import ReadOnlyTaskSupervisor
from .readonly_benchmark import ReadOnlyMeasurement
from .ha_preview_task_factory import PreviewTaskFactory
from .panel import async_register_panel, async_remove_panel
from .websocket_api import async_register_commands


@dataclass(slots=True)
class LabRuntime:
    registry: OperationRegistry
    supervisor: ReadOnlyTaskSupervisor
    journal: OperationJournal
    measurement: ReadOnlyMeasurement


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create a fresh, read-only lab for a single config entry."""
    store = hass.data.setdefault(DOMAIN, {})
    if "runtime" in store:
        return False
    # Fixed, private-to-this-integration .storage key; fail closed on any
    # unreadable/incompatible record instead of overwriting evidence.
    journal = OperationJournal(Store(hass, 1, "deploy_relay_v2_dev.journal"))
    try:
        await journal.load()
    except JournalError:
        return False
    measurement = ReadOnlyMeasurement()
    registry = OperationRegistry(max_completed=12, max_readonly=1)
    supervisor = ReadOnlyTaskSupervisor(
        registry,
        PreviewTaskFactory(hass, entry),
        on_registered=journal.capture,
        on_terminal=journal.capture,
    )
    runtime = LabRuntime(registry=registry, supervisor=supervisor, journal=journal,
                         measurement=measurement)
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
