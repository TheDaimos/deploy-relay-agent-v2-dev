"""Private V2 configuration: policy input, not worker or mutation activation.

No scheduler is reconfigured by saving settings. This is deliberate until
resource and write-path admission contracts pass their separate HA gates.
"""
from __future__ import annotations

import asyncio
from typing import Protocol

SCHEMA = "dra-v2-dev-settings.v1"
MODES = frozenset({"sequential", "controlled"})
DEFAULT = {"mode": "sequential", "max_readonly_jobs": 2, "max_worker_processes": 4}
KEYS = frozenset(DEFAULT)


class SettingsError(ValueError):
    """Invalid or unsafe preference (no secrets or paths)."""


class SettingsStore(Protocol):
    async def async_load(self) -> object: ...
    async def async_save(self, value: dict[str, object]) -> None: ...


def validate(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != KEYS:
        raise SettingsError("invalid settings keys")
    if type(value["mode"]) is not str or value["mode"] not in MODES:
        raise SettingsError("unsupported operating mode")
    for key, minimum, maximum in (
        ("max_readonly_jobs", 1, 4), ("max_worker_processes", 1, 12)
    ):
        n = value[key]
        if type(n) is not int or not minimum <= n <= maximum:
            raise SettingsError(f"invalid {key}")
    return {key: value[key] for key in DEFAULT}


class V2Settings:
    def __init__(self, store: SettingsStore) -> None:
        self._store = store
        self._lock = asyncio.Lock()
        self._data: dict[str, object] | None = None

    async def load(self) -> None:
        try:
            value = await self._store.async_load()
        except Exception:
            raise SettingsError("settings load failed") from None
        if value is None:
            self._data = dict(DEFAULT)
            return
        if type(value) is not dict or set(value) != {"schema", "settings"}:
            raise SettingsError("unknown settings envelope")
        if value["schema"] != SCHEMA:
            raise SettingsError("unknown settings schema")
        self._data = validate(value["settings"])

    def snapshot(self) -> dict[str, object]:
        if self._data is None:
            raise SettingsError("settings unavailable")
        return dict(self._data)

    async def save(self, values: object) -> dict[str, object]:
        desired = validate(values)
        async with self._lock:
            if self._data is None:
                raise SettingsError("settings unavailable")
            if desired == self._data:
                return self.snapshot()
            try:
                await self._store.async_save({"schema": SCHEMA, "settings": desired})
            except Exception:
                raise SettingsError("settings save failed") from None
            self._data = desired
            return self.snapshot()

    def effective(self) -> dict[str, object]:
        """Never claim limits are enforced by the current test-lab scheduler."""
        self.snapshot()
        return {
            "running_mode": "single_readonly_job",
            "active_readonly_limit": 1,
            "mutation_limit": 0,
            "worker_budget_enforced": False,
            "automatic_mode_available": False,
        }
