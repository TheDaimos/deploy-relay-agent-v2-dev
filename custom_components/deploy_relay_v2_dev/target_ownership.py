"""Read-only target-claim and batch-collision contract for DRA V2 DEV.

Pure validation of *server-created* source-preview reports. Never accept a
browser-supplied report as authorization. This is NOT an ownership handover,
a V1/V2 interprocess lock, a backup, or an installation permission.
"""
from __future__ import annotations

import re

from .project_catalog import CatalogError, normalize_repo
from .source_preflight import PreflightError, SHA, safe_path, target_path

SCHEMA = "dra-v2-dev-target-claims.v1"
PREVIEW_SCHEMA = "dra-v2-dev-source-preview.v1"
PROJECT_ID = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
MAX_PROJECTS = 32
MAX_EXTERNAL_TARGETS = 64
MAX_GROUPS = 12


class TargetClaimError(ValueError):
    """Generic, non-secret validation error."""


def _target(value: object) -> str:
    try:
        return target_path(value)
    except PreflightError:
        raise TargetClaimError("invalid target claim") from None


def assess_target_claims(
    source_previews: object, *, externally_occupied_targets: object = (),
) -> dict[str, object]:
    """Compute conservative cross-project target collisions without mutations.

    The input must come from an internally produced, pinned, read-only
    source-preview path. Empty external occupancy is NOT proof that V1 or
    another process does not own a path. Every result stays install-locked.
    """
    if type(source_previews) is not list or not 1 <= len(source_previews) <= MAX_PROJECTS:
        raise TargetClaimError("invalid project preview collection")
    if type(externally_occupied_targets) not in (list, tuple) or (
        len(externally_occupied_targets) > MAX_EXTERNAL_TARGETS
    ):
        raise TargetClaimError("invalid external target inventory")

    external: set[str] = set()
    for claimed in externally_occupied_targets:
        canonical = _target(claimed)
        key = canonical.casefold()
        if key in external:
            raise TargetClaimError("duplicate external target")
        external.add(key)

    projects: set[str] = set()
    repositories: set[str] = set()
    targets: dict[str, set[str]] = {}
    for preview in source_previews:
        if type(preview) is not dict or preview.get("schema") != PREVIEW_SCHEMA:
            raise TargetClaimError("untrusted source preview")
        project = preview.get("project_id")
        commit = preview.get("source_commit")
        if type(project) is not str or not PROJECT_ID.fullmatch(project):
            raise TargetClaimError("invalid project identity")
        if type(commit) is not str or SHA.fullmatch(commit) is None:
            raise TargetClaimError("source is not commit-pinned")
        try:
            repo = normalize_repo(preview.get("repository"))
        except CatalogError:
            raise TargetClaimError("invalid repository identity") from None
        if (
            preview.get("sources_verified") is not True
            or preview.get("local_inventory_readonly") is not True
            or preview.get("installation_enabled") is not False
            or preview.get("handover_required") is not True
            or preview.get("backup_verified") is not False
        ):
            raise TargetClaimError("source preview lacks read-only safety flags")
        if project in projects or repo.casefold() in repositories:
            raise TargetClaimError("duplicate project source")
        projects.add(project)
        repositories.add(repo.casefold())

        groups = preview.get("groups")
        if type(groups) is not list or not 1 <= len(groups) <= MAX_GROUPS:
            raise TargetClaimError("invalid source groups")
        own: set[str] = set()
        for group in groups:
            if type(group) is not dict or set(group) != {"source", "target"}:
                raise TargetClaimError("invalid source group")
            try:
                safe_path(group["source"])
            except PreflightError:
                raise TargetClaimError("invalid group source") from None
            root = _target(group["target"])
            key = root.casefold()
            if key in own:
                raise TargetClaimError("duplicate project target")
            own.add(key)
            targets.setdefault(key, set()).add(project)

    conflicts = sorted(
        root for root, owners in targets.items()
        if len(owners) > 1 or root in external
    )
    return {
        "schema": SCHEMA,
        "project_count": len(projects),
        "target_count": len(targets),
        "conflicting_targets": conflicts,
        "conflict_count": len(conflicts),
        "other_owners_must_be_checked": True,
        "exclusive_ownership_verified": False,
        "cross_process_lock_verified": False,
        "backup_verified": False,
        "handover_required": True,
        "installation_enabled": False,
        "parallel_installation_enabled": False,
    }
