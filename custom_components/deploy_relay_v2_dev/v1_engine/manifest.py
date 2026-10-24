"""Deployment manifest parsing and semantic validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from .const import APPROVED_LOGICAL_ROOT, MANIFEST_SCHEMA_V1, LifecycleAction

_PROJECT_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ALLOWED_SOURCE_MODES = frozenset({"repository_contents", "actions_artifact"})
_ALLOWED_GROUP_MODES = frozenset({"replace_directory", "replace_files"})


class ManifestError(ValueError):
    """Raised when a deployment manifest is invalid."""


@dataclass(frozen=True, slots=True)
class DeploymentGroup:
    """One manifest-authorized install boundary."""

    id: str
    source: str
    target: str
    mode: str
    files: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DeploymentManifest:
    """Validated deployment manifest."""

    project_id: str
    project_name: str
    repository: str
    source_mode: str
    artifact: str | None
    root: str
    groups: tuple[DeploymentGroup, ...]
    after_install: LifecycleAction
    max_files: int
    max_uncompressed_bytes: int


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object")
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{field} must be a non-empty string")
    return value


def parse_manifest(
    raw: str | bytes | dict[str, Any],
    *,
    expected_repository: str | None = None,
    expected_project_id: str | None = None,
) -> DeploymentManifest:
    """Parse and semantically validate a v1 manifest."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as err:
            raise ManifestError(f"invalid JSON: {err.msg}") from err
    else:
        data = raw

    root = _require_dict(data, "manifest")
    if root.get("schema") != MANIFEST_SCHEMA_V1:
        raise ManifestError("unsupported manifest schema")

    project = _require_dict(root.get("project"), "project")
    project_id = _require_string(project.get("id"), "project.id")
    project_name = _require_string(project.get("name"), "project.name")
    if not _PROJECT_ID.fullmatch(project_id):
        raise ManifestError("project.id has invalid format")
    if expected_project_id and project_id != expected_project_id:
        raise ManifestError("project.id does not match configured project")

    source = _require_dict(root.get("source"), "source")
    repository = _require_string(source.get("repository"), "source.repository")
    if not _REPOSITORY.fullmatch(repository):
        raise ManifestError("source.repository has invalid format")
    if expected_repository and repository.lower() != expected_repository.lower():
        raise ManifestError("source.repository does not match configured repository")

    source_mode = _require_string(source.get("mode"), "source.mode")
    if source_mode not in _ALLOWED_SOURCE_MODES:
        raise ManifestError("unsupported source.mode")
    artifact = source.get("artifact")
    if artifact is not None and (not isinstance(artifact, str) or not artifact):
        raise ManifestError("source.artifact must be a non-empty string when present")
    if source_mode == "actions_artifact" and not artifact:
        raise ManifestError("actions_artifact mode requires source.artifact")

    deployment = _require_dict(root.get("deployment"), "deployment")
    logical_root = _require_string(deployment.get("root"), "deployment.root")
    if logical_root != APPROVED_LOGICAL_ROOT:
        raise ManifestError("deployment.root is not locally approved")

    group_values = deployment.get("groups")
    if not isinstance(group_values, list) or not group_values:
        raise ManifestError("deployment.groups must be a non-empty list")

    groups: list[DeploymentGroup] = []
    seen_group_ids: set[str] = set()
    for index, group_value in enumerate(group_values):
        group = _require_dict(group_value, f"deployment.groups[{index}]")
        group_id = _require_string(group.get("id"), f"deployment.groups[{index}].id")
        if not _PROJECT_ID.fullmatch(group_id):
            raise ManifestError(f"group id {group_id!r} has invalid format")
        if group_id in seen_group_ids:
            raise ManifestError(f"duplicate group id {group_id!r}")
        seen_group_ids.add(group_id)

        source_path = _require_string(group.get("source"), f"deployment.groups[{index}].source")
        target_path = _require_string(group.get("target"), f"deployment.groups[{index}].target")
        mode = _require_string(group.get("mode"), f"deployment.groups[{index}].mode")
        if mode not in _ALLOWED_GROUP_MODES:
            raise ManifestError(f"unsupported deployment mode {mode!r}")

        raw_files = group.get("files", [])
        if not isinstance(raw_files, list) or any(
            not isinstance(item, str) or not item for item in raw_files
        ):
            raise ManifestError(f"deployment.groups[{index}].files is invalid")
        files = tuple(raw_files)
        if mode == "replace_files" and not files:
            raise ManifestError("replace_files requires a non-empty files list")
        if len(files) != len(set(files)):
            raise ManifestError("replace_files contains duplicate paths")

        groups.append(
            DeploymentGroup(
                id=group_id,
                source=source_path,
                target=target_path,
                mode=mode,
                files=files,
            )
        )

    lifecycle = _require_dict(root.get("lifecycle"), "lifecycle")
    try:
        after_install = LifecycleAction(
            _require_string(lifecycle.get("after_install"), "lifecycle.after_install")
        )
    except ValueError as err:
        raise ManifestError("unsupported lifecycle.after_install") from err

    policy = _require_dict(root.get("policy"), "policy")
    if policy.get("allow_symlinks") is not False:
        raise ManifestError("policy.allow_symlinks must be false in v1")
    max_files = policy.get("max_files")
    max_bytes = policy.get("max_uncompressed_bytes")
    if not isinstance(max_files, int) or isinstance(max_files, bool) or not 1 <= max_files <= 20000:
        raise ManifestError("policy.max_files is out of range")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 1 <= max_bytes <= 1073741824:
        raise ManifestError("policy.max_uncompressed_bytes is out of range")

    return DeploymentManifest(
        project_id=project_id,
        project_name=project_name,
        repository=repository,
        source_mode=source_mode,
        artifact=artifact,
        root=logical_root,
        groups=tuple(groups),
        after_install=after_install,
        max_files=max_files,
        max_uncompressed_bytes=max_bytes,
    )
