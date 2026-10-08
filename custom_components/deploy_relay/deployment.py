"""Safe staging, backup, install and rollback engine for Deploy Relay."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
from uuid import uuid4
from typing import Any

from aiohttp import ClientSession

from .github_client import GitHubClient
from .integrity import sha256_file
from .lifecycle_policy import LifecycleAssessment, assess_lifecycle, lifecycle_for_target_paths
from .manifest import DeploymentManifest
from .path_policy import normalize_relative_path, validate_target_path
from .planner import build_plan
from .preview import (
    PreviewFile,
    PreviewOperation,
    PreviewResult,
    hash_existing_target_file,
    iter_target_directory_files,
    safe_target_path,
)
from .source_inventory import SourceInventory
from .transaction import TransactionState, make_transaction_id


class DeploymentError(RuntimeError):
    """A deployment could not be completed safely."""


class RecoveryRequiredError(DeploymentError):
    """Deployment failed and automatic rollback could not be completed."""


ProgressCallback = Callable[[str, dict[str, Any]], Awaitable[None]]
BlockingExecutor = Callable[[Callable[[], Any]], Awaitable[Any]]

_MAX_BACKUP_ENTRIES = 20000
_MAX_BACKUP_METADATA_BYTES = 32 * 1024 * 1024
_MAX_RESTORE_SNAPSHOT_BYTES = 1024 * 1024 * 1024


async def _run_blocking(
    executor: BlockingExecutor | None,
    func: Callable[..., Any],
    /,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run local filesystem/CPU work outside Home Assistant's event loop."""
    job = partial(func, *args, **kwargs)
    if executor is not None:
        return await executor(job)
    return await asyncio.to_thread(job)


@dataclass(frozen=True, slots=True)
class BackupRestoreResult:
    """Final secret-free result of one explicit backup restoration."""

    transaction_id: str
    restored_backup_id: str
    safety_backup_path: str
    journal_path: str
    lifecycle: str
    restart_required: bool
    changed_files: int


@dataclass(frozen=True, slots=True)
class DeploymentExecutionResult:
    """Final secret-free deployment result."""

    transaction_id: str
    state: TransactionState
    backup_path: str | None
    journal_path: str
    lifecycle: str
    restart_required: bool
    changed_files: int
    error: str | None = None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _ensure_config_root(config_root: Path) -> Path:
    if config_root.is_symlink():
        raise DeploymentError("config root must not be a symlink")
    if not config_root.exists() or not config_root.is_dir():
        raise DeploymentError("config root must be an existing directory")
    return config_root.resolve()


def _ensure_owned_dir(config_root: Path, *parts: str) -> Path:
    """Create a Deploy Relay-owned directory while rejecting link traversal."""
    root = _ensure_config_root(config_root)
    current = root
    for part in ("deploy_relay", *parts):
        current = current / part
        if current.exists() and current.is_symlink():
            raise DeploymentError(f"Deploy Relay data path contains symlink: {current}")
        if current.exists() and not current.is_dir():
            raise DeploymentError(f"Deploy Relay data path is not a directory: {current}")
        current.mkdir(exist_ok=True)
        resolved = current.resolve()
        if resolved != root and root not in resolved.parents:
            raise DeploymentError("Deploy Relay data path escapes config root")
    return current


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    if tmp.exists():
        tmp.unlink()
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    with tmp.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        tmp.chmod(0o600)
    except OSError:
        pass
    os.replace(tmp, path)


def _copy_file_with_hash(
    source: Path,
    destination: Path,
    *,
    chunk_size: int = 1024 * 1024,
) -> tuple[str, int]:
    """Copy a local file while hashing the source stream once."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256()
    total = 0
    with source.open("rb") as src, destination.open("xb") as dst:
        while chunk := src.read(chunk_size):
            digest.update(chunk)
            total += len(chunk)
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    shutil.copystat(source, destination, follow_symlinks=False)
    return digest.hexdigest(), total


def _journal_payload(
    *,
    transaction_id: str,
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    preview_counts: dict[str, int],
    lifecycle: LifecycleAssessment,
    state: TransactionState,
    created_at: str,
    backup_path: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": "deploy-relay.transaction.v1",
        "transaction_id": transaction_id,
        "state": state.value,
        "created_at": created_at,
        "updated_at": _utc_now(),
        "project_id": manifest.project_id,
        "repository": manifest.repository,
        "source_ref": inventory.source_ref,
        "source_commit": inventory.source_commit,
        "lifecycle": lifecycle.effective.value,
        "lifecycle_declared": lifecycle.declared.value,
        "lifecycle_reason": lifecycle.reason,
        "preview": dict(preview_counts),
        "backup_path": backup_path,
        "error": error,
    }


def _stage_path(staging_root: Path, group_id: str, relative_path: str) -> Path:
    relative = normalize_relative_path(relative_path)
    return staging_root / "files" / group_id / Path(*relative.parts)


async def _progress(
    callback: ProgressCallback | None,
    phase: str,
    details: dict[str, Any],
) -> None:
    if callback is not None:
        await callback(phase, details)


def _prepare_staging_root(config_root: Path, transaction_id: str) -> Path:
    staging_parent = _ensure_owned_dir(config_root, "staging")
    staging_root = staging_parent / transaction_id
    if staging_root.exists():
        raise DeploymentError("transaction staging directory already exists")
    staging_root.mkdir()
    return staging_root


def _open_stage_part(destination: Path) -> tuple[Path, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(f".{destination.name}.part")
    return part, part.open("xb")


def _flush_fsync_close(handle: Any) -> None:
    handle.flush()
    os.fsync(handle.fileno())
    handle.close()


def _close_quietly(handle: Any) -> None:
    try:
        handle.close()
    except OSError:
        pass


def _unlink_if_exists(path: Path) -> None:
    path.unlink(missing_ok=True)


def _finalize_staged_file(
    part: Path,
    destination: Path,
    *,
    expected_sha256: str,
    expected_size: int,
) -> None:
    if part.stat().st_size != expected_size:
        raise DeploymentError(f"staged file size changed: {destination}")
    os.replace(part, destination)
    if sha256_file(destination) != expected_sha256:
        raise DeploymentError(f"staged file verification failed: {destination}")


async def async_materialize_staging(
    session: ClientSession,
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    *,
    token: str | None,
    config_root: Path,
    transaction_id: str,
    progress: ProgressCallback | None = None,
    blocking_executor: BlockingExecutor | None = None,
) -> Path:
    """Stream exact frozen source bytes into a unique verified staging tree."""
    if inventory.project_id != manifest.project_id:
        raise DeploymentError("source inventory project does not match manifest")
    if inventory.repository.casefold() != manifest.repository.casefold():
        raise DeploymentError("source inventory repository does not match manifest")

    staging_root = await _run_blocking(
        blocking_executor,
        _prepare_staging_root,
        config_root,
        transaction_id,
    )

    client = GitHubClient(session, token)
    total_files = 0
    total_bytes = 0

    await _progress(
        progress,
        "staging",
        {
            "transaction_id": transaction_id,
            "source_commit": inventory.source_commit,
            "file_count": inventory.total_files,
            "total_bytes": inventory.total_bytes,
        },
    )

    try:
        for group in inventory.groups:
            for item in group.files:
                destination = _stage_path(
                    staging_root,
                    group.group_id,
                    item.relative_path,
                )
                part, handle = await _run_blocking(
                    blocking_executor,
                    _open_stage_part,
                    destination,
                )
                digest = sha256()
                actual_size = 0
                try:
                    async for chunk in client.async_iter_file_bytes(
                        inventory.repository,
                        item.source_path,
                        ref=inventory.source_commit,
                        max_bytes=item.size,
                    ):
                        digest.update(chunk)
                        actual_size += len(chunk)
                        await _run_blocking(
                            blocking_executor,
                            handle.write,
                            chunk,
                        )
                    await _run_blocking(
                        blocking_executor,
                        _flush_fsync_close,
                        handle,
                    )
                    handle = None
                finally:
                    if handle is not None:
                        await _run_blocking(
                            blocking_executor,
                            _close_quietly,
                            handle,
                        )

                if actual_size != item.size or digest.hexdigest() != item.sha256:
                    await _run_blocking(
                        blocking_executor,
                        _unlink_if_exists,
                        part,
                    )
                    raise DeploymentError(
                        f"staged source integrity mismatch for {item.source_path!r}"
                    )

                await _run_blocking(
                    blocking_executor,
                    _finalize_staged_file,
                    part,
                    destination,
                    expected_sha256=item.sha256,
                    expected_size=item.size,
                )

                total_files += 1
                total_bytes += actual_size

        if total_files != inventory.total_files or total_bytes != inventory.total_bytes:
            raise DeploymentError("staging totals do not match frozen source inventory")

        await _run_blocking(
            blocking_executor,
            _write_json_atomic,
            staging_root / "staging.json",
            {
                "schema": "deploy-relay.staging.v1",
                "transaction_id": transaction_id,
                "project_id": inventory.project_id,
                "repository": inventory.repository,
                "source_ref": inventory.source_ref,
                "source_commit": inventory.source_commit,
                "file_count": total_files,
                "total_bytes": total_bytes,
            },
        )
        return staging_root
    except Exception:
        await _run_blocking(
            blocking_executor,
            shutil.rmtree,
            staging_root,
            ignore_errors=True,
        )
        raise


def _create_backup(
    manifest: DeploymentManifest,
    preview: PreviewResult,
    *,
    config_root: Path,
    transaction_id: str,
    context: dict[str, Any] | None = None,
) -> Path | None:
    """Create a verified pre-mutation restore point.

    replace_directory groups are captured as complete managed-state snapshots,
    so any retained restore point can later be restored independently. Other
    group modes retain the legacy per-path rollback representation and remain
    available for automatic transaction rollback only.
    """

    if not any(
        item.operation is not PreviewOperation.UNCHANGED
        for item in preview.files
    ):
        return None

    backup_parent = _ensure_owned_dir(config_root, "backups", manifest.project_id)
    backup_root = backup_parent / transaction_id
    if backup_root.exists():
        raise DeploymentError("transaction backup directory already exists")
    backup_root.mkdir()

    group_modes = {group.id: group.mode for group in manifest.groups}
    snapshot_complete = all(
        group.mode == "replace_directory"
        for group in manifest.groups
    )
    groups_payload = [
        {
            "id": group.id,
            "target": group.target,
            "mode": group.mode,
            "files": list(group.files),
        }
        for group in manifest.groups
    ]

    entries: list[dict[str, Any]] = []
    total_backup_bytes = 0
    try:
        for item in preview.files:
            mode = group_modes.get(item.group_id)
            if mode is None:
                raise DeploymentError("preview contains unknown backup group")

            if item.target_sha256 is None:
                if hash_existing_target_file(config_root, item.target_path) is not None:
                    raise DeploymentError(
                        f"target changed after preview: {item.target_path!r}"
                    )
                # Complete replace_directory snapshots do not need explicit
                # absent-file markers: scope verification removes any file that
                # is not present in the snapshot. Keep markers for narrower
                # legacy replace_files rollback semantics.
                if mode != "replace_directory":
                    entries.append(
                        {
                            "target_path": item.target_path,
                            "operation": item.operation.value,
                            "existed": False,
                            "sha256": None,
                            "size": None,
                        }
                    )
                continue

            source = safe_target_path(config_root, item.target_path)
            if not source.exists() or not source.is_file():
                raise DeploymentError(
                    f"backup source missing: {item.target_path!r}"
                )
            source_stat = source.stat()
            if source_stat.st_nlink > 1:
                raise DeploymentError(
                    f"backup source has hard links: {item.target_path!r}"
                )

            destination = backup_root / "files" / Path(
                *PurePosixPath(item.target_path).parts
            )
            copied_sha256, copied_size = _copy_file_with_hash(source, destination)
            if (
                copied_sha256 != item.target_sha256
                or copied_size != item.target_size
                or source_stat.st_size != item.target_size
            ):
                raise DeploymentError(
                    f"target changed after preview: {item.target_path!r}"
                )
            total_backup_bytes += copied_size
            if total_backup_bytes > manifest.max_uncompressed_bytes:
                raise DeploymentError(
                    "backup exceeds manifest max_uncompressed_bytes"
                )
            if sha256_file(destination) != item.target_sha256:
                raise DeploymentError(
                    f"backup verification failed: {item.target_path!r}"
                )
            entries.append(
                {
                    "target_path": item.target_path,
                    "operation": item.operation.value,
                    "existed": True,
                    "sha256": item.target_sha256,
                    "size": item.target_size,
                }
            )

        _write_json_atomic(
            backup_root / "backup.json",
            {
                "schema": "deploy-relay.backup.v1",
                "transaction_id": transaction_id,
                "project_id": manifest.project_id,
                "repository": manifest.repository,
                "created_at": _utc_now(),
                "kind": "deployment",
                "source_ref": preview.source_ref,
                "source_commit": preview.source_commit,
                "previous_version": (context or {}).get("previous_version"),
                "target_version": (context or {}).get("target_version"),
                "version_marker": (context or {}).get("version_marker"),
                "snapshot_complete": snapshot_complete,
                "groups": groups_payload,
                "entries": entries,
            },
        )
        return backup_root
    except Exception:
        shutil.rmtree(backup_root, ignore_errors=True)
        raise


def _atomic_copy_to_target(
    source: Path,
    target: Path,
    *,
    expected_sha256: str,
    transaction_id: str,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{transaction_id}.tmp")
    if tmp.exists():
        tmp.unlink()
    shutil.copy2(source, tmp)
    if sha256_file(tmp) != expected_sha256:
        tmp.unlink(missing_ok=True)
        raise DeploymentError(f"temporary target verification failed: {target}")
    os.replace(tmp, target)


def _apply_staged_changes(
    manifest: DeploymentManifest,
    preview: PreviewResult,
    *,
    config_root: Path,
    staging_root: Path,
    transaction_id: str,
) -> int:
    group_targets = {
        group.id: PurePosixPath(group.target)
        for group in manifest.groups
    }

    # Add/change first; removals last. Any failure after mutation is rolled back.
    ordered = sorted(
        (
            item
            for item in preview.files
            if item.operation is not PreviewOperation.UNCHANGED
        ),
        key=lambda item: (
            item.operation is PreviewOperation.REMOVE,
            item.target_path,
        ),
    )

    changed = 0
    for item in ordered:
        target = safe_target_path(config_root, item.target_path)
        current = hash_existing_target_file(config_root, item.target_path)

        if item.target_sha256 is None:
            if current is not None:
                raise DeploymentError(
                    f"target changed immediately before install: {item.target_path!r}"
                )
        elif current != (item.target_sha256, item.target_size):
            raise DeploymentError(
                f"target changed immediately before install: {item.target_path!r}"
            )

        if item.operation is PreviewOperation.REMOVE:
            if not target.exists() or not target.is_file():
                raise DeploymentError(
                    f"remove target missing during install: {item.target_path!r}"
                )
            target.unlink()
            changed += 1
            continue

        expected_sha256 = item.source_sha256
        expected_size = item.source_size
        group_target = group_targets.get(item.group_id)
        if (
            not expected_sha256
            or expected_size is None
            or group_target is None
        ):
            raise DeploymentError(
                f"preview source identity missing for {item.target_path!r}"
            )
        try:
            relative = PurePosixPath(item.target_path).relative_to(group_target)
        except ValueError as err:
            raise DeploymentError(
                f"preview target escapes deployment group: {item.target_path!r}"
            ) from err
        if not relative.parts:
            raise DeploymentError("preview target resolves to a managed directory")

        staged_path = _stage_path(
            staging_root,
            item.group_id,
            relative.as_posix(),
        )
        if not staged_path.is_file():
            raise DeploymentError(
                f"staged source missing for target {item.target_path!r}"
            )
        if staged_path.stat().st_size != expected_size:
            raise DeploymentError(
                f"staged file size changed for target {item.target_path!r}"
            )
        if sha256_file(staged_path) != expected_sha256:
            raise DeploymentError(
                f"staged file hash changed for target {item.target_path!r}"
            )

        # Re-check target safety after parent creation to fail closed on link traversal.
        target.parent.mkdir(parents=True, exist_ok=True)
        target = safe_target_path(config_root, item.target_path)
        _atomic_copy_to_target(
            staged_path,
            target,
            expected_sha256=expected_sha256,
            transaction_id=transaction_id,
        )
        changed += 1

    return changed


def _verify_installed(
    preview: PreviewResult,
    *,
    config_root: Path,
) -> None:
    """Verify the complete managed result without building another file map."""
    for item in preview.files:
        if item.operation is PreviewOperation.REMOVE:
            target = safe_target_path(config_root, item.target_path)
            if target.exists():
                raise DeploymentError(
                    f"removed target still exists: {item.target_path!r}"
                )
            continue

        if item.source_sha256 is None or item.source_size is None:
            raise DeploymentError(
                f"preview source identity missing for {item.target_path!r}"
            )
        current = hash_existing_target_file(config_root, item.target_path)
        if current != (item.source_sha256, item.source_size):
            raise DeploymentError(
                f"post-install verification failed: {item.target_path!r}"
            )


_PROJECT_ID_SAFE = re.compile(r"^[a-z][a-z0-9_]*$")
_TRANSACTION_ID_SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _backup_project_root(
    config_root: Path,
    project_id: str,
    *,
    create: bool,
) -> Path | None:
    """Return one project backup directory without permitting path traversal."""

    if not _PROJECT_ID_SAFE.fullmatch(project_id):
        raise DeploymentError("backup project id has invalid format")
    if create:
        return _ensure_owned_dir(config_root, "backups", project_id)

    root = _ensure_config_root(config_root)
    current = root
    for part in ("deploy_relay", "backups", project_id):
        current = current / part
        if not current.exists():
            return None
        if current.is_symlink() or not current.is_dir():
            raise DeploymentError("backup data path is unsafe")
        resolved = current.resolve()
        if resolved != root and root not in resolved.parents:
            raise DeploymentError("backup data path escapes config root")
    return current


def _backup_root_by_id(
    config_root: Path,
    project_id: str,
    transaction_id: str,
) -> Path:
    if not _TRANSACTION_ID_SAFE.fullmatch(transaction_id):
        raise DeploymentError("backup transaction id has invalid format")
    parent = _backup_project_root(config_root, project_id, create=False)
    if parent is None:
        raise LookupError("Backup not found")
    backup_root = parent / transaction_id
    if (
        not backup_root.exists()
        or backup_root.is_symlink()
        or not backup_root.is_dir()
        or backup_root.parent.resolve() != parent.resolve()
    ):
        raise LookupError("Backup not found")
    return backup_root


def _read_backup_payload(
    backup_root: Path,
    *,
    error_type: type[DeploymentError] = RecoveryRequiredError,
) -> dict[str, Any]:
    """Read one bounded backup metadata file exactly once."""
    metadata = backup_root / "backup.json"
    if metadata.is_symlink() or not metadata.is_file():
        raise error_type("backup metadata is missing or unsafe")
    try:
        size = metadata.stat().st_size
    except OSError as err:
        raise error_type("backup metadata cannot be stat'ed") from err
    if size > _MAX_BACKUP_METADATA_BYTES:
        raise error_type("backup metadata exceeds resource limit")
    try:
        payload = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise error_type("backup metadata cannot be read") from err
    if not isinstance(payload, dict) or payload.get("schema") != "deploy-relay.backup.v1":
        raise error_type("backup metadata schema is invalid")
    return payload


def _validated_backup_entries(
    payload: dict[str, Any],
    *,
    error_type: type[DeploymentError] = RecoveryRequiredError,
) -> list[dict[str, Any]]:
    """Validate and return the existing entries list without copying it."""
    entries = payload.get("entries")
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise error_type("backup metadata is invalid")
    if len(entries) > _MAX_BACKUP_ENTRIES:
        raise error_type("backup metadata contains too many entries")

    seen: set[str] = set()
    for item in entries:
        target_path = item.get("target_path")
        existed = item.get("existed")
        if (
            not isinstance(target_path, str)
            or not target_path
            or target_path in seen
            or not isinstance(existed, bool)
        ):
            raise error_type("backup metadata contains invalid entries")
        seen.add(target_path)
        try:
            validate_target_path(target_path)
        except Exception as err:
            raise error_type("backup metadata contains unsafe target path") from err

        if existed:
            digest = item.get("sha256")
            size = item.get("size")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest.casefold())
                or not isinstance(size, int)
                or isinstance(size, bool)
                or size < 0
            ):
                raise error_type("backup metadata has invalid file identity")
        elif item.get("sha256") is not None or item.get("size") is not None:
            raise error_type("backup metadata has invalid absent-file identity")
    return entries


def list_project_backups(
    config_root: Path,
    project_id: str,
) -> list[dict[str, Any]]:
    """Return verified metadata for DRA-owned backups, newest first."""

    parent = _backup_project_root(config_root, project_id, create=False)
    if parent is None:
        return []

    values: list[dict[str, Any]] = []
    for child in parent.iterdir():
        if child.is_symlink() or not child.is_dir():
            continue
        try:
            payload = _read_backup_payload(
                child,
                error_type=DeploymentError,
            )
            entries = _validated_backup_entries(
                payload,
                error_type=DeploymentError,
            )
        except DeploymentError:
            continue
        if payload.get("project_id") != project_id:
            continue
        if payload.get("transaction_id") != child.name:
            continue

        stored_files = 0
        total_bytes = 0
        for item in entries:
            if bool(item.get("existed")):
                stored_files += 1
                total_bytes += int(item["size"])

        groups = payload.get("groups")
        restore_capable = (
            payload.get("snapshot_complete") is True
            and isinstance(groups, list)
            and bool(groups)
            and all(
                isinstance(group, dict)
                and group.get("mode") == "replace_directory"
                and isinstance(group.get("target"), str)
                and bool(group.get("target"))
                for group in groups
            )
        )
        created_at = payload.get("created_at")
        values.append(
            {
                "transaction_id": str(payload.get("transaction_id") or child.name),
                "created_at": str(created_at or ""),
                "kind": str(payload.get("kind") or "deployment"),
                "repository": payload.get("repository"),
                "source_ref": payload.get("source_ref"),
                "source_commit": payload.get("source_commit"),
                "previous_version": payload.get("previous_version"),
                "target_version": payload.get("target_version"),
                "version_marker": payload.get("version_marker"),
                "restore_source_transaction": payload.get("restore_source_transaction"),
                "restore_capable": restore_capable,
                "entries": len(entries),
                "stored_files": stored_files,
                "total_bytes": total_bytes,
            }
        )

    values.sort(
        key=lambda item: (item["created_at"], item["transaction_id"]),
        reverse=True,
    )
    return values


def prune_project_backups(
    config_root: Path,
    project_id: str,
    retain: int,
    *,
    protected_ids: set[str] | None = None,
) -> list[str]:
    """Keep at most the newest configured valid backups for one project."""

    if retain < 1:
        raise DeploymentError("backup retention must be positive")
    protected = protected_ids or set()
    backups = list_project_backups(config_root, project_id)
    if len(backups) <= retain:
        return []

    removable = [
        item for item in reversed(backups)
        if item["transaction_id"] not in protected
    ]
    remove_count = len(backups) - retain
    removed: list[str] = []
    for item in removable:
        if len(removed) >= remove_count:
            break
        backup_root = _backup_root_by_id(
            config_root,
            project_id,
            str(item["transaction_id"]),
        )
        shutil.rmtree(backup_root)
        removed.append(str(item["transaction_id"]))
    return removed


def _read_restore_groups(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Validate complete replace-directory snapshot boundaries."""

    if payload.get("snapshot_complete") is not True:
        raise DeploymentError(
            "Selected backup is a legacy transaction rollback point and cannot "
            "be restored independently. Use Git/version rollback for that state."
        )
    raw_groups = payload.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise DeploymentError("backup restore scope is missing")

    groups: list[dict[str, str]] = []
    targets: list[PurePosixPath] = []
    seen_ids: set[str] = set()
    for raw in raw_groups:
        if not isinstance(raw, dict):
            raise DeploymentError("backup restore scope is invalid")
        group_id = raw.get("id")
        mode = raw.get("mode")
        target = raw.get("target")
        if (
            not isinstance(group_id, str)
            or not group_id
            or group_id in seen_ids
            or mode != "replace_directory"
            or not isinstance(target, str)
            or not target
        ):
            raise DeploymentError("backup restore scope is not independently restorable")
        clean_target = validate_target_path(target).as_posix()
        target_path = PurePosixPath(clean_target)
        for existing in targets:
            if (
                target_path == existing
                or target_path in existing.parents
                or existing in target_path.parents
            ):
                raise DeploymentError("backup restore scopes overlap")
        seen_ids.add(group_id)
        targets.append(target_path)
        groups.append(
            {
                "id": group_id,
                "mode": "replace_directory",
                "target": clean_target,
            }
        )
    return groups


def _target_in_group(target_path: str, group_target: str) -> bool:
    target = PurePosixPath(target_path)
    root = PurePosixPath(group_target)
    return root in target.parents


def _capture_current_snapshot_entries(
    *,
    config_root: Path,
    groups: list[dict[str, str]],
    backup_root: Path,
) -> list[dict[str, Any]]:
    """Copy the complete current managed state for restore safety."""

    entries: list[dict[str, Any]] = []
    total_bytes = 0
    total_files = 0
    for group in groups:
        target_root = group["target"]
        for relative, _digest, advertised_size in iter_target_directory_files(
            config_root,
            target_root,
            max_files=_MAX_BACKUP_ENTRIES - total_files,
            hash_files=False,
        ):
            total_files += 1
            if total_files > _MAX_BACKUP_ENTRIES:
                raise RecoveryRequiredError("restore snapshot contains too many files")
            target_path = validate_target_path(
                (PurePosixPath(target_root) / PurePosixPath(relative)).as_posix()
            ).as_posix()

            source = safe_target_path(config_root, target_path)
            source_stat = source.stat()
            if source_stat.st_nlink > 1:
                raise RecoveryRequiredError(
                    f"restore safety source has hard links: {target_path!r}"
                )
            destination = backup_root / "files" / Path(
                *PurePosixPath(target_path).parts
            )
            digest, size = _copy_file_with_hash(source, destination)
            if size != advertised_size or source_stat.st_size != advertised_size:
                raise RecoveryRequiredError(
                    f"restore safety source changed: {target_path!r}"
                )
            total_bytes += size
            if total_bytes > _MAX_RESTORE_SNAPSHOT_BYTES:
                raise RecoveryRequiredError("restore safety backup exceeds 1 GiB")
            if sha256_file(destination) != digest:
                raise RecoveryRequiredError(
                    f"restore safety backup verification failed: {target_path!r}"
                )
            entries.append(
                {
                    "target_path": target_path,
                    "operation": "restore_safety",
                    "existed": True,
                    "sha256": digest,
                    "size": size,
                }
            )
    return entries


def _create_restore_safety_backup(
    *,
    config_root: Path,
    project_id: str,
    repository: str,
    selected_payload: dict[str, Any],
    transaction_id: str,
    restore_source_transaction: str,
) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    """Create a complete snapshot and return its already-built metadata."""

    groups = _read_restore_groups(selected_payload)
    parent = _backup_project_root(config_root, project_id, create=True)
    assert parent is not None
    backup_root = parent / transaction_id
    if backup_root.exists():
        raise DeploymentError("restore safety backup directory already exists")
    backup_root.mkdir()

    try:
        entries = _capture_current_snapshot_entries(
            config_root=config_root,
            groups=groups,
            backup_root=backup_root,
        )
        payload = {
            "schema": "deploy-relay.backup.v1",
            "transaction_id": transaction_id,
            "project_id": project_id,
            "repository": repository,
            "created_at": _utc_now(),
            "kind": "restore_safety",
            "restore_source_transaction": restore_source_transaction,
            "snapshot_complete": True,
            "groups": groups,
            "entries": entries,
        }
        _write_json_atomic(
            backup_root / "backup.json",
            payload,
        )
        return backup_root, payload, entries
    except Exception:
        shutil.rmtree(backup_root, ignore_errors=True)
        raise


def _changed_paths_between_backup_states(
    desired_entries: list[dict[str, Any]],
    current_entries: list[dict[str, Any]],
) -> list[str]:
    """Return exact path differences between two complete snapshot states."""

    desired = {
        str(item["target_path"]): (
            bool(item.get("existed")),
            item.get("sha256") if item.get("existed") else None,
        )
        for item in desired_entries
    }
    changed: list[str] = []
    for item in current_entries:
        path = str(item["target_path"])
        current_state = (
            bool(item.get("existed")),
            item.get("sha256") if item.get("existed") else None,
        )
        desired_state = desired.pop(path, (False, None))
        if desired_state != current_state:
            changed.append(path)

    for path, desired_state in desired.items():
        if desired_state != (False, None):
            changed.append(path)
    changed.sort()
    return changed


def _prune_complete_snapshot_scope(
    *,
    config_root: Path,
    groups: list[dict[str, str]],
    entries: list[dict[str, Any]],
) -> None:
    """Remove current managed files not present in the selected snapshot."""

    desired = {
        str(item["target_path"])
        for item in entries
        if bool(item.get("existed"))
    }
    for group in groups:
        target_root = group["target"]
        for relative, _digest, _size in iter_target_directory_files(
            config_root,
            target_root,
            max_files=_MAX_BACKUP_ENTRIES,
            hash_files=False,
        ):
            target_path = validate_target_path(
                (PurePosixPath(target_root) / PurePosixPath(relative)).as_posix()
            ).as_posix()
            if target_path in desired:
                continue
            target = safe_target_path(config_root, target_path)
            if target.exists():
                if not target.is_file() or target.is_symlink() or target.stat().st_nlink > 1:
                    raise RecoveryRequiredError(
                        f"restore target is unsafe: {target_path!r}"
                    )
                target.unlink()


def _verify_complete_snapshot_scope(
    *,
    config_root: Path,
    groups: list[dict[str, str]],
    entries: list[dict[str, Any]],
) -> None:
    """Prove the managed target exactly matches a complete snapshot."""

    expected = {
        str(item["target_path"]): (str(item["sha256"]), int(item["size"]))
        for item in entries
        if bool(item.get("existed"))
    }
    for group in groups:
        target_root = group["target"]
        for relative, digest, size in iter_target_directory_files(
            config_root,
            target_root,
            max_files=_MAX_BACKUP_ENTRIES,
            hash_files=True,
        ):
            assert digest is not None
            target_path = validate_target_path(
                (PurePosixPath(target_root) / PurePosixPath(relative)).as_posix()
            ).as_posix()
            if expected.pop(target_path, None) != (digest, size):
                raise RecoveryRequiredError(
                    "restored managed scope does not exactly match backup snapshot"
                )
    if expected:
        raise RecoveryRequiredError(
            "restored managed scope does not exactly match backup snapshot"
        )


def restore_project_backup(
    *,
    config_root: Path,
    project_id: str,
    repository: str,
    backup_transaction_id: str,
) -> BackupRestoreResult:
    """Restore one independent snapshot with a new safety snapshot first."""

    selected_root = _backup_root_by_id(
        config_root,
        project_id,
        backup_transaction_id,
    )
    selected_payload = _read_backup_payload(
        selected_root,
        error_type=DeploymentError,
    )
    if selected_payload.get("project_id") != project_id:
        raise DeploymentError("backup project identity mismatch")
    if selected_payload.get("transaction_id") != backup_transaction_id:
        raise DeploymentError("backup transaction identity mismatch")
    backup_repository = selected_payload.get("repository")
    if (
        not isinstance(backup_repository, str)
        or not backup_repository
        or backup_repository.casefold() != repository.casefold()
    ):
        raise DeploymentError("backup repository identity mismatch")

    _read_restore_groups(selected_payload)
    selected_entries = _validated_backup_entries(
        selected_payload,
        error_type=DeploymentError,
    )

    restore_id = (
        f"{make_transaction_id(project_id, 'restore')}-"
        f"{uuid4().hex[:8]}"
    )
    safety_root, safety_payload, current_entries = _create_restore_safety_backup(
        config_root=config_root,
        project_id=project_id,
        repository=repository,
        selected_payload=selected_payload,
        transaction_id=restore_id,
        restore_source_transaction=backup_transaction_id,
    )
    changed_paths = _changed_paths_between_backup_states(
        selected_entries,
        current_entries,
    )
    lifecycle = lifecycle_for_target_paths(changed_paths)

    transaction_dir = _ensure_owned_dir(config_root, "transactions")
    journal_path = transaction_dir / f"{restore_id}.json"

    def write_restore_state(state: str, *, error: str | None = None) -> None:
        _write_json_atomic(
            journal_path,
            {
                "schema": "deploy-relay.restore.v1",
                "transaction_id": restore_id,
                "project_id": project_id,
                "repository": repository,
                "created_at": _utc_now(),
                "state": state,
                "restored_backup_id": backup_transaction_id,
                "safety_backup_path": str(safety_root),
                "changed_files": len(changed_paths),
                "lifecycle": lifecycle.value,
                "error": error,
            },
        )

    write_restore_state("restoring")
    try:
        _rollback(
            config_root=config_root,
            backup_root=selected_root,
            transaction_id=restore_id,
            payload=selected_payload,
            entries=selected_entries,
        )
    except Exception as restore_err:
        try:
            _rollback(
                config_root=config_root,
                backup_root=safety_root,
                transaction_id=f"{restore_id}-safety",
                payload=safety_payload,
                entries=current_entries,
            )
        except Exception as safety_err:
            message = (
                f"backup restore failed ({type(restore_err).__name__}) and "
                f"safety rollback failed ({type(safety_err).__name__}): {safety_err}"
            )
            write_restore_state("recovery_required", error=message)
            raise RecoveryRequiredError(message) from safety_err

        message = f"backup restore failed and safety rollback succeeded: {restore_err}"
        write_restore_state("rolled_back", error=message)
        raise DeploymentError(message) from restore_err

    write_restore_state("success")
    return BackupRestoreResult(
        transaction_id=restore_id,
        restored_backup_id=backup_transaction_id,
        safety_backup_path=str(safety_root),
        journal_path=str(journal_path),
        lifecycle=lifecycle.value,
        restart_required=lifecycle.value == "home_assistant_restart",
        changed_files=len(changed_paths),
    )


def _read_backup_entries(backup_root: Path) -> list[dict[str, Any]]:
    """Read and validate backup entries through the bounded single-parse path."""
    payload = _read_backup_payload(backup_root)
    return _validated_backup_entries(payload)


def _rollback(
    *,
    config_root: Path,
    backup_root: Path | None,
    transaction_id: str,
    payload: dict[str, Any] | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> None:
    if backup_root is None:
        return

    if payload is None:
        payload = _read_backup_payload(backup_root)
    if entries is None:
        entries = _validated_backup_entries(payload)
    groups: list[dict[str, str]] = []
    if payload.get("snapshot_complete") is True:
        groups = _read_restore_groups(payload)
        _prune_complete_snapshot_scope(
            config_root=config_root,
            groups=groups,
            entries=entries,
        )

    for item in reversed(entries):
        target_path = str(item["target_path"])
        target = safe_target_path(config_root, target_path)
        existed = bool(item.get("existed"))

        if not existed:
            if target.exists():
                if not target.is_file():
                    raise RecoveryRequiredError(
                        f"rollback target is not a file: {target_path!r}"
                    )
                target.unlink()
            continue

        expected_sha256 = item.get("sha256")
        if not isinstance(expected_sha256, str) or not expected_sha256:
            raise RecoveryRequiredError("backup metadata has no valid hash")
        source = backup_root / "files" / Path(*PurePosixPath(target_path).parts)
        if (
            source.is_symlink()
            or not source.is_file()
            or source.stat().st_nlink > 1
            or sha256_file(source) != expected_sha256
        ):
            raise RecoveryRequiredError(
                f"backup file verification failed: {target_path!r}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target = safe_target_path(config_root, target_path)
        _atomic_copy_to_target(
            source,
            target,
            expected_sha256=expected_sha256,
            transaction_id=f"{transaction_id}-rollback",
        )

    # Prove that all backed-up states were restored.
    for item in entries:
        target_path = str(item["target_path"])
        current = hash_existing_target_file(config_root, target_path)
        if bool(item.get("existed")):
            expected = (str(item["sha256"]), int(item["size"]))
            if current != expected:
                raise RecoveryRequiredError(
                    f"rollback verification failed: {target_path!r}"
                )
        elif current is not None:
            raise RecoveryRequiredError(
                f"rollback could not remove added file: {target_path!r}"
            )

    if groups:
        _verify_complete_snapshot_scope(
            config_root=config_root,
            groups=groups,
            entries=entries,
        )


async def async_execute_deployment(
    session: ClientSession,
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    preview: PreviewResult,
    *,
    token: str | None,
    config_root: Path,
    progress: ProgressCallback | None = None,
    backup_context: dict[str, Any] | None = None,
    blocking_executor: BlockingExecutor | None = None,
) -> DeploymentExecutionResult:
    """Stage, back up, install and verify without blocking the HA event loop."""
    transaction_id = make_transaction_id(
        manifest.project_id,
        inventory.source_commit,
    )
    created_at = _utc_now()
    transaction_dir = await _run_blocking(
        blocking_executor,
        _ensure_owned_dir,
        config_root,
        "transactions",
    )
    journal_path = transaction_dir / f"{transaction_id}.json"
    if await _run_blocking(blocking_executor, journal_path.exists):
        raise DeploymentError("transaction journal already exists")

    backup_root: Path | None = None
    staging_root: Path | None = None
    mutation_started = False
    changed_files = 0
    lifecycle = await _run_blocking(
        blocking_executor,
        assess_lifecycle,
        manifest,
        preview,
    )

    preview_counts = {
        "add": 0,
        "change": 0,
        "remove": 0,
        "unchanged": 0,
    }
    for item in preview.files:
        preview_counts[item.operation.value] += 1

    async def write_state(
        state: TransactionState,
        *,
        error: str | None = None,
    ) -> None:
        await _run_blocking(
            blocking_executor,
            _write_json_atomic,
            journal_path,
            _journal_payload(
                transaction_id=transaction_id,
                manifest=manifest,
                inventory=inventory,
                preview_counts=preview_counts,
                lifecycle=lifecycle,
                state=state,
                created_at=created_at,
                backup_path=str(backup_root) if backup_root else None,
                error=error,
            ),
        )

    await write_state(TransactionState.STAGING)

    try:
        staging_root = await async_materialize_staging(
            session,
            manifest,
            inventory,
            token=token,
            config_root=config_root,
            transaction_id=transaction_id,
            progress=progress,
            blocking_executor=blocking_executor,
        )

        await write_state(TransactionState.BACKING_UP)
        await _progress(
            progress,
            "backup",
            {"transaction_id": transaction_id},
        )
        # _create_backup validates the complete preview target identity before
        # any mutation, so a separate full-tree rehash would only duplicate IO.
        backup_root = await _run_blocking(
            blocking_executor,
            _create_backup,
            manifest,
            preview,
            config_root=config_root,
            transaction_id=transaction_id,
            context=backup_context,
        )
        await write_state(TransactionState.BACKING_UP)

        affected_count = (
            preview_counts["add"]
            + preview_counts["change"]
            + preview_counts["remove"]
        )
        if affected_count:
            mutation_started = True
            await write_state(TransactionState.INSTALLING)
            await _progress(
                progress,
                "install",
                {
                    "transaction_id": transaction_id,
                    "affected_files": affected_count,
                },
            )
            changed_files = await _run_blocking(
                blocking_executor,
                _apply_staged_changes,
                manifest,
                preview,
                config_root=config_root,
                staging_root=staging_root,
                transaction_id=transaction_id,
            )

        await write_state(TransactionState.VERIFYING_INSTALL)
        await _progress(
            progress,
            "verify_install",
            {
                "transaction_id": transaction_id,
                "changed_files": changed_files,
            },
        )
        await _run_blocking(
            blocking_executor,
            _verify_installed,
            preview,
            config_root=config_root,
        )

        await write_state(TransactionState.SUCCESS)
        await _progress(
            progress,
            "success",
            {
                "transaction_id": transaction_id,
                "changed_files": changed_files,
                "lifecycle": lifecycle.effective.value,
                "lifecycle_declared": lifecycle.declared.value,
                "lifecycle_reason": lifecycle.reason,
            },
        )
        if staging_root is not None:
            await _run_blocking(
                blocking_executor,
                shutil.rmtree,
                staging_root,
                ignore_errors=True,
            )

        return DeploymentExecutionResult(
            transaction_id=transaction_id,
            state=TransactionState.SUCCESS,
            backup_path=str(backup_root) if backup_root else None,
            journal_path=str(journal_path),
            lifecycle=lifecycle.effective.value,
            restart_required=lifecycle.effective.value == "home_assistant_restart",
            changed_files=changed_files,
        )
    except Exception as err:
        if not mutation_started:
            await write_state(TransactionState.FAILED_NO_CHANGE, error=str(err))
            if staging_root is not None:
                await _run_blocking(
                    blocking_executor,
                    shutil.rmtree,
                    staging_root,
                    ignore_errors=True,
                )
            raise DeploymentError(str(err)) from err

        try:
            await _progress(
                progress,
                "rollback",
                {
                    "transaction_id": transaction_id,
                    "reason": type(err).__name__,
                },
            )
            await _run_blocking(
                blocking_executor,
                _rollback,
                config_root=config_root,
                backup_root=backup_root,
                transaction_id=transaction_id,
            )
        except Exception as rollback_err:
            message = (
                f"deployment failed ({type(err).__name__}) and rollback failed "
                f"({type(rollback_err).__name__}): {rollback_err}"
            )
            await write_state(TransactionState.RECOVERY_REQUIRED, error=message)
            raise RecoveryRequiredError(message) from rollback_err

        await write_state(TransactionState.ROLLED_BACK, error=str(err))
        if staging_root is not None:
            await _run_blocking(
                blocking_executor,
                shutil.rmtree,
                staging_root,
                ignore_errors=True,
            )
        raise DeploymentError(
            f"deployment failed and automatic rollback succeeded: {err}"
        ) from err
