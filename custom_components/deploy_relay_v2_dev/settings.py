"""Private DRA V2 settings, startup CPU visibility and persistent warnings.

Core limits are configuration preferences only. This module never changes the
HA process affinity, mutating jobs or the read-only test-lab scheduler.
"""
from __future__ import annotations

import asyncio
import os
from typing import Protocol

SCHEMA = "dra-v2-dev-settings.v2"
LEGACY_SCHEMA = "dra-v2-dev-settings.v1"
MODES = frozenset({"sequential", "controlled"})
DEFAULT = {"mode": "sequential", "max_readonly_jobs": 2, "max_worker_processes": 4}
KEYS = frozenset(DEFAULT)
ENVELOPE_KEYS = frozenset({"schema", "settings", "available_cores", "hardware_warning"})
WARNING_KEYS = frozenset({"code", "previous_available", "available_cores", "reduced_from"})
MAX_REPORTED_CORES = 4096


class SettingsError(ValueError):
    """Invalid or unsafe preference or runtime observation (no secrets)."""


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


def valid_cores(value: object, *, optional: bool = False) -> int | None:
    if optional and value is None:
        return None
    if type(value) is not int or not 1 <= value <= MAX_REPORTED_CORES:
        raise SettingsError("invalid available core count")
    return value


def validate_warning(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if type(value) is not dict or set(value) != WARNING_KEYS:
        raise SettingsError("invalid hardware warning")
    if value["code"] != "cpu_limit_reduced" or type(value["code"]) is not str:
        raise SettingsError("invalid hardware warning code")
    previous = valid_cores(value["previous_available"], optional=True)
    count = valid_cores(value["available_cores"])
    was = valid_cores(value["reduced_from"])
    if was <= min(count, 12):
        raise SettingsError("invalid hardware warning limits")
    return {
        "code": "cpu_limit_reduced",
        "previous_available": previous,
        "available_cores": count,
        "reduced_from": was,
    }


def detect_available_cores() -> int | None:
    """HA process-visible logical CPUs; no claim of physical cores or quota.

    Affinity may be narrower than os.cpu_count(). If both APIs fail or report
    invalid data, do not invent a CPU count or change user preferences.
    """
    candidates: list[int] = []
    try:
        amount = os.cpu_count()
        if type(amount) is int and 1 <= amount <= MAX_REPORTED_CORES:
            candidates.append(amount)
    except (OSError, ValueError, TypeError):
        pass
    get_affinity = getattr(os, "sched_getaffinity", None)
    if get_affinity is not None:
        try:
            amount = len(get_affinity(0))
            if type(amount) is int and 1 <= amount <= MAX_REPORTED_CORES:
                candidates.append(amount)
        except (OSError, ValueError, TypeError):
            pass
    return min(candidates) if candidates else None


class V2Settings:
    def __init__(self, store: SettingsStore) -> None:
        self._store = store
        self._lock = asyncio.Lock()
        self._data: dict[str, object] | None = None
        self._available_cores: int | None = None
        self._warning: dict[str, object] | None = None

    async def load(self) -> None:
        try:
            value = await self._store.async_load()
        except Exception:
            raise SettingsError("settings load failed") from None
        if value is None:
            self._data = dict(DEFAULT)
            self._available_cores = None
            self._warning = None
            return
        if type(value) is not dict:
            raise SettingsError("unknown settings envelope")
        if set(value) == {"schema", "settings"} and value["schema"] == LEGACY_SCHEMA:
            self._data = validate(value["settings"])
            self._available_cores = None
            self._warning = None
            return
        if set(value) != ENVELOPE_KEYS or value["schema"] != SCHEMA:
            raise SettingsError("unknown settings schema")
        data = validate(value["settings"])
        available = valid_cores(value["available_cores"], optional=True)
        warning = validate_warning(value["hardware_warning"])
        self._data = data
        self._available_cores = available
        self._warning = warning

    def snapshot(self) -> dict[str, object]:
        if self._data is None:
            raise SettingsError("settings unavailable")
        return dict(self._data)

    def core_status(self) -> dict[str, object]:
        self.snapshot()
        return {
            "available_cores": self._available_cores,
            "warning": dict(self._warning) if self._warning is not None else None,
        }

    def _envelope(
        self, data: dict[str, object], available: int | None,
        warning: dict[str, object] | None,
    ) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "settings": dict(data),
            "available_cores": available,
            "hardware_warning": dict(warning) if warning is not None else None,
        }

    async def _write(
        self, data: dict[str, object], available: int | None,
        warning: dict[str, object] | None,
    ) -> None:
        try:
            await self._store.async_save(self._envelope(data, available, warning))
        except Exception:
            raise SettingsError("settings save failed") from None
        self._data = dict(data)
        self._available_cores = available
        self._warning = dict(warning) if warning is not None else None

    async def startup_check(self, available: int | None = None, *, probe: bool = True) -> dict[str, object]:
        """Remember available cores each startup; clamp and warn on reduction.

        If count grows, update observation silently; never auto-increase the
        user's chosen worker limit. Failed detection does not rewrite settings.
        """
        count = detect_available_cores() if probe else available
        if count is None:
            return self.core_status()
        count = valid_cores(count)
        async with self._lock:
            data = self.snapshot()
            prior = self._available_cores
            warning = self._warning
            if data["max_worker_processes"] > count:
                warning = {
                    "code": "cpu_limit_reduced",
                    "previous_available": prior,
                    "available_cores": count,
                    "reduced_from": data["max_worker_processes"],
                }
                data["max_worker_processes"] = count
            if data != self._data or prior != count or warning != self._warning:
                await self._write(data, count, warning)
            return self.core_status()

    async def save(self, values: object) -> dict[str, object]:
        desired = validate(values)
        async with self._lock:
            if self._data is None:
                raise SettingsError("settings unavailable")
            if (self._available_cores is not None and
                    desired["max_worker_processes"] > self._available_cores):
                raise SettingsError("requested workers exceed available cores")
            if desired == self._data and self._warning is None:
                return self.snapshot()
            await self._write(desired, self._available_cores, None)
            return self.snapshot()

    async def acknowledge_warning(self) -> dict[str, object]:
        async with self._lock:
            data = self.snapshot()
            if self._warning is not None:
                await self._write(data, self._available_cores, None)
            return self.core_status()

    def effective(self) -> dict[str, object]:
        """Current test lab is unchanged: no parallel/read-write activation."""
        self.snapshot()
        return {
            "running_mode": "single_readonly_job",
            "active_readonly_limit": 1,
            "mutation_limit": 0,
            "worker_budget_enforced": False,
            "automatic_mode_available": False,
        }
