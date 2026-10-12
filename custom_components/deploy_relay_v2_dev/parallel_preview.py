"""Bounded multicore execution of independent *real* V1 preview groups.

Reuses the original V1 build_preview() without duplicating its filesystem and
hashing semantics. CPU-intensive target hashing of disjoint deployment groups
may run in separate processes. One-group projects take the original V1 path.
No writes, no browser-supplied paths, no mutable authorization decisions.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from dataclasses import replace
import multiprocessing
import os
from pathlib import Path

from .v1_engine.manifest import DeploymentManifest
from .v1_engine.planner import build_plan
from .v1_engine.preview import PreviewResult, build_preview
from .v1_engine.source_inventory import SourceInventory

MAX_WORKERS = 4
MAX_PARALLEL_GROUPS = 32
GROUP_TIMEOUT_SECONDS = 180


def _group_preview(
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    group_index: int,
    config_root: Path,
) -> PreviewResult:
    """Executed in a fresh worker process; no Home Assistant dependencies."""
    group = manifest.groups[group_index]
    matching = [g for g in inventory.groups if g.group_id == group.id]
    if len(matching) != 1:
        raise ValueError("inventory group identity mismatch")
    reduced_manifest = replace(manifest, groups=(group,))
    reduced_inventory = replace(inventory, groups=(matching[0],))
    return build_preview(reduced_manifest, reduced_inventory, config_root=config_root)


def _parallel_worker_group_previews(
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    config_root: Path,
    workers: int,
) -> PreviewResult:
    # Run the potentially blocking process startup/shutdown in an executor
    # thread, never on HA's event loop.
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as pool:
        futures = [
            pool.submit(_group_preview, manifest, inventory, index, config_root)
            for index in range(len(manifest.groups))
        ]
        parts = [future.result(timeout=GROUP_TIMEOUT_SECONDS) for future in futures]
    return PreviewResult(
        project_id=inventory.project_id,
        repository=inventory.repository,
        source_ref=inventory.source_ref,
        source_commit=inventory.source_commit,
        files=tuple(item for part in parts for item in part.files),
    )


async def async_build_parallel_preview(
    manifest: DeploymentManifest,
    inventory: SourceInventory,
    *, config_root: Path,
    max_workers: int = MAX_WORKERS,
) -> PreviewResult:
    """Build the same V1 preview, using processes only for independent groups.

    Any overlap, duplicate or mismatching group fails before spawning.
    If multiple cores or safe process startup are unavailable, perform the
    *same* V1 algorithm serially. Never use a partial parallel result.
    """
    if (type(manifest) is not DeploymentManifest
        or type(inventory) is not SourceInventory
        or not isinstance(config_root, Path)
        or config_root.is_symlink()
        or type(max_workers) is not int
        or not 1 <= max_workers <= MAX_WORKERS):
        raise ValueError("invalid V1 parallel preview inputs")
    plan = build_plan(
        manifest, source_ref=inventory.source_ref,
        source_commit=inventory.source_commit,
    )
    ids = [g.id for g in inventory.groups]
    if (len(ids) != len(plan.groups)
        or len(ids) != len(set(ids))
        or set(ids) != {g.id for g in plan.groups}
        or inventory.project_id != manifest.project_id
        or inventory.repository.casefold() != manifest.repository.casefold()):
        raise ValueError("manifest and inventory groups do not match")
    cores = os.cpu_count() or 1
    workers = min(max_workers, len(plan.groups), max(1, cores))
    if workers <= 1 or len(plan.groups) > MAX_PARALLEL_GROUPS:
        return await asyncio.to_thread(build_preview, manifest, inventory,
                                       config_root=config_root)
    try:
        return await asyncio.to_thread(
            _parallel_worker_group_previews,
            manifest, inventory, config_root, workers,
        )
    except (BrokenProcessPool, OSError):
        # Process creation may be unavailable in limited HA installations.
        # The complete original V1 preview is the deterministic fallback.
        return await asyncio.to_thread(build_preview, manifest, inventory,
                                       config_root=config_root)
