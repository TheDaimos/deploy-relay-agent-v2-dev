"""DRA V2 isolated, bounded operation registry; no task or filesystem ownership.

This is a *preparatory* state registry, not a deployment scheduler. The future
Home Assistant operation manager must own runtime tasks, authorization checks,
transaction journaling, resource locks and shutdown/recovery separately.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections import OrderedDict
from re import fullmatch

try:
    from .operation_model import (
        ErrorFamily,
        OperationContractError,
        OperationPhase,
        OperationRecord,
        OperationStatus,
        OperationType,
    )
except ImportError:  # standard-library-only standalone tests
    from operation_model import (  # type: ignore[no-redef]
        ErrorFamily,
        OperationContractError,
        OperationPhase,
        OperationRecord,
        OperationStatus,
        OperationType,
    )


MUTATING_OPERATIONS = frozenset({
    OperationType.INSTALL,
    OperationType.RESTORE,
    OperationType.BATCH_INSTALL,
    OperationType.SELF_UPDATE,
})


class OperationRegistry:
    """In-memory, allowlisted snapshots with conservative admission controls.

    The service has no network methods, credentials, dynamic exception strings,
    storage writers or task-spawning APIs. Permission checks must be performed
    *outside* this class before registering any mutation.
    """

    def __init__(self, *, max_completed: int = 64, max_readonly: int = 2) -> None:
        if type(max_completed) is not int or not 1 <= max_completed <= 1000:
            raise OperationContractError("max_completed must be between 1 and 1000")
        if type(max_readonly) is not int or not 1 <= max_readonly <= 32:
            raise OperationContractError("max_readonly must be between 1 and 32")
        self._max_completed = max_completed
        self._max_readonly = max_readonly
        self._lock = asyncio.Lock()
        self._records: OrderedDict[str, OperationRecord] = OrderedDict()
        self._idempotency: dict[str, tuple[str, OperationType, str, str | None, str | None]] = {}

    @staticmethod
    def _hash_request(value: str | None) -> str | None:
        if value is None:
            return None
        # Never retain the original client-generated request key.
        if not isinstance(value, str) or fullmatch(r"[A-Za-z0-9_.-]{16,128}", value) is None:
            raise OperationContractError("invalid idempotency request id")
        return hashlib.sha256(value.encode("ascii")).hexdigest()

    @staticmethod
    def _operation_id(value: str) -> str:
        if not isinstance(value, str) or fullmatch(r"[0-9a-f]{32}", value) is None:
            raise OperationContractError("invalid operation id")
        return value

    def _prune_completed(self) -> None:
        terminal = [key for key, op in self._records.items() if op.terminal]
        excess = len(terminal) - self._max_completed
        for key in terminal[:max(0, excess)]:
            self._records.pop(key)
            # No dangling idempotency lookups to removed operations.
            for h, (mapped, *_rest) in tuple(self._idempotency.items()):
                if mapped == key:
                    del self._idempotency[h]

    async def register(
        self,
        *,
        operation_type: OperationType,
        project_key: str,
        source_commit: str | None = None,
        run_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, object]:
        """Admit a new descriptor. This NEVER starts/authorizes a mutation."""
        typ = OperationType(operation_type)
        # Validate *before* idempotent lookup so malformed requests cannot hide.
        candidate = OperationRecord(
            operation_type=typ,
            project_key=project_key,
            source_commit=source_commit,
            run_id=run_id,
        )
        fingerprint = self._hash_request(request_id)
        identity = (typ, candidate.project_key, candidate.source_commit, candidate.run_id)
        async with self._lock:
            if fingerprint is not None and fingerprint in self._idempotency:
                old_id, *stored_identity = self._idempotency[fingerprint]
                if tuple(stored_identity) != identity:
                    raise OperationContractError("request id reused for a different operation")
                return self._records[old_id].snapshot()
            in_flight = [op for op in self._records.values() if not op.terminal]
            if typ in MUTATING_OPERATIONS:
                if any(op.operation_type in MUTATING_OPERATIONS for op in in_flight):
                    raise OperationContractError("a mutating operation is already queued or active")
            elif sum(op.operation_type not in MUTATING_OPERATIONS for op in in_flight) >= self._max_readonly:
                raise OperationContractError("read-only operation capacity reached")
            self._records[candidate.operation_id] = candidate
            if fingerprint is not None:
                self._idempotency[fingerprint] = (candidate.operation_id, *identity)
            self._prune_completed()
            return candidate.snapshot()

    async def get(self, operation_id: str) -> dict[str, object] | None:
        self._operation_id(operation_id)
        async with self._lock:
            op = self._records.get(operation_id)
            return op.snapshot() if op else None

    async def list(self, *, active_only: bool = False, limit: int = 100) -> list[dict[str, object]]:
        if type(active_only) is not bool:
            raise OperationContractError("active_only must be a boolean")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise OperationContractError("limit must be 1 to 100")
        async with self._lock:
            matching = (
                op for op in reversed(tuple(self._records.values()))
                if not active_only or not op.terminal
            )
            return [op.snapshot() for _, op in zip(range(limit), matching)]

    async def transition(
        self,
        operation_id: str,
        target: OperationStatus,
        *,
        phase: OperationPhase | None = None,
        error_family: ErrorFamily | None = None,
    ) -> dict[str, object]:
        self._operation_id(operation_id)
        async with self._lock:
            op = self._records.get(operation_id)
            if op is None:
                raise OperationContractError("unknown operation")
            op.transition(target, phase=phase, error_family=error_family)
            self._prune_completed()
            return op.snapshot()

    async def progress(
        self,
        operation_id: str,
        *,
        phase: OperationPhase,
        current: int,
        total: int,
        overall: bool = False,
    ) -> dict[str, object]:
        self._operation_id(operation_id)
        async with self._lock:
            op = self._records.get(operation_id)
            if op is None:
                raise OperationContractError("unknown operation")
            op.update_progress(phase=phase, current=current, total=total, overall=overall)
            return op.snapshot()

    async def request_cancel(self, operation_id: str) -> dict[str, object]:
        """Request cancellation; never cancels an unsafe running transaction."""
        self._operation_id(operation_id)
        async with self._lock:
            op = self._records.get(operation_id)
            if op is None:
                raise OperationContractError("unknown operation")
            if op.status == OperationStatus.QUEUED:
                op.transition(OperationStatus.CANCELLED)
                self._prune_completed()
            elif op.status in {OperationStatus.WAITING_FOR_RESOURCE, OperationStatus.RUNNING}:
                op.transition(OperationStatus.CANCEL_REQUESTED)
            elif op.status != OperationStatus.CANCEL_REQUESTED:
                raise OperationContractError("cannot cancel a terminal operation")
            return op.snapshot()
