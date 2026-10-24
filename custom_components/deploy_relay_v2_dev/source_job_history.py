"""G2 read-only job history: bounded, secret-free, restart-safe HA Store contract.

Persist only job identifier, timestamps, status and fixed error family.
NEVER persist project/repository, Git ref, commit, tokens, preview report,
file listings or raw exceptions. An interrupted job is NEVER resumed.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from datetime import datetime, timezone
import json
import re
from typing import Protocol

SCHEMA = "dra-v2-source-job-history.v1"
MAX_RECORDS = 8
MAX_BYTES = 6000
FIELDS = frozenset({
    "operation_id", "status", "created_at", "finished_at",
    "reason", "installation_enabled", "resume_allowed",
    "source_preview_saved",
})
ID = re.compile(r"[a-f0-9]{32}\Z")
STATES = frozenset({"queued", "success", "failed", "interrupted"})
TERMINAL = frozenset({"success", "failed", "interrupted"})
REASONS = frozenset({"source_unavailable", "resource_unavailable", "interrupted", "history_unavailable"})


class SourceJobHistoryError(ValueError):
    """Always sanitized: never include stored bytes or exceptions."""


class AsyncStore(Protocol):
    async def async_load(self) -> object: ...
    async def async_save(self, data: dict) -> None: ...


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _valid_time(value: object) -> bool:
    if type(value) is not str or len(value) != 25 or not value.endswith("+00:00"):
        return False
    try:
        return datetime.fromisoformat(value).utcoffset() == timezone.utc.utcoffset(None)
    except ValueError:
        return False


def sanitized(row: object) -> dict:
    if type(row) is not dict or set(row) != FIELDS:
        raise SourceJobHistoryError("invalid source history record")
    if (type(row["operation_id"]) is not str or not ID.fullmatch(row["operation_id"]) or
        type(row["status"]) is not str or row["status"] not in STATES or
        not _valid_time(row["created_at"]) or
        (row["finished_at"] is not None and not _valid_time(row["finished_at"])) or
        ((row["status"] in TERMINAL) != (row["finished_at"] is not None)) or
        (row["reason"] is not None and (
            type(row["reason"]) is not str or row["reason"] not in REASONS)) or
        (row["status"] == "success" and row["reason"] is not None) or
        (row["status"] == "queued" and row["reason"] is not None) or
        (row["status"] in {"failed", "interrupted"} and row["reason"] is None) or
        row["installation_enabled"] is not False or
        row["resume_allowed"] is not False or
        row["source_preview_saved"] is not False):
        raise SourceJobHistoryError("invalid source history record")
    return dict(row)


def _validated_document(value: object) -> OrderedDict[str, dict]:
    if type(value) is not dict or set(value) != {"schema", "records"} or value["schema"] != SCHEMA:
        raise SourceJobHistoryError("invalid source history document")
    rows = value["records"]
    if type(rows) is not list or len(rows) > MAX_RECORDS:
        raise SourceJobHistoryError("invalid source history retention")
    try:
        if len(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")) > MAX_BYTES:
            raise SourceJobHistoryError("source history too large")
    except (TypeError, ValueError, RecursionError):
        raise SourceJobHistoryError("invalid source history document") from None
    result: OrderedDict[str, dict] = OrderedDict()
    for item in rows:
        checked = sanitized(item)
        key = checked["operation_id"]
        if key in result:
            raise SourceJobHistoryError("duplicate source job identifier")
        result[key] = checked
    return result


class SourceJobHistory:
    """Persist bounded terminal metadata without persisting reusable preview results."""

    def __init__(self, store: AsyncStore):
        if not callable(getattr(store, "async_load", None)) or not callable(
            getattr(store, "async_save", None)
        ):
            raise SourceJobHistoryError("source history store unavailable")
        self._store = store
        self._lock = asyncio.Lock()
        self._records: OrderedDict[str, dict] = OrderedDict()
        self._loaded = False

    def _document(self, rows: OrderedDict[str, dict]) -> dict:
        return {"schema": SCHEMA, "records": list(rows.values())}

    async def load(self) -> None:
        async with self._lock:
            if self._loaded:
                raise SourceJobHistoryError("source history already loaded")
            try:
                raw = await self._store.async_load()
            except Exception:
                raise SourceJobHistoryError("source history unavailable") from None
            if raw is None:
                self._loaded = True
                return
            records = _validated_document(raw)
            dirty = False
            # A reboot/unload is NOT a successful or resumable operation.
            for row in records.values():
                if row["status"] == "queued":
                    row.update(status="interrupted", finished_at=utc_now(),
                               reason="interrupted")
                    dirty = True
            if dirty:
                try:
                    await self._store.async_save(self._document(records))
                except Exception:
                    raise SourceJobHistoryError("source history recovery failed") from None
            self._records = records
            self._loaded = True

    async def _save(self, updated: OrderedDict[str, dict]) -> None:
        doc = self._document(updated)
        _validated_document(doc)
        try:
            await self._store.async_save(doc)
        except Exception:
            raise SourceJobHistoryError("source history write failed") from None
        self._records = updated

    async def queued(self, operation_id: str) -> None:
        if type(operation_id) is not str or not ID.fullmatch(operation_id):
            raise SourceJobHistoryError("invalid source operation id")
        async with self._lock:
            if not self._loaded or operation_id in self._records:
                raise SourceJobHistoryError("source history not writable")
            updated = self._records.copy()
            updated[operation_id] = sanitized({
                "operation_id": operation_id, "status": "queued",
                "created_at": utc_now(), "finished_at": None,
                "reason": None, "installation_enabled": False,
                "resume_allowed": False, "source_preview_saved": False,
            })
            while len(updated) > MAX_RECORDS:
                updated.popitem(last=False)
            await self._save(updated)

    async def terminal(self, operation_id: str, status: str, *, reason: str | None = None) -> None:
        if type(operation_id) is not str or not ID.fullmatch(operation_id):
            raise SourceJobHistoryError("invalid source operation id")
        if status not in TERMINAL or type(status) is not str:
            raise SourceJobHistoryError("invalid terminal source state")
        async with self._lock:
            row = self._records.get(operation_id)
            if not self._loaded or row is None or row["status"] != "queued":
                raise SourceJobHistoryError("source history terminal conflict")
            updated = self._records.copy()
            updated[operation_id] = sanitized({
                **row, "status": status, "reason": reason,
                "finished_at": utc_now(),
            })
            await self._save(updated)

    async def list(self) -> list[dict]:
        async with self._lock:
            if not self._loaded:
                raise SourceJobHistoryError("source history unavailable")
            return [dict(row) for row in reversed(self._records.values())]
