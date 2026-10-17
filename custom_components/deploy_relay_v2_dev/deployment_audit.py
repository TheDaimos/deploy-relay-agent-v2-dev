"""Bounded, sanitized in-memory audit stream for V2-owned deployments.

No tokens, file paths, raw exception messages, or payloads. Events are HA-owned
and deliberately non-persistent; V1 transaction journals remain authoritative.
"""
from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
import json
import re
from time import monotonic

_SAFE_ID = re.compile(r"[a-zA-Z0-9_-]{1,128}\Z")
_ALLOWED = frozenset({"queued", "running", "staging", "backup", "install",
                     "verify_install", "rollback", "success", "failed",
                     "recovery_required", "interrupted"})
_MAX_EVENTS = 256
_MAX_BYTES = 72000
_SCHEMA = "dra-v2-deployment-audit.v1"


class DeploymentAudit:
    def __init__(self, store=None) -> None:
        self._store = store
        self._save_lock = asyncio.Lock()
        self._events: deque[dict[str, object]] = deque(maxlen=_MAX_EVENTS)
        self._seq = 0
        self._started: dict[str, float] = {}

    async def load(self) -> None:
        if self._store is None:
            return
        try:
            document = await self._store.async_load()
        except Exception:
            raise ValueError("audit history unavailable") from None
        if document is None:
            return
        if (type(document) is not dict or set(document) != {"schema", "records"}
            or document["schema"] != _SCHEMA or type(document["records"]) is not list
            or len(document["records"]) > _MAX_EVENTS):
            raise ValueError("invalid audit history")
        if len(json.dumps(document, separators=(",", ":"))) > _MAX_BYTES:
            raise ValueError("audit history exceeds size limit")
        last_seq = 0
        for row in document["records"]:
            if (type(row) is not dict or set(row) != {"sequence", "captured_at",
                    "operation_id", "project_key", "stage", "status", "elapsed_ms"}
                or type(row["sequence"]) is not int or row["sequence"] <= last_seq
                or type(row["captured_at"]) is not str or not row["captured_at"].endswith("Z")
                or type(row["operation_id"]) is not str or not _SAFE_ID.fullmatch(row["operation_id"])
                or type(row["project_key"]) is not str or not _SAFE_ID.fullmatch(row["project_key"])
                or row["stage"] not in _ALLOWED or row["status"] not in _ALLOWED
                or type(row["elapsed_ms"]) is not int or not 0 <= row["elapsed_ms"] <= 86400000):
                raise ValueError("invalid audit event")
            try:
                parsed = datetime.fromisoformat(row["captured_at"].replace("Z", "+00:00"))
                if parsed.utcoffset() != timezone.utc.utcoffset(None):
                    raise ValueError("invalid timezone")
            except ValueError:
                raise ValueError("invalid audit timestamp") from None
            last_seq = row["sequence"]
        self._events = deque((dict(row) for row in document["records"]), maxlen=_MAX_EVENTS)
        self._seq = last_seq

    async def save(self) -> None:
        if self._store is None:
            return
        # Independent deployments can finish together; serialize snapshots.
        async with self._save_lock:
            document = {"schema": _SCHEMA, "records": list(self._events)}
            if len(json.dumps(document, separators=(",", ":"))) > _MAX_BYTES:
                raise ValueError("audit history exceeds size limit")
            try:
                await self._store.async_save(document)
            except Exception:
                raise ValueError("audit history write failed") from None

    def record(self, *, operation_id: str, project_key: str,
               stage: str, status: str = "running") -> None:
        if (not isinstance(operation_id, str) or not _SAFE_ID.fullmatch(operation_id)
            or not isinstance(project_key, str) or not _SAFE_ID.fullmatch(project_key)
            or stage not in _ALLOWED or status not in _ALLOWED):
            return
        now = monotonic()
        if stage == "queued" or operation_id not in self._started:
            self._started[operation_id] = now
        elapsed_ms = max(0, min(86400000, int((now - self._started[operation_id]) * 1000)))
        self._seq += 1
        self._events.append({
            "sequence": self._seq,
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "operation_id": operation_id,
            "project_key": project_key,
            "stage": stage,
            "status": status,
            "elapsed_ms": elapsed_ms,
        })
        if status in {"success", "failed", "recovery_required", "interrupted"}:
            self._started.pop(operation_id, None)

    def entries(self) -> list[dict[str, object]]:
        return list(reversed(self._events))
