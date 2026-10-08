"""Deterministic deployment planning model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .manifest import DeploymentManifest
from .path_policy import normalize_relative_path, validate_target_path


@dataclass(frozen=True, slots=True)
class PlannedGroup:
    """Validated group operation before filesystem mutation."""

    id: str
    source: str
    target: str
    mode: str
    files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DeploymentPlan:
    """Immutable high-level deployment plan."""

    project_id: str
    repository: str
    source_ref: str
    source_commit: str
    groups: tuple[PlannedGroup, ...]


def _paths_overlap(left: str, right: str) -> bool:
    """Return whether two relative target paths are equal or nested."""
    left_path = PurePosixPath(left)
    right_path = PurePosixPath(right)
    return (
        left_path == right_path
        or left_path in right_path.parents
        or right_path in left_path.parents
    )


def build_plan(
    manifest: DeploymentManifest,
    *,
    source_ref: str,
    source_commit: str,
) -> DeploymentPlan:
    """Build a validated, deterministic plan from an accepted manifest."""
    if not source_ref:
        raise ValueError("source_ref must not be empty")
    if not source_commit:
        raise ValueError("source_commit must not be empty")

    planned: list[PlannedGroup] = []
    seen_targets: list[str] = []

    for group in manifest.groups:
        source = normalize_relative_path(group.source).as_posix()
        target = validate_target_path(group.target).as_posix()

        for existing in seen_targets:
            if _paths_overlap(existing, target):
                raise ValueError(
                    f"deployment target {target!r} overlaps existing target {existing!r}"
                )
        seen_targets.append(target)

        files = tuple(normalize_relative_path(item).as_posix() for item in group.files)
        if len(files) != len(set(files)):
            raise ValueError(f"group {group.id!r} contains duplicate normalized files")

        planned.append(
            PlannedGroup(
                id=group.id,
                source=source,
                target=target,
                mode=group.mode,
                files=files,
            )
        )

    return DeploymentPlan(
        project_id=manifest.project_id,
        repository=manifest.repository,
        source_ref=source_ref,
        source_commit=source_commit,
        groups=tuple(planned),
    )
