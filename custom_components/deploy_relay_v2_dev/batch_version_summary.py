"""Read-only version provenance for an immutable HA batch preparation.

No additional Git request is performed: remote markers are already included in
the verified V1 source inventory. Local markers are read only when bytes still
match the exact local SHA256 from that same V1 preview. Unknown is not success.
"""
from __future__ import annotations

import asyncio
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
from stat import S_ISREG

from .v1_engine.preview import PreviewError, _safe_target_path
from .v1_engine.version_markers import (
    MAX_VERSION_MARKER_SCAN_BYTES, VersionMarker, extract_version_markers,
)

_APPROVED_FILES = frozenset({
    "build_info.py", "version.py", "const.py", "__init__.py", "manifest.json",
})
_MAX_CANDIDATES = 12


def _read_verified_local(config_root: Path, target: str, expected_sha: str) -> bytes | None:
    """Bounded no-follow file read; never trust a target changed since preview."""
    try:
        path = _safe_target_path(config_root, target)
        if not path.exists() or path.is_symlink():
            return None
        before = path.lstat()
        if not S_ISREG(before.st_mode) or before.st_nlink != 1 or (
            before.st_size > MAX_VERSION_MARKER_SCAN_BYTES
        ):
            return None
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            after = os.fstat(fd)
            if (not S_ISREG(after.st_mode) or after.st_nlink != 1
                    or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                    or after.st_size > MAX_VERSION_MARKER_SCAN_BYTES):
                return None
            with os.fdopen(fd, "rb", closefd=False) as handle:
                data = handle.read(MAX_VERSION_MARKER_SCAN_BYTES + 1)
        finally:
            os.close(fd)
        return data if sha256(data).hexdigest() == expected_sha else None
    except (OSError, ValueError, PreviewError):
        return None


def _best(marker_values: list[VersionMarker]) -> VersionMarker | None:
    if not marker_values:
        return None
    top = max(row.rank for row in marker_values)
    strongest = [row for row in marker_values if row.rank == top]
    # Contradictory markers of equal authority are not safe to assert.
    if len({row.value for row in strongest}) > 1:
        return None
    return sorted(strongest, key=lambda x: (x.relative_path, x.name))[0]


async def prepared_version_summary(prepared, *, config_root: Path) -> dict[str, str | None]:
    """A display-only, non-secret current/new version pair.

    Never interprets source revisions as installed runtime versions and never
    authorizes writing. Missing or contradictory markers are reported as null.
    """
    inventory = prepared.inventory
    preview = prepared.preview
    manifest = prepared.manifest
    groups = {row.id: row.target for row in manifest.groups}
    files = {(row.group_id, row.source_path): row for row in preview.files
             if row.source_path is not None}
    candidates = [marker for marker in inventory.version_markers
                  if PurePosixPath(marker.relative_path).name.casefold() in _APPROVED_FILES]
    # Prefer matching the same marker in both versions, not two unrelated apps.
    candidates.sort(key=lambda x: (-x.rank, x.relative_path, x.name))
    source_marker = _best(candidates)
    source_ambiguous = bool(candidates) and source_marker is None
    paired: list[tuple[VersionMarker, VersionMarker]] = []
    inspected: set[tuple[str, str]] = set()
    for marker in candidates[:_MAX_CANDIDATES]:
        group_target = groups.get(marker.group_id)
        if group_target is None:
            continue
        target = f"{group_target}/{marker.relative_path}"
        entry = next((f for f in preview.files
                      if f.group_id == marker.group_id and f.target_path == target), None)
        if entry is None or not entry.target_sha256:
            continue
        key = (marker.group_id, marker.relative_path)
        if key in inspected:
            continue
        inspected.add(key)
        content = await asyncio.to_thread(
            _read_verified_local, config_root, target, entry.target_sha256
        )
        if content is None:
            continue
        local = extract_version_markers(marker.group_id, marker.relative_path, content)
        for remote_marker in (m for m in candidates if (
            m.group_id == marker.group_id and m.relative_path == marker.relative_path
        )):
            for local_marker in local:
                if local_marker.name == remote_marker.name:
                    paired.append((remote_marker, local_marker))
    if paired and not source_ambiguous:
        rank = max(remote.rank for remote, _ in paired)
        leaders = [(remote, local) for remote, local in paired if remote.rank == rank]
        if (len({remote.value for remote, _ in leaders}) == 1 and
                len({local.value for _, local in leaders}) == 1):
            remote, local = sorted(
                leaders, key=lambda pair: (pair[0].relative_path, pair[0].name)
            )[0]
            return {"installed_version": local.value, "new_version": remote.value,
                    "version_marker": remote.name, "version_status": "verified_pair"}
    return {"installed_version": None,
            "new_version": source_marker.value if source_marker else None,
            "version_marker": source_marker.name if source_marker else None,
            "version_status": "source_only" if source_marker else "unknown"}
