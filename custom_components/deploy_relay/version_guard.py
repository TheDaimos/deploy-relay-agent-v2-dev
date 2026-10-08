"""Source-vs-local version regression assessment for Deploy Relay."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .manifest import DeploymentManifest
from .path_policy import validate_target_path
from .planner import build_plan
from .preview import PreviewResult, safe_target_path
from .source_inventory import SourceInventory
from .version_markers import VersionMarker, extract_version_markers


@dataclass(frozen=True, slots=True)
class VersionGuardResult:
    """Secret-free semantic comparison between selected Git source and local target."""

    status: str
    source_version: str | None
    local_version: str | None
    marker: str | None
    source_path: str | None
    target_path: str | None
    regression: bool
    warning: bool
    reason: str
    destructive_changes: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _numeric_key(value: str) -> tuple[int, ...] | None:
    numbers = re.findall(r"\d+", value)
    if not numbers:
        return None
    return tuple(int(item) for item in numbers[:8])


def _compare_versions(source: str, local: str) -> str:
    if source == local:
        return "same"

    source_key = _numeric_key(source)
    local_key = _numeric_key(local)
    if source_key is None or local_key is None:
        return "unknown"

    length = max(len(source_key), len(local_key))
    source_key += (0,) * (length - len(source_key))
    local_key += (0,) * (length - len(local_key))
    if source_key < local_key:
        return "downgrade"
    if source_key > local_key:
        return "upgrade"
    return "unknown"


def _target_relative_path(
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    marker: VersionMarker,
) -> str:
    plan = build_plan(
        manifest,
        source_ref=inventory.source_ref,
        source_commit=inventory.source_commit,
    )
    groups = {group.id: group for group in plan.groups}
    group = groups.get(marker.group_id)
    if group is None:
        raise ValueError("version marker group is missing from deployment plan")
    target = (
        PurePosixPath(group.target) / PurePosixPath(marker.relative_path)
    ).as_posix()
    return validate_target_path(target).as_posix()


def _local_markers_for_source_marker(
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    marker: VersionMarker,
    *,
    config_root: Path,
) -> tuple[VersionMarker, ...]:
    target_relative = _target_relative_path(manifest, inventory, marker)
    target = safe_target_path(config_root, target_relative)
    if not target.exists() or not target.is_file():
        return ()
    try:
        if target.stat().st_size > 512 * 1024:
            return ()
        raw = target.read_bytes()
    except OSError:
        return ()
    return extract_version_markers(
        marker.group_id,
        marker.relative_path,
        raw,
    )


def assess_version_guard(
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    preview: PreviewResult,
    *,
    config_root: Path,
) -> VersionGuardResult:
    """Compare the strongest common Git/local version marker and classify risk."""
    destructive_changes = preview.change_count + preview.remove_count

    candidates: list[tuple[int, VersionMarker, VersionMarker, str]] = []
    for source_marker in inventory.version_markers:
        local_markers = _local_markers_for_source_marker(
            manifest,
            inventory,
            source_marker,
            config_root=config_root,
        )
        for local_marker in local_markers:
            if local_marker.name != source_marker.name:
                continue
            if local_marker.relative_path != source_marker.relative_path:
                continue
            relation = _compare_versions(
                source_marker.value,
                local_marker.value,
            )
            candidates.append(
                (
                    source_marker.rank,
                    source_marker,
                    local_marker,
                    relation,
                )
            )

    if not candidates:
        return VersionGuardResult(
            status="unknown",
            source_version=None,
            local_version=None,
            marker=None,
            source_path=None,
            target_path=None,
            regression=False,
            warning=preview.remove_count > 0,
            reason=(
                "no_common_version_marker_with_removals"
                if preview.remove_count > 0
                else "no_common_version_marker"
            ),
            destructive_changes=destructive_changes,
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1].name,
            item[1].relative_path,
        )
    )
    _, source_marker, local_marker, relation = candidates[0]
    target_path = _target_relative_path(manifest, inventory, source_marker)

    regression = relation == "downgrade"
    warning = regression or (
        relation == "same" and destructive_changes > 0
    )
    reason = {
        "downgrade": "source_older_than_local",
        "upgrade": "source_newer_than_local",
        "same": (
            "same_version_with_file_changes"
            if destructive_changes > 0
            else "same_version"
        ),
        "unknown": "version_order_unknown",
    }[relation]

    return VersionGuardResult(
        status=relation,
        source_version=source_marker.value,
        local_version=local_marker.value,
        marker=source_marker.name,
        source_path=source_marker.relative_path,
        target_path=target_path,
        regression=regression,
        warning=warning,
        reason=reason,
        destructive_changes=destructive_changes,
    )
