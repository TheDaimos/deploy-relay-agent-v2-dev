"""Bounded V2 DEV read-only journal. Stdlib-only: no filesystem or HA imports.

The sole production adapter supplies a Home Assistant Store (async_load/async_save).
This journal never authorizes writes or resumes any task after a reboot.
"""
from __future__ import annotations

import asyncio
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Protocol

SCHEMA = "dra-v2-dev-journal.v1"
RECORD_SCHEMA = "dra-operation-v2.v1"
MAX_RECORDS = 12
MAX_EVENTS = 48
MAX_BYTES = 48000
STATUSES = frozenset(("queued", "waiting_for_resource", "running",
    "cancel_requested", "success", "failed", "recovery_required", "cancelled",
    "interrupted"))
TERMINAL = frozenset(("success", "failed", "recovery_required", "cancelled",
    "interrupted"))
PHASES = frozenset(("prepare", "waiting", "select_source", "inventory",
    "preview", "preflight", "staging", "integrity", "backup", "apply",
    "verify", "cleanup", "rollback", "recovery", "complete"))
ERRORS = frozenset(("validation", "authorization", "source", "resource",
    "filesystem", "integration", "verification", "rollback", "unknown"))
FIELDS = frozenset(("schema", "operation_id", "operation_type",
    "project_key", "source_commit", "run_id", "status", "phase", "created_at",
    "started_at", "finished_at", "current_index", "total_count",
    "phase_percent", "progress_percent", "progress_exact", "error_family",
    "restart_required", "frontend_reload_possible", "recovery_required",
    "completed_items", "failed_items"))
EVENT_FIELDS = frozenset(("operation_id", "status", "at"))
ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
TIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}\+00:00\Z")


class JournalError(ValueError):
    """Public generic error: never include raw store contents or exceptions."""


class AsyncStore(Protocol):
    async def async_load(self) -> object: ...
    async def async_save(self, data: dict[str, object]) -> None: ...


def _time(value: object, *, optional: bool = False) -> bool:
    if value is None:
        return optional
    if not isinstance(value, str) or not TIME_PATTERN.fullmatch(value):
        return False
    try:
        return datetime.fromisoformat(value).utcoffset() == timezone.utc.utcoffset(None)
    except ValueError:
        return False


def _number(value: object, low: int, high: int, *, optional: bool = False) -> bool:
    return (value is None and optional) or (type(value) is int and low <= value <= high)


def _snapshot(value: object) -> dict[str, object]:
    """Validate full exact-schema snapshot and return an independent allowlisted copy."""
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise JournalError("invalid journal snapshot")
    s = dict(value)
    if (s["schema"] != RECORD_SCHEMA or
        not isinstance(s["operation_id"], str) or
        not ID_PATTERN.fullmatch(s["operation_id"]) or
        s["operation_type"] != "preview" or
        s["project_key"] != "lab_readonly_preview" or
        s["source_commit"] is not None or s["run_id"] is not None or
        not isinstance(s["status"], str) or s["status"] not in STATUSES or
        s["status"] == "recovery_required" or
        not isinstance(s["phase"], str) or s["phase"] not in PHASES or
        not _time(s["created_at"]) or not _time(s["started_at"], optional=True) or
        not _time(s["finished_at"], optional=True) or
        (s["status"] in TERMINAL) != (s["finished_at"] is not None) or
        (s["status"] == "running" and s["started_at"] is None) or
        not _number(s["current_index"], 0, 1_000_000_000, optional=True) or
        not _number(s["total_count"], 1, 1_000_000_000, optional=True) or
        (s["current_index"] is None) != (s["total_count"] is None) or
        (s["current_index"] is not None and s["current_index"] > s["total_count"]) or
        not _number(s["phase_percent"], 0, 100, optional=True) or
        not _number(s["progress_percent"], 0, 100, optional=True) or
        type(s["progress_exact"]) is not bool or
        (s["error_family"] is not None and
            (not isinstance(s["error_family"], str) or
             s["error_family"] not in ERRORS)) or
        (s["status"] != "failed" and s["error_family"] is not None) or
        s["restart_required"] is not False or
        s["frontend_reload_possible"] is not False or
        s["recovery_required"] is not False or
        not _number(s["completed_items"], 0, 1_000_000_000) or
        not _number(s["failed_items"], 0, 1_000_000_000) or
        (s["status"] == "success" and
            (s["progress_percent"] != 100 or s["phase"] != "complete")) or
        (s["status"] != "success" and s["progress_percent"] == 100) or
        (s["status"] != "success" and s["phase"] == "complete")):
        raise JournalError("invalid journal snapshot")
    return s


def _event(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != EVENT_FIELDS:
        raise JournalError("invalid journal event")
    if (not isinstance(value["operation_id"], str) or
        not ID_PATTERN.fullmatch(value["operation_id"]) or
        not isinstance(value["status"], str) or
        value["status"] not in STATUSES or
        not _time(value["at"])):
        raise JournalError("invalid journal event")
    return dict(value)


def _validate_document(value: object) -> tuple[OrderedDict[str, dict], list[dict]]:
    if not isinstance(value, dict) or set(value) != {"schema", "records", "events"}:
        raise JournalError("invalid journal document")
    if value["schema"] != SCHEMA:
        raise JournalError("unsupported journal schema")
    records, events = value["records"], value["events"]
    if (type(records) is not list or len(records) > MAX_RECORDS or
        type(events) is not list or len(events) > MAX_EVENTS):
        raise JournalError("journal retention exceeded")
    try:
        if len(json.dumps(value, ensure_ascii=True, separators=(",", ":"))) > MAX_BYTES:
            raise JournalError("journal size exceeded")
    except (TypeError, ValueError, RecursionError) as err:
        raise JournalError("invalid journal document") from None
    loaded: OrderedDict[str, dict] = OrderedDict()
    for raw in records:
        snap = _snapshot(raw)
        key = snap["operation_id"]
        if key in loaded:
            raise JournalError("duplicate operation id")
        loaded[key] = snap
    checked = [_event(raw) for raw in events]
    if any(item["operation_id"] not in loaded for item in checked):
        raise JournalError("orphan journal event")
    return loaded, checked


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class OperationJournal:
    """Fail-closed serialized Store adapter; never starts jobs after restart."""

    def __init__(self, store: AsyncStore) -> None:
        if not callable(getattr(store, "async_load", None)) or not callable(
            getattr(store, "async_save", None)
        ):
            raise JournalError("journal store not available")
        self._store = store
        self._lock = asyncio.Lock()
        self._records: OrderedDict[str, dict] = OrderedDict()
        self._events: list[dict] = []
        self._loaded = False

    def _document(self) -> dict[str, object]:
        return {"schema": SCHEMA, "records": list(self._records.values()),
                "events": self._events.copy()}

    async def load(self) -> None:
        async with self._lock:
            if self._loaded:
                raise JournalError("journal already opened")
            try:
                raw = await self._store.async_load()
            except Exception:
                raise JournalError("journal unavailable") from None
            if raw is None:
                self._loaded = True
                return
            records, events = _validate_document(raw)
            modified = False
            for key, snapshot in records.items():
                if snapshot["status"] not in TERMINAL:
                    snapshot["status"] = "interrupted"
                    snapshot["finished_at"] = _now()
                    snapshot["progress_exact"] = False
                    snapshot["error_family"] = None
                    snapshot["recovery_required"] = False
                    events.append({"operation_id": key, "status": "interrupted",
                                   "at": snapshot["finished_at"]})
                    modified = True
            events = events[-MAX_EVENTS:]
            if modified:
                try:
                    await self._store.async_save({
                        "schema": SCHEMA, "records": list(records.values()),
                        "events": events,
                    })
                except Exception:
                    raise JournalError("journal recovery write failed") from None
            self._records, self._events = records, events
            self._loaded = True

    async def capture(self, snapshot: dict[str, object]) -> None:
        safe = _snapshot(snapshot)
        async with self._lock:
            if not self._loaded:
                raise JournalError("journal not opened")
            original_records = self._records.copy()
            original_events = self._events.copy()
            key = safe["operation_id"]
            previous = self._records.get(key)
            if previous and previous["status"] in TERMINAL and previous != safe:
                raise JournalError("terminal journal record cannot change")
            self._records[key] = safe
            self._records.move_to_end(key)
            if previous is None or previous["status"] != safe["status"]:
                self._events.append({"operation_id": key, "status": safe["status"],
                                     "at": _now()})
            while len(self._records) > MAX_RECORDS:
                self._records.popitem(last=False)
            retained = set(self._records)
            self._events = [e for e in self._events
                            if e["operation_id"] in retained][-MAX_EVENTS:]
            try:
                document = self._document()
                if len(json.dumps(document, separators=(",", ":"))) > MAX_BYTES:
                    raise JournalError("journal size exceeded")
                await self._store.async_save(document)
            except Exception:
                self._records, self._events = original_records, original_events
                raise JournalError("journal write failed") from None

    async def get(self, operation_id: str) -> dict[str, object] | None:
        if not isinstance(operation_id, str) or not ID_PATTERN.fullmatch(operation_id):
            raise JournalError("invalid operation id")
        async with self._lock:
            value = self._records.get(operation_id)
            return value.copy() if value is not None else None

    async def list(self, limit: int = MAX_RECORDS) -> list[dict[str, object]]:
        if type(limit) is not int or not 1 <= limit <= MAX_RECORDS:
            raise JournalError("invalid journal list limit")
        async with self._lock:
            return [snap.copy() for snap in list(self._records.values())[::-1][:limit]]
