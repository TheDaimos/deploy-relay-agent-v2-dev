"""V2: Home Assistant ConfigEntry task factory for read-only preview trials.

Not wired into DRA setup, WebSocket or deployment paths.
The active HA integration still uses the existing V1 lifecycle.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, Protocol


class ConfigEntryBackgroundTaskAPI(Protocol):
    """Narrow public HA ConfigEntry background task interface."""

    def async_create_background_task(
        self,
        hass: object,
        target: Coroutine[Any, Any, None],
        name: str,
        *,
        eager_start: bool = True,
    ) -> asyncio.Task[None]: ...


class PreviewTaskFactory:
    """Schedule a read-only coroutine under the config entry lifecycle.

    The caller must provide a read-only, already authorized preview coroutine.
    This factory does not authenticate the user or authorize a Git source.
    """

    def __init__(self, hass: object, entry: ConfigEntryBackgroundTaskAPI) -> None:
        if hass is None or not callable(
            getattr(entry, "async_create_background_task", None)
        ):
            raise ValueError("Home Assistant and a ConfigEntry task API are required")
        self._hass = hass
        self._entry = entry

    def __call__(
        self, coroutine: Coroutine[Any, Any, None]
    ) -> asyncio.Task[None]:
        """Create entry-owned background task without eager execution.

        Delayed first scheduling makes registry/task bookkeeping deterministic.
        HA owns the task and handles its lifetime at config entry unload.
        """
        return self._entry.async_create_background_task(
            self._hass,
            coroutine,
            "Deploy Relay V2 read-only preview",
            eager_start=False,
        )
