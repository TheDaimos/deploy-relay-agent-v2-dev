"""Deterministic, read-only source-to-target preview."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
import os
from pathlib import Path, PurePosixPath
import stat

from .integrity import sha256_file
from .manifest import DeploymentManifest
from .path_policy import PathPolicyError, validate_target_path
from .planner import DeploymentPlan, PlannedGroup, build_plan
from .runtime_policy import is_runtime_generated_path
from .source_inventory import SourceGroupInventory, SourceInventory


class PreviewError(RuntimeError):
    """A safe deterministic preview could not be produced."""


class PreviewOperation(StrEnum):
    """One proposed file operation."""

    ADD = "add"
    CHANGE = "change"
    REMOVE = "remove"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class PreviewFile:
    """One source/target comparison result."""

    group_id: str
    operation: PreviewOperation
    target_path: str
    source_path: str | None
    source_sha256: str | None
    target_sha256: str | None
    source_size: int | None
    target_size: int | None


@dataclass(frozen=True, slots=True)
class PreviewResult:
    """Immutable read-only preview bound to one commit."""

    project_id: str
    repository: str
    source_ref: str
    source_commit: str
    files: tuple[PreviewFile, ...]

    @property
    def add_count(self) -> int:
        return sum(item.operation is PreviewOperation.ADD for item in self.files)

    @property
    def change_count(self) -> int:
        return sum(item.operation is PreviewOperation.CHANGE for item in self.files)

    @property
    def remove_count(self) -> int:
        return sum(item.operation is PreviewOperation.REMOVE for item in self.files)

    @property
    def unchanged_count(self) -> int:
        return sum(item.operation is PreviewOperation.UNCHANGED for item in self.files)


def _ensure_config_root(config_root: Path) -> Path:
    """Return a trusted existing config root."""
    if config_root.is_symlink():
        raise PreviewError("config root must not be a symlink")
    if not config_root.exists() or not config_root.is_dir():
        raise PreviewError("config root must be an existing directory")
    return config_root.resolve()


def _safe_target_path(config_root: Path, relative: str) -> Path:
    """Resolve a target path while rejecting link traversal."""
    try:
        clean = validate_target_path(relative)
    except PathPolicyError as err:
        raise PreviewError(str(err)) from err

    root = _ensure_config_root(config_root)
    current = root

    for index, part in enumerate(clean.parts):
        current = current / part

        if current.is_symlink():
            raise PreviewError(f"target path contains symlink: {relative!r}")

        if current.exists():
            try:
                current_stat = current.stat()
            except OSError as err:
                raise PreviewError(f"cannot stat target path {relative!r}") from err

            if stat.S_ISREG(current_stat.st_mode) and current_stat.st_nlink > 1:
                raise PreviewError(f"target file has hard links: {relative!r}")

            if index < len(clean.parts) - 1 and not current.is_dir():
                raise PreviewError(
                    f"target parent is not a directory: {relative!r}"
                )

    try:
        resolved = current.resolve(strict=False)
    except OSError as err:
        raise PreviewError(f"cannot resolve target path {relative!r}") from err

    if resolved != root and root not in resolved.parents:
        raise PreviewError("target path escapes config root")
    return current


def _hash_existing_file(config_root: Path, relative: str) -> tuple[str, int] | None:
    """Hash one regular target file or return None when absent."""
    path = _safe_target_path(config_root, relative)
    if not path.exists():
        return None
    if not path.is_file():
        raise PreviewError(f"expected regular target file at {relative!r}")

    try:
        file_stat = path.stat()
        digest = sha256_file(path)
    except OSError as err:
        raise PreviewError(f"cannot read target file {relative!r}") from err

    if file_stat.st_nlink > 1:
        raise PreviewError(f"target file has hard links: {relative!r}")
    return digest, file_stat.st_size


def _iter_target_directory_files(
    config_root: Path,
    target: str,
    *,
    max_files: int,
    hash_files: bool,
) -> Iterator[tuple[str, str | None, int]]:
    """Yield safe managed target files without materializing an extra inventory."""
    base = _safe_target_path(config_root, target)
    if not base.exists():
        return
    if not base.is_dir():
        raise PreviewError(f"managed directory target is not a directory: {target!r}")

    seen: set[str] = set()
    count = 0
    for current_root, dirnames, filenames in os.walk(base, followlinks=False):
        current_path = Path(current_root)
        dirnames.sort(key=str.casefold)
        filenames.sort(key=str.casefold)

        for dirname in list(dirnames):
            directory = current_path / dirname
            if directory.is_symlink():
                raise PreviewError(
                    f"managed target directory contains symlink: {directory}"
                )

            relative_directory = directory.relative_to(base).as_posix()
            if is_runtime_generated_path(relative_directory):
                dirnames.remove(dirname)

        for filename in filenames:
            path = current_path / filename
            if path.is_symlink():
                raise PreviewError(f"managed target contains symlink: {path}")

            relative = path.relative_to(base).as_posix()
            if is_runtime_generated_path(relative):
                continue
            if relative in seen:
                raise PreviewError("duplicate target path discovered")
            seen.add(relative)

            count += 1
            if count > max_files:
                raise PreviewError("managed target exceeds manifest max_files")

            try:
                file_stat = path.stat()
            except OSError as err:
                raise PreviewError(f"cannot stat managed target file {path}") from err

            if not stat.S_ISREG(file_stat.st_mode):
                raise PreviewError(f"managed target contains non-regular file: {path}")
            if file_stat.st_nlink > 1:
                raise PreviewError(f"managed target contains hard-linked file: {path}")

            digest: str | None = None
            if hash_files:
                try:
                    digest = sha256_file(path)
                except OSError as err:
                    raise PreviewError(f"cannot hash managed target file {path}") from err

            yield relative, digest, file_stat.st_size


def _walk_target_directory(
    config_root: Path,
    target: str,
    *,
    max_files: int,
) -> dict[str, tuple[str, int]]:
    """Hash regular files below one exact managed target directory."""
    files: dict[str, tuple[str, int]] = {}
    for relative, digest, size in _iter_target_directory_files(
        config_root,
        target,
        max_files=max_files,
        hash_files=True,
    ):
        assert digest is not None
        files[relative] = (digest, size)
    return files


def _source_groups(inventory: SourceInventory) -> dict[str, SourceGroupInventory]:
    """Index source groups and reject duplicates."""
    groups: dict[str, SourceGroupInventory] = {}
    for group in inventory.groups:
        if group.group_id in groups:
            raise PreviewError(f"duplicate source inventory group {group.group_id!r}")
        groups[group.group_id] = group
    return groups


def _target_join(target: str, relative: str) -> str:
    """Join and validate a target group path with a managed relative file."""
    path = PurePosixPath(target) / PurePosixPath(relative)
    try:
        return validate_target_path(path.as_posix()).as_posix()
    except PathPolicyError as err:
        raise PreviewError("managed target file violates path policy") from err


def _compare_file(
    *,
    config_root: Path,
    group_id: str,
    target_path: str,
    source_path: str,
    source_sha256: str,
    source_size: int,
) -> PreviewFile:
    """Compare one expected source file with its target."""
    target = _hash_existing_file(config_root, target_path)
    if target is None:
        return PreviewFile(
            group_id=group_id,
            operation=PreviewOperation.ADD,
            target_path=target_path,
            source_path=source_path,
            source_sha256=source_sha256,
            target_sha256=None,
            source_size=source_size,
            target_size=None,
        )

    target_sha256, target_size = target
    operation = (
        PreviewOperation.UNCHANGED
        if target_sha256 == source_sha256
        else PreviewOperation.CHANGE
    )
    return PreviewFile(
        group_id=group_id,
        operation=operation,
        target_path=target_path,
        source_path=source_path,
        source_sha256=source_sha256,
        target_sha256=target_sha256,
        source_size=source_size,
        target_size=target_size,
    )


def build_preview(
    manifest: DeploymentManifest,
    source_inventory: SourceInventory,
    *,
    config_root: Path,
) -> PreviewResult:
    """Build an exact read-only add/change/remove/unchanged preview."""
    if source_inventory.project_id != manifest.project_id:
        raise PreviewError("source inventory project does not match manifest")
    if source_inventory.repository.casefold() != manifest.repository.casefold():
        raise PreviewError("source inventory repository does not match manifest")
    if not source_inventory.source_commit:
        raise PreviewError("source inventory has no frozen commit SHA")

    plan: DeploymentPlan = build_plan(
        manifest,
        source_ref=source_inventory.source_ref,
        source_commit=source_inventory.source_commit,
    )
    group_inventories = _source_groups(source_inventory)

    if set(group_inventories) != {group.id for group in plan.groups}:
        raise PreviewError("source inventory groups do not match deployment plan")

    preview_files: list[PreviewFile] = []

    for group in plan.groups:
        inventory_group = group_inventories[group.id]

        previous_relative: str | None = None
        for source_file in inventory_group.files:
            if source_file.relative_path == previous_relative:
                raise PreviewError(f"duplicate source file in group {group.id!r}")
            previous_relative = source_file.relative_path

        if group.mode == "replace_files":
            expected = sorted(group.files)
            actual = [item.relative_path for item in inventory_group.files]
            if actual != expected:
                raise PreviewError(
                    f"source inventory for group {group.id!r} does not match manifest files"
                )

            for source_file in inventory_group.files:
                preview_files.append(
                    _compare_file(
                        config_root=config_root,
                        group_id=group.id,
                        target_path=_target_join(group.target, source_file.relative_path),
                        source_path=source_file.source_path,
                        source_sha256=source_file.sha256,
                        source_size=source_file.size,
                    )
                )
            continue

        if group.mode != "replace_directory":
            raise PreviewError(f"unsupported deployment mode {group.mode!r}")

        target_inventory = _walk_target_directory(
            config_root,
            group.target,
            max_files=manifest.max_files,
        )

        for source_file in inventory_group.files:
            relative = source_file.relative_path
            target_path = _target_join(group.target, relative)
            target_file = target_inventory.pop(relative, None)

            if target_file is None:
                preview_files.append(
                    PreviewFile(
                        group_id=group.id,
                        operation=PreviewOperation.ADD,
                        target_path=target_path,
                        source_path=source_file.source_path,
                        source_sha256=source_file.sha256,
                        target_sha256=None,
                        source_size=source_file.size,
                        target_size=None,
                    )
                )
                continue

            target_sha256, target_size = target_file
            preview_files.append(
                PreviewFile(
                    group_id=group.id,
                    operation=(
                        PreviewOperation.UNCHANGED
                        if target_sha256 == source_file.sha256
                        else PreviewOperation.CHANGE
                    ),
                    target_path=target_path,
                    source_path=source_file.source_path,
                    source_sha256=source_file.sha256,
                    target_sha256=target_sha256,
                    source_size=source_file.size,
                    target_size=target_size,
                )
            )

        for relative in sorted(target_inventory):
            target_sha256, target_size = target_inventory[relative]
            preview_files.append(
                PreviewFile(
                    group_id=group.id,
                    operation=PreviewOperation.REMOVE,
                    target_path=_target_join(group.target, relative),
                    source_path=None,
                    source_sha256=None,
                    target_sha256=target_sha256,
                    source_size=None,
                    target_size=target_size,
                )
            )

    return PreviewResult(
        project_id=plan.project_id,
        repository=plan.repository,
        source_ref=plan.source_ref,
        source_commit=plan.source_commit,
        files=tuple(preview_files),
    )


def iter_target_directory_files(
    config_root: Path,
    target: str,
    *,
    max_files: int = 20000,
    hash_files: bool = True,
) -> Iterator[tuple[str, str | None, int]]:
    """Yield safe target files for executor-owned deployment/restore work."""
    yield from _iter_target_directory_files(
        config_root,
        target,
        max_files=max_files,
        hash_files=hash_files,
    )


def inventory_target_directory(
    config_root: Path,
    target: str,
    *,
    max_files: int = 20000,
) -> dict[str, tuple[str, int]]:
    """Return a safe SHA-256 inventory for one managed target directory."""

    return _walk_target_directory(
        config_root,
        target,
        max_files=max_files,
    )


def safe_target_path(config_root: Path, relative: str) -> Path:
    """Public write-path safety wrapper shared with the deployment engine."""
    return _safe_target_path(config_root, relative)


def hash_existing_target_file(
    config_root: Path,
    relative: str,
) -> tuple[str, int] | None:
    """Public target identity wrapper used for pre/post-mutation verification."""
    return _hash_existing_file(config_root, relative)
