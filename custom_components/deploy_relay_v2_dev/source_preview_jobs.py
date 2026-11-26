"""HA-owned read-only source-preview jobs, reconnectable during one HA runtime.

No filesystem, network or credential code lives here. The authorized caller
supplies an inspected, bounded coroutine. Results cannot authorize install.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any
from uuid import uuid4

from .project_catalog import CatalogError, normalize_repo
from .remote_source import source_ref, PreflightError
from .source_job_history import SourceJobHistory, SourceJobHistoryError

MAX_JOBS = 4
# Explicit DEV-only fixed-duration network interruption test. Does not change
# the real source inspection timeout, and cannot be configured by the caller.
CONNECTION_TEST_SECONDS = 60
ACTIVE = frozenset({"queued", "running"})
RESULT_SCHEMA = "dra-v2-source-preview-job.v1"


async def _connection_test_delay() -> None:
    """Yield to HA for a fixed 60s test window, without blocking its event loop."""
    await asyncio.sleep(CONNECTION_TEST_SECONDS)


class SourcePreviewJobError(ValueError):
    """Fixed category only; never raw remote or local exception text."""


class SourcePreviewJobs:
    """Single-flight read-only work owned by the HA ConfigEntry, not a browser."""

    def __init__(
        self, task_factory: Callable[[Coroutine[Any, Any, None]], asyncio.Task],
        *, history: SourceJobHistory | None = None,
    ) -> None:
        if not callable(task_factory):
            raise SourcePreviewJobError("task factory required")
        self._task_factory = task_factory
        self._history = history
        self._lock = asyncio.Lock()
        self._jobs: OrderedDict[str, dict] = OrderedDict()
        self._tasks: dict[str, asyncio.Task] = {}
        self._closed = False

    @staticmethod
    def _copy(row: dict) -> dict:
        # Reports include nested lists. Never expose mutable internal buffers.
        import copy
        return copy.deepcopy(row)

    def _prune(self) -> None:
        for key in list(self._jobs):
            if len(self._jobs) <= MAX_JOBS:
                break
            if self._jobs[key]["status"] not in ACTIVE:
                del self._jobs[key]

    async def start(
        self, repository: str, ref: str, *,
        inspect: Callable[[], Awaitable[dict]],
        connection_test: bool = False,
    ) -> dict:
        try:
            canonical = normalize_repo(repository)
            checked_ref = source_ref(ref)
        except (CatalogError, PreflightError):
            raise SourcePreviewJobError("invalid source selection") from None
        if not callable(inspect):
            raise SourcePreviewJobError("read-only inspector required")
        if type(connection_test) is not bool:
            raise SourcePreviewJobError("invalid connection test mode")
        async with self._lock:
            if self._closed:
                raise SourcePreviewJobError("source jobs closed")
            active = next((row for row in self._jobs.values()
                           if row["status"] in ACTIVE), None)
            if active is not None:
                if (active["repository"].casefold() == canonical.casefold() and
                        active["ref"] == checked_ref and
                        active["connection_test"] is connection_test):
                    return self._copy(active)  # double-tap is idempotent
                raise SourcePreviewJobError("source preview already active")
            job_id = uuid4().hex
            row = {
                "schema": RESULT_SCHEMA, "operation_id": job_id,
                "repository": canonical, "ref": checked_ref,
                "status": "queued", "stage": "admission",
                "connection_test": connection_test,
                "result": None, "reason": None,
                "installation_enabled": False,
            }
            # Commit minimal non-resumable metadata before scheduling work.
            if self._history is not None:
                try:
                    await self._history.queued(job_id)
                except SourceJobHistoryError:
                    raise SourcePreviewJobError("source history unavailable") from None
            self._jobs[job_id] = row
            self._prune()

            async def runner() -> None:
                try:
                    row["status"] = "running"
                    if connection_test:
                        # The operation already belongs to HA; closing the
                        # browser must not cancel this bounded, read-only wait.
                        row["stage"] = "connection_test_wait"
                        await _connection_test_delay()
                    row["stage"] = "source_inspection"
                    report = await inspect()
                    claim = report.get("target_claims") if type(report) is dict else None
                    import re
                    if (type(report) is not dict or
                            report.get("schema") != "dra-v2-dev-source-preview.v1" or
                            type(report.get("source_commit")) is not str or
                            re.fullmatch(r"[0-9a-f]{40}", report["source_commit"]) is None or
                            report.get("sources_verified") is not True or
                            report.get("local_inventory_readonly") is not True or
                            report.get("handover_required") is not True or
                            report.get("backup_verified") is not False or
                            report.get("installation_enabled") is not False or
                            type(report.get("repository")) is not str or
                            report["repository"].casefold() != canonical.casefold() or
                            type(claim) is not dict or
                            claim.get("exclusive_ownership_verified") is not False or
                            claim.get("cross_process_lock_verified") is not False or
                            claim.get("backup_verified") is not False or
                            claim.get("installation_enabled") is not False):
                        raise SourcePreviewJobError("untrusted source result")
                    if self._history is not None:
                        await self._history.terminal(job_id, "success")
                    row["result"] = self._copy(report)
                    row["stage"] = "complete"
                    row["status"] = "success"
                except asyncio.CancelledError:
                    if self._history is not None:
                        try:
                            await self._history.terminal(
                                job_id, "interrupted", reason="interrupted")
                        except SourceJobHistoryError:
                            pass  # Queued state will be interrupted on next startup.
                    row["result"] = None
                    row["stage"] = "interrupted"
                    row["reason"] = "interrupted"
                    row["status"] = "interrupted"
                    raise
                except Exception:
                    if self._history is not None:
                        try:
                            await self._history.terminal(
                                job_id, "failed", reason="source_unavailable")
                        except SourceJobHistoryError:
                            pass  # Never report success without durable evidence.
                    row["result"] = None
                    row["stage"] = "failed"
                    row["reason"] = "source_unavailable"
                    row["status"] = "failed"
                finally:
                    self._tasks.pop(job_id, None)

            coroutine = runner()
            try:
                task = self._task_factory(coroutine)
                if not isinstance(task, asyncio.Task):
                    raise TypeError("invalid HA task")
            except Exception:
                coroutine.close()
                if self._history is not None:
                    try:
                        await self._history.terminal(
                            job_id, "failed", reason="resource_unavailable")
                    except SourceJobHistoryError:
                        pass
                row["status"] = "failed"
                row["stage"] = "failed"
                row["reason"] = "resource_unavailable"
                raise SourcePreviewJobError("unable to schedule preview") from None
            self._tasks[job_id] = task
            return self._copy(row)

    async def get(self, operation_id: str) -> dict | None:
        if type(operation_id) is not str or len(operation_id) != 32 or any(
                c not in "0123456789abcdef" for c in operation_id):
            raise SourcePreviewJobError("invalid operation identifier")
        async with self._lock:
            row = self._jobs.get(operation_id)
            return self._copy(row) if row is not None else None

    async def latest(self) -> dict | None:
        async with self._lock:
            return self._copy(next(reversed(self._jobs.values()))) if self._jobs else None

    async def close(self) -> None:
        async with self._lock:
            self._closed = True
            pending = list(self._tasks.values())
            for task in pending:
                task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        async with self._lock:
            for row in self._jobs.values():
                if row["status"] in ACTIVE:
                    row.update(status="interrupted", stage="interrupted",
                               reason="interrupted", result=None)
            self._tasks.clear()
