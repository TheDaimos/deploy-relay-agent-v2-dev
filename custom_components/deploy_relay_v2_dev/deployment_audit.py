"""Bounded, sanitized in-memory audit stream for V2-owned deployments.

No tokens, file paths, raw exception messages, or payloads. Events are HA-owned
and deliberately non-persistent; V1 transaction journals remain authoritative.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import re

_SAFE_ID = re.compile(r"[a-zA-Z0-9_-]{1,128}\Z")
_ALLOWED = frozenset({"queued", "running", "staging", "backup", "install",
                     "verify_install", "rollback", "success", "failed",
                     "recovery_required", "interrupted"})
_MAX_EVENTS = 256


class DeploymentAudit:
    def __init__(self) -> None:
        self._events: deque[dict[str, object]] = deque(maxlen=_MAX_EVENTS)
        self._seq = 0

    def record(self, *, operation_id: str, project_key: str,
               stage: str, status: str = "running") -> None:
        if (not isinstance(operation_id, str) or not _SAFE_ID.fullmatch(operation_id)
            or not isinstance(project_key, str) or not _SAFE_ID.fullmatch(project_key)
            or stage not in _ALLOWED or status not in _ALLOWED):
            return
        self._seq += 1
        self._events.append({
            "sequence": self._seq,
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "operation_id": operation_id,
            "project_key": project_key,
            "stage": stage,
            "status": status,
        })

    def entries(self) -> list[dict[str, object]]:
        return list(reversed(self._events))
