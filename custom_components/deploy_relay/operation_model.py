"""DRA V2: isolated, stdlib-only operation contract (not wired into V1 runtime).

No network, file-system mutation, Home Assistant dependencies or project tokens.
This model describes an operation; it never authorizes a deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from re import fullmatch
from typing import Final
from uuid import uuid4


class OperationContractError(ValueError):
    """An operation does not satisfy the accepted state contract."""


class OperationType(StrEnum):
    SOURCE_CHECK = "source_check"
    PREVIEW = "preview"
    INSTALL = "install"
    RESTORE = "restore"
    BATCH_CHECK = "batch_check"
    BATCH_INSTALL = "batch_install"
    SELF_UPDATE = "self_update"


class OperationStatus(StrEnum):
    QUEUED = "queued"
    WAITING_FOR_RESOURCE = "waiting_for_resource"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    SUCCESS = "success"
    FAILED = "failed"
    RECOVERY_REQUIRED = "recovery_required"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class OperationPhase(StrEnum):
    PREPARE = "prepare"
    WAITING = "waiting"
    SELECT_SOURCE = "select_source"
    INVENTORY = "inventory"
    PREVIEW = "preview"
    PREFLIGHT = "preflight"
    STAGING = "staging"
    INTEGRITY = "integrity"
    BACKUP = "backup"
    APPLY = "apply"
    VERIFY = "verify"
    CLEANUP = "cleanup"
    ROLLBACK = "rollback"
    RECOVERY = "recovery"
    COMPLETE = "complete"


class ErrorFamily(StrEnum):
    VALIDATION = "validation"
    AUTHORIZATION = "authorization"
    SOURCE = "source"
    RESOURCE = "resource"
    FILESYSTEM = "filesystem"
    INTEGRATION = "integration"
    VERIFICATION = "verification"
    ROLLBACK = "rollback"
    UNKNOWN = "unknown"


TERMINAL: Final[frozenset[OperationStatus]] = frozenset(
    {
        OperationStatus.SUCCESS,
        OperationStatus.FAILED,
        OperationStatus.RECOVERY_REQUIRED,
        OperationStatus.CANCELLED,
        OperationStatus.INTERRUPTED,
    }
)

MAX_WORK_ITEMS: Final[int] = 1_000_000_000

ALLOWED_TRANSITIONS: Final[dict[OperationStatus, frozenset[OperationStatus]]] = {
    OperationStatus.QUEUED: frozenset({
        OperationStatus.WAITING_FOR_RESOURCE, OperationStatus.RUNNING,
        OperationStatus.CANCELLED, OperationStatus.FAILED,
        OperationStatus.INTERRUPTED,
    }),
    OperationStatus.WAITING_FOR_RESOURCE: frozenset({
        OperationStatus.RUNNING, OperationStatus.CANCEL_REQUESTED,
        OperationStatus.CANCELLED, OperationStatus.FAILED,
        OperationStatus.INTERRUPTED,
    }),
    OperationStatus.RUNNING: frozenset({
        OperationStatus.WAITING_FOR_RESOURCE, OperationStatus.CANCEL_REQUESTED,
        OperationStatus.SUCCESS, OperationStatus.FAILED,
        OperationStatus.RECOVERY_REQUIRED, OperationStatus.INTERRUPTED,
    }),
    OperationStatus.CANCEL_REQUESTED: frozenset({
        # Cancelling cannot break a mutation in its unsafe critical section.
        OperationStatus.SUCCESS, OperationStatus.CANCELLED,
        OperationStatus.FAILED, OperationStatus.RECOVERY_REQUIRED,
        OperationStatus.INTERRUPTED,
    }),
    **{state: frozenset() for state in TERMINAL},
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _project_key(value: str) -> str:
    if not isinstance(value, str) or fullmatch(r"[a-zA-Z0-9_.-]{1,128}", value) is None:
        raise OperationContractError("project_key must be an opaque safe identifier")
    return value


def _commit_hash(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
        raise OperationContractError("source_commit must be a full immutable Git SHA")
    return value


def _run_key(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or fullmatch(r"[a-zA-Z0-9_.-]{1,128}", value) is None:
        raise OperationContractError("run_id must be an opaque identifier")
    return value


@dataclass(slots=True)
class OperationRecord:
    """Small, allowlisted snapshot of an operation (not proof of write approval).

    Use opaque internal project identifiers. Never store an access token,
    repository URL, file path, exception message or arbitrary metadata here.
    """

    operation_type: OperationType
    project_key: str
    source_commit: str | None = None
    run_id: str | None = None
    # Only identifying fields belong to the constructor. Generated state and
    # progress cannot be forged by passing extra constructor arguments.
    operation_id: str = field(default_factory=lambda: uuid4().hex, init=False)
    status: OperationStatus = field(default=OperationStatus.QUEUED, init=False)
    phase: OperationPhase = field(default=OperationPhase.PREPARE, init=False)
    created_at: str = field(default_factory=_utc_timestamp, init=False)
    started_at: str | None = field(default=None, init=False)
    finished_at: str | None = field(default=None, init=False)
    current_index: int | None = field(default=None, init=False)
    total_count: int | None = field(default=None, init=False)
    phase_percent: int | None = field(default=None, init=False)
    progress_percent: int | None = field(default=None, init=False)
    progress_exact: bool = field(default=False, init=False)
    error_family: ErrorFamily | None = field(default=None, init=False)
    restart_required: bool = field(default=False, init=False)
    frontend_reload_possible: bool = field(default=False, init=False)
    # Fixed, bounded, non-sensitive counters only: never arbitrary dict payloads.
    completed_items: int = field(default=0, init=False)
    failed_items: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.operation_type = OperationType(self.operation_type)
        self.status = OperationStatus(self.status)
        self.phase = OperationPhase(self.phase)
        self.project_key = _project_key(self.project_key)
        self.source_commit = _commit_hash(self.source_commit)
        self.run_id = _run_key(self.run_id)
        if not isinstance(self.operation_id, str) or fullmatch(r"[0-9a-f]{32}", self.operation_id) is None:
            raise OperationContractError("operation_id must be a UUID4-style hex key")
        if self.status != OperationStatus.QUEUED:
            raise OperationContractError("new operation must start queued")
        if any((self.started_at, self.finished_at, self.error_family, self.progress_percent, self.phase_percent)):
            raise OperationContractError("new operation cannot have fabricated progress or outcome")
        if self.completed_items or self.failed_items or self.current_index is not None or self.total_count is not None:
            raise OperationContractError("new operation cannot have work counters")
        if self.phase != OperationPhase.PREPARE or self.restart_required or self.frontend_reload_possible:
            raise OperationContractError("new operation cannot have fabricated phase or post action")

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL

    def transition(
        self,
        target: OperationStatus,
        *,
        phase: OperationPhase | None = None,
        error_family: ErrorFamily | None = None,
    ) -> None:
        """Advance to an allowed state. Terminal state is immutable."""
        target = OperationStatus(target)
        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise OperationContractError(f"invalid status transition {self.status} -> {target}")
        if error_family is not None and target not in (
            OperationStatus.FAILED, OperationStatus.RECOVERY_REQUIRED,
        ):
            raise OperationContractError("error family belongs only to a failed operation")
        family = ErrorFamily(error_family) if error_family is not None else None
        next_phase = OperationPhase(phase) if phase is not None else self.phase
        if target == OperationStatus.RUNNING and next_phase == OperationPhase.WAITING:
            next_phase = OperationPhase.PREPARE
        if target != OperationStatus.SUCCESS and next_phase == OperationPhase.COMPLETE:
            raise OperationContractError("only success may enter the complete phase")
        if target == OperationStatus.RECOVERY_REQUIRED:
            next_phase = OperationPhase.RECOVERY
        elif target == OperationStatus.SUCCESS:
            next_phase = OperationPhase.COMPLETE
        elif target == OperationStatus.WAITING_FOR_RESOURCE:
            next_phase = OperationPhase.WAITING
        self.status = target
        self.phase = next_phase
        if target == OperationStatus.RUNNING and self.started_at is None:
            self.started_at = _utc_timestamp()
        if target in TERMINAL:
            self.finished_at = _utc_timestamp()
            self.error_family = family
            if target == OperationStatus.SUCCESS:
                self.progress_percent = 100
                self.progress_exact = True
            else:
                self.progress_exact = False

    def update_progress(
        self,
        *,
        phase: OperationPhase,
        current: int,
        total: int,
        overall: bool = False,
    ) -> None:
        """Record actual counts without mistaking a phase for whole-job progress.

        Default: only phase_percent is known. The caller may set overall=True
        exclusively when (current, total) measure the *entire* operation.
        """
        if self.status is not OperationStatus.RUNNING:
            raise OperationContractError("progress is allowed only during running")
        next_phase = OperationPhase(phase)
        if isinstance(current, bool) or isinstance(total, bool) or not isinstance(current, int) or not isinstance(total, int):
            raise OperationContractError("progress requires integer work counts")
        if total < 1 or total > MAX_WORK_ITEMS or current < 0 or current > total:
            raise OperationContractError("invalid progress counters")
        if not isinstance(overall, bool):
            raise OperationContractError("overall must be a boolean")
        if self.phase == next_phase:
            if self.total_count is not None and self.total_count != total:
                raise OperationContractError("same-phase total cannot change silently")
            if self.current_index is not None and current < self.current_index:
                raise OperationContractError("same-phase progress cannot regress")
        self.phase = next_phase
        self.current_index = current
        self.total_count = total
        measured = (100 * current) // total
        self.phase_percent = measured
        if overall:
            # Whole-job 100 percent means verified success, never a running state.
            percent = min(99, measured)
            previous = self.progress_percent
            self.progress_percent = max(previous if previous is not None else 0, percent)
            self.progress_exact = bool(measured < 100 and self.progress_percent == percent)
        else:
            self.progress_exact = False

    def update_item_counts(self, *, completed: int, failed: int) -> None:
        if self.status is not OperationStatus.RUNNING:
            raise OperationContractError("work counters require running state")
        if any(
            isinstance(v, bool) or not isinstance(v, int)
            or not 0 <= v <= MAX_WORK_ITEMS for v in (completed, failed)
        ):
            raise OperationContractError("work counters must be nonnegative integers")
        if completed < self.completed_items or failed < self.failed_items:
            raise OperationContractError("work counters cannot regress")
        self.completed_items = completed
        self.failed_items = failed

    def mark_post_action(self, *, restart_required: bool, frontend_reload_possible: bool) -> None:
        if self.status is not OperationStatus.RUNNING:
            raise OperationContractError("post action must be set before reaching terminal state")
        if not isinstance(restart_required, bool) or not isinstance(frontend_reload_possible, bool):
            raise OperationContractError("post action flags must be boolean")
        self.restart_required = restart_required
        self.frontend_reload_possible = frontend_reload_possible and not restart_required

    def snapshot(self) -> dict[str, object]:
        """Explicit safe fields only, JSON serializable; no raw exception strings."""
        return {
            "schema": "dra-operation-v2.v1",
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "project_key": self.project_key,
            "source_commit": self.source_commit,
            "run_id": self.run_id,
            "status": self.status.value,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "current_index": self.current_index,
            "total_count": self.total_count,
            "phase_percent": self.phase_percent,
            "progress_percent": self.progress_percent,
            "progress_exact": self.progress_exact,
            "error_family": self.error_family.value if self.error_family else None,
            "restart_required": self.restart_required,
            "frontend_reload_possible": self.frontend_reload_possible,
            "recovery_required": self.status == OperationStatus.RECOVERY_REQUIRED,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
        }
