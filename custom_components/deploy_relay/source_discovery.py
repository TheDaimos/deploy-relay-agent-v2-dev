"""Read-only source/version discovery for Deploy Relay."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from aiohttp import ClientSession

from .const import DEFAULT_MANIFEST_PATH
from .github_client import GitHubClient, GitHubNotFoundError
from .manifest import DeploymentManifest, ManifestError, parse_manifest
from .path_policy import normalize_relative_path
from .repository import normalize_repository

_COMMIT_INPUT = re.compile(r"^[0-9a-fA-F]{7,64}$")
_FROZEN_COMMIT = re.compile(r"^[0-9a-fA-F]{40,64}$")


class SourceDiscoveryError(RuntimeError):
    """Source discovery or resolution failed."""


class SourceManifestNotFound(SourceDiscoveryError):
    """Selected source contains no deployment manifest."""


class SourceKind(StrEnum):
    """Supported source identity kinds."""

    BRANCH = "branch"
    TAG = "tag"
    RELEASE = "release"
    COMMIT = "commit"


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """One selectable source returned by GitHub discovery."""

    kind: SourceKind
    ref: str
    commit_sha: str | None
    label: str
    prerelease: bool = False


@dataclass(frozen=True, slots=True)
class SourceDiscoveryResult:
    """Bounded source candidate collection."""

    repository: str
    default_branch: str
    candidates: tuple[SourceCandidate, ...]
    truncated: bool


@dataclass(frozen=True, slots=True)
class ResolvedSource:
    """Immutable selected source identity plus validated manifest."""

    kind: SourceKind
    requested_ref: str
    commit_sha: str
    manifest: DeploymentManifest


async def async_discover_sources(
    session: ClientSession,
    repository: str,
    *,
    token: str | None = None,
) -> SourceDiscoveryResult:
    """Discover branches, tags and non-draft releases without writing anything."""
    normalized = normalize_repository(repository)
    client = GitHubClient(session, token)

    info = await client.async_get_repository(normalized)
    branches = await client.async_list_branches(info.full_name)
    tags = await client.async_list_tags(info.full_name)
    releases = await client.async_list_releases(info.full_name)

    candidates: list[SourceCandidate] = []

    ordered_branches = sorted(
        branches.items,
        key=lambda item: (item.name != info.default_branch, item.name.casefold()),
    )
    for item in ordered_branches:
        suffix = " (default)" if item.name == info.default_branch else ""
        candidates.append(
            SourceCandidate(
                kind=SourceKind.BRANCH,
                ref=item.name,
                commit_sha=item.commit_sha,
                label=f"Branch · {item.name}{suffix}",
            )
        )

    for item in tags.items:
        candidates.append(
            SourceCandidate(
                kind=SourceKind.TAG,
                ref=item.name,
                commit_sha=item.commit_sha,
                label=f"Tag · {item.name}",
            )
        )

    for item in releases.items:
        if item.draft:
            continue
        suffix = " · prerelease" if item.prerelease else ""
        name = item.name if item.name == item.tag_name else f"{item.name} ({item.tag_name})"
        candidates.append(
            SourceCandidate(
                kind=SourceKind.RELEASE,
                ref=item.tag_name,
                commit_sha=None,
                label=f"Release · {name}{suffix}",
                prerelease=item.prerelease,
            )
        )

    return SourceDiscoveryResult(
        repository=info.full_name,
        default_branch=info.default_branch,
        candidates=tuple(candidates),
        truncated=branches.truncated or tags.truncated or releases.truncated,
    )


async def async_load_frozen_manifest(
    session: ClientSession,
    repository: str,
    *,
    commit_sha: str,
    token: str | None = None,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    expected_project_id: str | None = None,
) -> DeploymentManifest:
    """Read and validate a manifest from an already frozen commit SHA."""
    normalized_repository = normalize_repository(repository)
    normalized_manifest_path = normalize_relative_path(manifest_path).as_posix()

    if not isinstance(commit_sha, str) or not _FROZEN_COMMIT.fullmatch(commit_sha):
        raise SourceDiscoveryError("stored source commit is not a canonical commit SHA")

    client = GitHubClient(session, token)
    try:
        raw_manifest = await client.async_get_text_file(
            normalized_repository,
            normalized_manifest_path,
            ref=commit_sha,
        )
    except GitHubNotFoundError as err:
        raise SourceManifestNotFound(
            "frozen source contains no deployment manifest"
        ) from err

    try:
        return parse_manifest(
            raw_manifest,
            expected_repository=normalized_repository,
            expected_project_id=expected_project_id,
        )
    except ManifestError as err:
        raise SourceDiscoveryError(
            f"frozen source contains an invalid deployment manifest: {err}"
        ) from err


async def async_resolve_source(
    session: ClientSession,
    repository: str,
    *,
    kind: SourceKind | str,
    ref: str,
    token: str | None = None,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    expected_project_id: str | None = None,
) -> ResolvedSource:
    """Freeze a selected source to a commit SHA and validate that SHA's manifest."""
    normalized_repository = normalize_repository(repository)

    try:
        source_kind = SourceKind(kind)
    except ValueError as err:
        raise SourceDiscoveryError("unsupported source kind") from err

    if not isinstance(ref, str) or not ref.strip():
        raise SourceDiscoveryError("source ref must be a non-empty string")
    requested_ref = ref.strip()

    if source_kind is SourceKind.COMMIT and not _COMMIT_INPUT.fullmatch(requested_ref):
        raise SourceDiscoveryError("manual commit must be a hexadecimal commit id")

    client = GitHubClient(session, token)
    commit_sha = await client.async_resolve_commit(
        normalized_repository,
        requested_ref,
    )

    manifest = await async_load_frozen_manifest(
        session,
        normalized_repository,
        commit_sha=commit_sha,
        token=token,
        manifest_path=manifest_path,
        expected_project_id=expected_project_id,
    )

    return ResolvedSource(
        kind=source_kind,
        requested_ref=requested_ref,
        commit_sha=commit_sha,
        manifest=manifest,
    )
