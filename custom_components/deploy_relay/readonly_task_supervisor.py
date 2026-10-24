"""Isolated V2 owner for read-only preview tasks.

NOT imported by the HA integration. A future adapter must provide a HA-owned
task factory, administrator checks and an explicit config-entry lifecycle.
This module cannot install, restore, update or grant deployment permissions.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

try:
    from .operation_model import (
        ErrorFamily, OperationContractError, OperationPhase, OperationStatus,
        OperationType,
    )
    from .operation_registry import OperationRegistry
except ImportError:
    from operation_model import (  # type: ignore[no-redef]
        ErrorFamily, OperationContractError, OperationPhase, OperationStatus,
        OperationType,
    )
    from operation_registry import OperationRegistry  # type: ignore[no-redef]

ProgressReporter = Callable[[OperationPhase, int, int], Awaitable[None]]
ReadOnlyWork = Callable[[ProgressReporter], Awaitable[None]]
TaskFactory = Callable[[Coroutine[Any, Any, None]], asyncio.Task[None]]


class ReadOnlyTaskSupervisor:
    """In-memory preview job ownership without any external API or mutations."""

    def __init__(self, registry: OperationRegistry, task_factory: TaskFactory) -> None:
        if not isinstance(registry, OperationRegistry) or not callable(task_factory):
            raise OperationContractError("registry and task factory are required")
        self._registry = registry
        self._task_factory = task_factory
        self._start_lock = asyncio.Lock()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._closed = False

    async def start_preview(
        self,
        *,
        project_key: str,
        request_id: str,
        work: ReadOnlyWork,
        source_commit: str | None = None,
    ) -> dict[str, object]:
        """Queue read-only work; does NOT authorize HA users or Git sources."""
        if not callable(work):
            raise OperationContractError("read-only work callback required")
        async with self._start_lock:
            if self._closed:
                raise OperationContractError("read-only task owner is closed")
            snapshot = await self._registry.register(
                operation_type=OperationType.PREVIEW,
                project_key=project_key,
                request_id=request_id,
                source_commit=source_commit,
            )
            key = str(snapshot["operation_id"])
            if key in self._tasks or snapshot["status"] != OperationStatus.QUEUED.value:
                return snapshot

            async def runner() -> None:
                try:
                    await self._registry.transition(key, OperationStatus.RUNNING)

                    async def progress(
                        phase: OperationPhase, current: int, total: int
                    ) -> None:
                        await self._registry.progress(
                            key, phase=phase, current=current, total=total,
                            overall=False,
                        )

                    await work(progress)
                    await self._registry.transition(key, OperationStatus.SUCCESS)
                except asyncio.CancelledError:
                    await self._registry.transition(key, OperationStatus.INTERRUPTED)
                    raise
                except Exception:
                    # Only safe, predefined error families enter the snapshot.
                    await self._registry.transition(
                        key, OperationStatus.FAILED,
                        error_family=ErrorFamily.UNKNOWN,
                    )

            coro = runner()
            try:
                task = self._task_factory(coro)
                if not isinstance(task, asyncio.Task):
                    raise TypeError("task factory returned no Task")
            except Exception:
                coro.close()
                await self._registry.transition(
                    key, OperationStatus.FAILED,
                    error_family=ErrorFamily.RESOURCE,
                )
                raise OperationContractError(
                    "unable to schedule a read-only job"
                ) from None
            self._tasks[key] = task
            task.add_done_callback(
                lambda done, op_id=key: self._tasks.pop(op_id, None)
            )
            return snapshot

    async def close(self) -> None:
        """Cancel only read-only jobs and close unfinished registry entries."""
        async with self._start_lock:
            self._closed = True
            pending = tuple(self._tasks.items())
            for _key, task in pending:
                task.cancel()
        if pending:
            await asyncio.gather(
                *(task for _, task in pending), return_exceptions=True
            )
        for key, _task in pending:
            snapshot = await self._registry.get(key)
            if snapshot and snapshot["status"] in {
                OperationStatus.QUEUED.value,
                OperationStatus.WAITING_FOR_RESOURCE.value,
                OperationStatus.RUNNING.value,
                OperationStatus.CANCEL_REQUESTED.value,
            }:
                await self._registry.transition(
                    key, OperationStatus.INTERRUPTED
                )
