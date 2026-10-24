"""V2-only complete backup integrity contract (pure, no filesystem writes).

Creating real backups, deletion, and restore remain unavailable. The future
transaction layer must stage independently and re-read every archived byte
against these hashes before claiming a backup verified and restorable.
"""
from __future__ import annotations

import hashlib
import re

from .source_preflight import PreflightError, safe_path, target_path

SCHEMA = "dra-v2-dev-complete-backup.v1"
MAX_FILES = 1000
MAX_BYTES = 32 * 1024 * 1024
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
IDENTITY = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


class BackupIntegrityError(ValueError):
    """Incomplete, conflicting, unsafe or corrupted backup content."""


def _root_list(values: object) -> list[str]:
    if type(values) is not list or not values or len(values) > 12:
        raise BackupIntegrityError("invalid backup roots")
    try:
        roots = [target_path(value) for value in values]
    except PreflightError:
        raise BackupIntegrityError("invalid backup target") from None
    if len(set(r.casefold() for r in roots)) != len(roots):
        raise BackupIntegrityError("duplicate backup target")
    return sorted(roots)


def _files(roots: list[str], blobs: object) -> list[dict]:
    if type(blobs) is not dict or len(blobs) > MAX_FILES:
        raise BackupIntegrityError("invalid backup payload")
    files: list[dict] = []
    total = 0
    lowered: set[str] = set()
    for path, raw in blobs.items():
        try:
            candidate = safe_path(path)
        except PreflightError:
            raise BackupIntegrityError("invalid backup file") from None
        if not any(candidate.startswith(root + "/") for root in roots):
            raise BackupIntegrityError("file outside managed target")
        if candidate.casefold() in lowered:
            raise BackupIntegrityError("duplicate backup file")
        lowered.add(candidate.casefold())
        if type(raw) is not bytes:
            raise BackupIntegrityError("backup must contain immutable file bytes")
        total += len(raw)
        if total > MAX_BYTES:
            raise BackupIntegrityError("backup exceeds byte budget")
        files.append({
            "path": candidate, "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    return sorted(files, key=lambda row: row["path"])


def create_complete_manifest(project_id: str, roots: list[str],
                             snapshot_files: dict[str, bytes]) -> dict:
    """Create deterministic metadata only; does NOT back up a single byte."""
    if type(project_id) is not str or not IDENTITY.fullmatch(project_id):
        raise BackupIntegrityError("invalid backup project identity")
    checked_roots = _root_list(roots)
    entries = _files(checked_roots, snapshot_files)
    # Empty backups are valid only if the managed directories are truly empty;
    # future I/O layer must prove that at transaction time.
    return {
        "schema": SCHEMA, "project_id": project_id,
        "target_roots": checked_roots, "files": entries,
        "total_bytes": sum(item["size"] for item in entries),
        "complete_inventory_required": True,
    }


def verify_complete_manifest(manifest: object,
                             archived_files: dict[str, bytes]) -> dict:
    """Independently verify all archived bytes and exact path coverage.

    No booleans from stored metadata can substitute for this byte validation.
    """
    if type(manifest) is not dict or set(manifest) != {
        "schema", "project_id", "target_roots", "files",
        "total_bytes", "complete_inventory_required",
    }:
        raise BackupIntegrityError("invalid backup record")
    if manifest["schema"] != SCHEMA or manifest["complete_inventory_required"] is not True:
        raise BackupIntegrityError("unverified backup record")
    if type(manifest["project_id"]) is not str or not IDENTITY.fullmatch(manifest["project_id"]):
        raise BackupIntegrityError("invalid project identity")
    roots = _root_list(manifest["target_roots"])
    if roots != manifest["target_roots"]:
        raise BackupIntegrityError("noncanonical target list")
    entries = manifest["files"]
    if type(entries) is not list or len(entries) > MAX_FILES:
        raise BackupIntegrityError("invalid backup file list")
    if type(manifest["total_bytes"]) is not int or not 0 <= manifest["total_bytes"] <= MAX_BYTES:
        raise BackupIntegrityError("invalid backup byte count")
    # Independently hash the entire set of supplied archived bytes.
    expected = _files(roots, archived_files)
    if expected != entries or sum(item["size"] for item in expected) != manifest["total_bytes"]:
        raise BackupIntegrityError("backup incomplete or hash mismatch")
    return {
        "verified": True, "project_id": manifest["project_id"],
        "file_count": len(entries),
        "total_bytes": manifest["total_bytes"],
        "target_roots": list(roots),
        "restoration_enabled": False,
        "mutation_enabled": False,
    }
