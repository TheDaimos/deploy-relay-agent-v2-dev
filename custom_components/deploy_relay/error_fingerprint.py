"""Stable error fingerprints for Deploy Relay diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import traceback
from typing import Any

_TRACE_FRAME_RE = re.compile(
    r'File ["\'](?P<file>.+?)["\'], line \d+, in (?P<function>[^\n]+)'
)


@dataclass(frozen=True, slots=True)
class ErrorFingerprint:
    """Stable exact and family identifiers for one error."""

    exact: str
    family: str
    exception_type: str
    stack_signature: tuple[str, ...]


def _digest(prefix: str, parts: list[str]) -> str:
    canonical = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}-{sha256(canonical).hexdigest()[:20]}"


def _normalize_frame(filename: str, function: str) -> str:
    """Normalize a traceback frame without line numbers or machine paths."""
    return f"{Path(filename).name}:{function.strip()}"


def _stack_from_exception(err: BaseException) -> tuple[str, ...]:
    if err.__traceback__ is None:
        return ("<no-traceback>",)

    frames = traceback.extract_tb(err.__traceback__)
    normalized = tuple(
        _normalize_frame(frame.filename, frame.name)
        for frame in frames
    )
    return normalized or ("<no-traceback>",)


def _stack_from_text(value: str | None) -> tuple[str, ...]:
    if not value:
        return ("<no-traceback>",)

    frames = tuple(
        _normalize_frame(match.group("file"), match.group("function"))
        for match in _TRACE_FRAME_RE.finditer(value)
    )
    return frames or ("<no-traceback>",)


def build_error_fingerprint(
    *,
    exception_type: str,
    component: str | None,
    operation: str | None,
    phase: str | None,
    stack_signature: tuple[str, ...],
) -> ErrorFingerprint:
    """Build stable exact/family fingerprints from non-secret structure."""
    family_parts = [
        exception_type or "Exception",
        component or "-",
        operation or "-",
        phase or "-",
    ]
    exact_parts = [*family_parts, *stack_signature]
    return ErrorFingerprint(
        exact=_digest("err", exact_parts),
        family=_digest("fam", family_parts),
        exception_type=exception_type or "Exception",
        stack_signature=stack_signature,
    )


def fingerprint_exception(
    err: BaseException,
    *,
    component: str | None,
    operation: str | None,
    phase: str | None,
) -> ErrorFingerprint:
    """Fingerprint a live exception without hashing its message."""
    return build_error_fingerprint(
        exception_type=type(err).__name__,
        component=component,
        operation=operation,
        phase=phase,
        stack_signature=_stack_from_exception(err),
    )


def fingerprint_serialized_event(event: dict[str, Any]) -> ErrorFingerprint | None:
    """Backfill a fingerprint for an older serialized ERROR event."""
    exception = event.get("exception")
    if not isinstance(exception, dict):
        return None

    exception_type = exception.get("type")
    if not isinstance(exception_type, str) or not exception_type:
        return None

    traceback_text = exception.get("traceback")
    return build_error_fingerprint(
        exception_type=exception_type,
        component=(
            str(event["component"])
            if event.get("component") is not None
            else None
        ),
        operation=(
            str(event["operation"])
            if event.get("operation") is not None
            else None
        ),
        phase=(
            str(event["phase"])
            if event.get("phase") is not None
            else None
        ),
        stack_signature=_stack_from_text(
            traceback_text if isinstance(traceback_text, str) else None
        ),
    )
