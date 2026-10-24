"""Generic version/build marker extraction for regression detection."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import PurePosixPath
import re

MAX_VERSION_MARKER_SCAN_BYTES = 512 * 1024
_TEXT_SUFFIXES = frozenset({".js", ".mjs", ".cjs", ".ts", ".py", ".json"})

_ASSIGNMENT = re.compile(
    r"""(?mx)
    ^\s*
    (?:(?:const|let|var)\s+)?
    (?P<name>[A-Z][A-Z0-9_]*(?:VERSION|REV|REVISION))
    \s*(?::[^=\n]+)?
    =\s*
    ["']
    (?P<value>[^"'\r\n]{1,64})
    ["']
    """
)


@dataclass(frozen=True, slots=True)
class VersionMarker:
    """One non-secret version/build marker found in managed project content."""

    group_id: str
    relative_path: str
    name: str
    value: str
    rank: int


def _rank(name: str) -> int:
    if "BUILD_VERSION" in name:
        return 120
    if name.endswith("_VERSION") or name == "VERSION":
        return 100
    if "BUILD_REV" in name or "LOADER_REV" in name:
        return 90
    if name.endswith("_REVISION"):
        return 80
    if name.endswith("_REV"):
        return 70
    if name == "manifest.version":
        return 50
    return 10


def should_scan_version_markers(
    relative_path: str,
    advertised_size: int | None = None,
) -> bool:
    """Return whether a managed file can contain a bounded version marker scan."""
    path = PurePosixPath(relative_path)
    if path.suffix.casefold() not in _TEXT_SUFFIXES:
        return False
    return advertised_size is None or advertised_size <= MAX_VERSION_MARKER_SCAN_BYTES


def extract_version_markers(
    group_id: str,
    relative_path: str,
    raw: bytes,
) -> tuple[VersionMarker, ...]:
    """Extract bounded declarative version/build markers from one managed file."""
    if len(raw) > MAX_VERSION_MARKER_SCAN_BYTES:
        return ()

    path = PurePosixPath(relative_path)
    if path.suffix.casefold() not in _TEXT_SUFFIXES:
        return ()

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ()

    markers: list[VersionMarker] = []

    if path.name.casefold() == "manifest.json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            version = payload.get("version")
            if isinstance(version, str) and 0 < len(version) <= 64:
                markers.append(
                    VersionMarker(
                        group_id=group_id,
                        relative_path=relative_path,
                        name="manifest.version",
                        value=version.strip(),
                        rank=_rank("manifest.version"),
                    )
                )

    for match in _ASSIGNMENT.finditer(text):
        name = match.group("name")
        value = match.group("value").strip()
        if not value:
            continue
        markers.append(
            VersionMarker(
                group_id=group_id,
                relative_path=relative_path,
                name=name,
                value=value,
                rank=_rank(name),
            )
        )

    dedup: dict[tuple[str, str, str], VersionMarker] = {}
    for marker in markers:
        dedup[(marker.relative_path, marker.name, marker.value)] = marker
    return tuple(dedup.values())
