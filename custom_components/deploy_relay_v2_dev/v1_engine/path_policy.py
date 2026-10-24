"""Local path-policy enforcement for Deploy Relay."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import re

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")

_DENIED_FIRST_COMPONENTS = frozenset({
    ".storage",
    ".cloud",
})
_DENIED_BASENAMES = frozenset({
    "secrets.yaml",
    "home-assistant_v2.db",
    "home-assistant_v2.db-shm",
    "home-assistant_v2.db-wal",
    "auth",
    "auth_provider.homeassistant",
})


class PathPolicyError(ValueError):
    """Raised when a source or target path violates local policy."""


def normalize_relative_path(value: str) -> PurePosixPath:
    """Normalize and validate a manifest/archive relative path."""
    if not isinstance(value, str) or not value:
        raise PathPolicyError("path must be a non-empty string")
    if "\x00" in value:
        raise PathPolicyError("NUL bytes are forbidden")
    if _DRIVE_PREFIX.match(value):
        raise PathPolicyError("Windows drive prefixes are forbidden")

    normalized_text = value.replace("\\", "/")
    path = PurePosixPath(normalized_text)
    if path.is_absolute():
        raise PathPolicyError("absolute paths are forbidden")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise PathPolicyError("empty/dot/traversal path components are forbidden")
    if PureWindowsPath(value).is_absolute():
        raise PathPolicyError("absolute Windows paths are forbidden")
    return path


def validate_target_path(value: str) -> PurePosixPath:
    """Validate a target relative to the approved Home Assistant config root."""
    path = normalize_relative_path(value)
    lowered = tuple(part.casefold() for part in path.parts)

    if lowered[0] in _DENIED_FIRST_COMPONENTS:
        raise PathPolicyError("target enters a denied Home Assistant internal area")
    if any(part in _DENIED_FIRST_COMPONENTS for part in lowered):
        raise PathPolicyError("target contains a denied Home Assistant internal area")
    if lowered[-1] in _DENIED_BASENAMES:
        raise PathPolicyError("target is a denied sensitive Home Assistant file")
    return path


def resolve_under_root(root: Path, relative: str, *, target: bool = False) -> Path:
    """Resolve a relative path below root and prove containment."""
    clean = validate_target_path(relative) if target else normalize_relative_path(relative)
    root_resolved = root.resolve()
    candidate = (root_resolved / Path(*clean.parts)).resolve()

    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise PathPolicyError("resolved path escapes approved root")
    return candidate
