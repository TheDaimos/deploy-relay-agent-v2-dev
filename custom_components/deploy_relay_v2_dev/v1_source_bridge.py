"""Freeze a Git source and prepare the proven V1 deployment input for V2.

This is a backend-only adapter: no writing, browser authorization or WebSocket
route. Uses the V1 manifest, source inventory and local target comparison.
All remote source bytes are read from the exact pinned commit, not a branch.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .v1_engine.github_client import GitHubClient
from .v1_engine.manifest import DeploymentManifest, parse_manifest
from .v1_engine.preview import PreviewResult
from .parallel_preview import async_build_parallel_preview
from .v1_engine.repository import normalize_repository
from .v1_engine.source_inventory import SourceInventory, async_build_source_inventory

COMMIT = re.compile(r"[0-9a-f]{40}\Z")
PROJECT = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
MAX_MANIFEST_BYTES = 262144


class SourceBridgeError(ValueError):
    """Safe stage-labelled failure; never includes tokens or remote payloads."""

    def __init__(self, message: str, *, check_stage: str = "source_reference") -> None:
        super().__init__(message)
        self.check_stage = check_stage


@dataclass(frozen=True, slots=True)
class PreparedV1Source:
    manifest: DeploymentManifest
    inventory: SourceInventory
    preview: PreviewResult


async def prepare_frozen_v1_source(
    *, session: Any, repository: str, source_ref: str,
    source_commit: str, expected_project_id: str,
    config_root: Path, token: str | None = None,
    manifest_path: str = "deploy-relay.json",
) -> PreparedV1Source:
    """Build immutable V1 objects for one server-chosen registered project.

    This must be called only by a trusted backend with a server-registered
    repository and fixed commit. It never writes any project or backup data.
    """
    if (type(repository) is not str or not repository or
        type(source_ref) is not str or not 1 <= len(source_ref) <= 255 or
        type(source_commit) is not str or not COMMIT.fullmatch(source_commit) or
        type(expected_project_id) is not str or not PROJECT.fullmatch(expected_project_id) or
        not isinstance(config_root, Path) or config_root.is_symlink() or
        type(manifest_path) is not str or manifest_path != "deploy-relay.json" or
        token is not None and type(token) is not str):
        raise SourceBridgeError("invalid source identity")
    try:
        normalized = normalize_repository(repository)
    except (ValueError, TypeError):
        raise SourceBridgeError("invalid source repository") from None
    if normalized.casefold() != repository.casefold():
        raise SourceBridgeError("unexpected repository spelling")
    client = GitHubClient(session, token)
    # Prove that the supplied SHA is a real, immutable commit in this repo.
    try:
        resolved = await client.async_resolve_commit(normalized, source_commit)
    except Exception:
        raise SourceBridgeError("source commit not verifiable") from None
    if resolved != source_commit:
        raise SourceBridgeError("source moved unexpectedly")
    try:
        raw = await client.async_get_file_bytes(
            normalized, manifest_path, ref=source_commit,
            max_bytes=MAX_MANIFEST_BYTES,
        )
        manifest = parse_manifest(raw, expected_repository=normalized,
                                  expected_project_id=expected_project_id)
    except Exception:
        raise SourceBridgeError("verified manifest unavailable or invalid",
                                check_stage="manifest") from None
    try:
        inventory = await async_build_source_inventory(
            session, manifest, source_ref=source_ref,
            source_commit=source_commit, token=token)
    except Exception:
        raise SourceBridgeError("verified source inventory unavailable",
                                check_stage="inventory") from None
    try:
        preview = await async_build_parallel_preview(
            manifest, inventory, config_root=config_root,
        )
    except Exception:
        raise SourceBridgeError("local comparison not safely possible",
                                check_stage="local_comparison") from None
    if (preview.source_commit != source_commit or
        preview.project_id != expected_project_id or
        inventory.repository.casefold() != normalized.casefold()):
        raise SourceBridgeError("source preview identity mismatch",
                                check_stage="local_comparison")
    return PreparedV1Source(manifest,inventory,preview)
