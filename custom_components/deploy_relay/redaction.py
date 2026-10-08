"""Central secret redaction for Deploy Relay diagnostics."""

from __future__ import annotations

import re
from typing import Any, Iterable

_REDACTED = "<redacted>"

_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "cookie",
    "credential",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
)

_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[^\s,;]+"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]+\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]+\b"),
)


def _is_sensitive_key(key: object) -> bool:
    """Return whether a mapping key names secret material."""
    normalized = str(key).casefold().replace("-", "_").replace(" ", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def redact_text(value: str, secrets: Iterable[str] = ()) -> str:
    """Redact known token formats and explicitly registered secrets."""
    result = value

    for secret in secrets:
        if secret and len(secret) >= 6:
            result = result.replace(secret, _REDACTED)

    for pattern in _PATTERNS:
        result = pattern.sub(_REDACTED, result)

    return result


def redact_value(value: Any, secrets: Iterable[str] = ()) -> Any:
    """Recursively redact secret values while preserving useful structure."""
    secret_values = tuple(secret for secret in secrets if secret)

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key):
                redacted[key_text] = _REDACTED if item not in (None, "", False) else item
            else:
                redacted[key_text] = redact_value(item, secret_values)
        return redacted

    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact_value(item, secret_values) for item in value]

    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"

    if isinstance(value, str):
        return redact_text(value, secret_values)

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return redact_text(repr(value), secret_values)
