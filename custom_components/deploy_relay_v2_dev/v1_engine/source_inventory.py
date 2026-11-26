"""Read-only source inventory bound to a frozen repository commit."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath

from aiohttp import ClientSession

from .github_client import GitHubApiError, GitHubClient, GitHubNotFoundError
from .manifest import DeploymentManifest
from .path_policy import PathPolicyError, normalize_relative_path
from .planner import DeploymentPlan, PlannedGroup, build_plan
from .runtime_policy import is_runtime_generated_path
from .version_markers import (
    MAX_VERSION_MARKER_SCAN_BYTES,
    VersionMarker,
    extract_version_markers,
    should_scan_version_markers,
)


class SourceInventoryError(RuntimeError):
    """Source inventory could not be built safely."""


@dataclass(frozen=True, slots=True)
class SourceInventoryFile:
    """One managed source file at an exact commit."""

    relative_path: str
    source_path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SourceGroupInventory:
    """Source files belonging to one deployment group."""

    group_id: str
    files: tuple[SourceInventoryFile, ...]


@dataclass(frozen=True, slots=True)
class SourceInventory:
    """Complete read-only inventory for one frozen source."""

    project_id: str
    repository: str
    source_ref: str
    source_commit: str
    groups: tuple[SourceGroupInventory, ...]
    total_files: int
    total_bytes: int
    version_markers: tuple[VersionMarker, ...] = ()


def _relative_to_source(entry_path: str, source: PurePosixPath) -> str:
    """Return a normalized path relative to a group's source directory."""
    normalized = normalize_relative_path(entry_path)
    try:
        relative = normalized.relative_to(source)
    except ValueError as err:
        raise SourceInventoryError("GitHub returned a path outside the source group") from err
    if not relative.parts:
        raise SourceInventoryError("source inventory contains the source directory itself")
    return relative.as_posix()


async def _discover_directory_files(
    client: GitHubClient,
    plan_group: PlannedGroup,
    *,
    repository: str,
    commit_sha: str,
    max_files: int,
) -> tuple[tuple[str, str, int], ...]:
    """Discover regular files below a source directory at an exact commit."""
    source = normalize_relative_path(plan_group.source)
    queue: deque[str] = deque([source.as_posix()])
    discovered: list[tuple[str, str, int]] = []
    seen_directories: set[str] = set()
    seen_relative_paths: set[str] = set()

    while queue:
        directory = queue.popleft()
        if directory in seen_directories:
            raise SourceInventoryError("duplicate/cyclic source directory discovery")
        seen_directories.add(directory)

        try:
            entries = await client.async_list_directory(
                repository,
                directory,
                ref=commit_sha,
            )
        except (GitHubNotFoundError, GitHubApiError) as err:
            raise SourceInventoryError(
                f"cannot read source directory {directory!r}"
            ) from err

        for entry in sorted(entries, key=lambda item: item.path.casefold()):
            try:
                relative = _relative_to_source(entry.path, source)
            except PathPolicyError as err:
                raise SourceInventoryError("unsafe source path returned by GitHub") from err

            if entry.type == "dir":
                if is_runtime_generated_path(relative):
                    continue
                queue.append(entry.path)
                continue
            if entry.type != "file":
                raise SourceInventoryError(
                    f"unsupported source entry type {entry.type!r} at {entry.path!r}"
                )

            if is_runtime_generated_path(relative):
                continue

            if relative in seen_relative_paths:
                raise SourceInventoryError("source contains duplicate normalized paths")
            seen_relative_paths.add(relative)
            discovered.append((relative, entry.path, entry.size))
            if len(discovered) > max_files:
                raise SourceInventoryError("source exceeds manifest max_files")

    return tuple(discovered)


async def _group_file_specs(
    client: GitHubClient,
    plan_group: PlannedGroup,
    *,
    repository: str,
    commit_sha: str,
    max_files: int,
) -> tuple[tuple[str, str, int | None], ...]:
    """Return relative path, repository path and optional advertised size."""
    source = normalize_relative_path(plan_group.source)

    if plan_group.mode == "replace_directory":
        return await _discover_directory_files(
            client,
            plan_group,
            repository=repository,
            commit_sha=commit_sha,
            max_files=max_files,
        )

    if plan_group.mode != "replace_files":
        raise SourceInventoryError(f"unsupported group mode {plan_group.mode!r}")

    specs: list[tuple[str, str, int | None]] = []
    for value in plan_group.files:
        relative = normalize_relative_path(value)
        if is_runtime_generated_path(relative.as_posix()):
            raise SourceInventoryError(
                f"runtime-generated artifact cannot be explicitly deployed: {relative}"
            )
        repository_path = (source / relative).as_posix()
        specs.append((relative.as_posix(), repository_path, None))

    return tuple(specs)


async def async_build_source_inventory(
    session: ClientSession,
    manifest: DeploymentManifest,
    *,
    source_ref: str,
    source_commit: str,
    token: str | None = None,
) -> SourceInventory:
    """Hash all manifest-managed repository files from one frozen commit."""
    if manifest.source_mode != "repository_contents":
        raise SourceInventoryError(
            "V0.13 source inventory supports repository_contents only"
        )

    plan: DeploymentPlan = build_plan(
        manifest,
        source_ref=source_ref,
        source_commit=source_commit,
    )
    client = GitHubClient(session, token)

    groups: list[SourceGroupInventory] = []
    version_markers: list[VersionMarker] = []
    total_files = 0
    total_bytes = 0

    for group in plan.groups:
        specs = await _group_file_specs(
            client,
            group,
            repository=plan.repository,
            commit_sha=plan.source_commit,
            max_files=manifest.max_files - total_files,
        )

        files: list[SourceInventoryFile] = []
        pending_specs = deque(specs)
        del specs
        while pending_specs:
            relative_path, source_path, advertised_size = pending_specs.popleft()
            total_files += 1
            if total_files > manifest.max_files:
                raise SourceInventoryError("source exceeds manifest max_files")

            if advertised_size is not None and (
                total_bytes + advertised_size > manifest.max_uncompressed_bytes
            ):
                raise SourceInventoryError(
                    "source exceeds manifest max_uncompressed_bytes"
                )

            remaining = manifest.max_uncompressed_bytes - total_bytes
            file_budget = (
                min(remaining, advertised_size)
                if advertised_size is not None
                else remaining
            )
            digest = sha256()
            actual_size = 0
            marker_bytes = (
                bytearray()
                if should_scan_version_markers(relative_path, advertised_size)
                else None
            )
            try:
                async for chunk in client.async_iter_file_bytes(
                    plan.repository,
                    source_path,
                    ref=plan.source_commit,
                    max_bytes=file_budget,
                ):
                    digest.update(chunk)
                    actual_size += len(chunk)
                    if marker_bytes is not None:
                        if actual_size <= MAX_VERSION_MARKER_SCAN_BYTES:
                            marker_bytes.extend(chunk)
                        else:
                            marker_bytes = None
            except (GitHubNotFoundError, GitHubApiError) as err:
                raise SourceInventoryError(
                    f"cannot read managed source file {source_path!r}"
                ) from err

            if advertised_size is not None and actual_size != advertised_size:
                raise SourceInventoryError(
                    f"GitHub file size changed while reading {source_path!r}"
                )

            total_bytes += actual_size
            if total_bytes > manifest.max_uncompressed_bytes:
                raise SourceInventoryError(
                    "source exceeds manifest max_uncompressed_bytes"
                )

            files.append(
                SourceInventoryFile(
                    relative_path=relative_path,
                    source_path=source_path,
                    size=actual_size,
                    sha256=digest.hexdigest(),
                )
            )
            if marker_bytes is not None:
                version_markers.extend(
                    extract_version_markers(
                        group.id,
                        relative_path,
                        bytes(marker_bytes),
                    )
                )

        groups.append(
            SourceGroupInventory(
                group_id=group.id,
                files=tuple(sorted(files, key=lambda item: item.relative_path)),
            )
        )

    return SourceInventory(
        project_id=plan.project_id,
        repository=plan.repository,
        source_ref=plan.source_ref,
        source_commit=plan.source_commit,
        groups=tuple(groups),
        total_files=total_files,
        total_bytes=total_bytes,
        version_markers=tuple(
            sorted(
                version_markers,
                key=lambda item: (
                    -item.rank,
                    item.group_id,
                    item.relative_path,
                    item.name,
                ),
            )
        ),
    )
