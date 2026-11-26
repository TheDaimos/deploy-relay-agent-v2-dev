"""Deployment transaction primitives."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
import re

_SAFE = re.compile(r"[^a-z0-9_]+")


class TransactionState(StrEnum):
    """Canonical transaction states."""

    IDLE = "idle"
    CHECKING = "checking"
    AVAILABLE = "available"
    PLANNING = "planning"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    STAGING = "staging"
    BACKING_UP = "backing_up"
    INSTALLING = "installing"
    VERIFYING_INSTALL = "verifying_install"
    SUCCESS = "success"
    FAILED_NO_CHANGE = "failed_no_change"
    ROLLED_BACK = "rolled_back"
    RECOVERY_REQUIRED = "recovery_required"


def _slug(value: str, *, limit: int) -> str:
    value = _SAFE.sub("_", value.casefold()).strip("_")
    return (value or "unknown")[:limit]


def make_transaction_id(
    project_id: str,
    source_commit: str,
    *,
    now: datetime | None = None,
) -> str:
    """Create a bounded, filesystem-safe transaction id."""
    timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    project = _slug(project_id, limit=40)
    commit = _slug(source_commit, limit=12)
    return f"dra-{stamp}-{project}-{commit}"
