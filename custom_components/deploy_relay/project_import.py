"""Read-only project import and discovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aiohttp import ClientSession

from .const import DEFAULT_MANIFEST_PATH
from .github_client import (
    GitHubClient,
    GitHubNotFoundError,
    GitHubRepositoryInfo,
)
from .manifest import DeploymentManifest, ManifestError, parse_manifest
from .path_policy import normalize_relative_path
from .repository import (
    normalize_repository,
    provisional_project_id,
    provisional_project_name,
)


class ProjectImportError(RuntimeError):
    """Project discovery failed."""


class ProjectImportStatus(StrEnum):
    """Read-only import status."""

    READY = "ready"
    MANIFEST_PENDING = "manifest_pending"


@dataclass(frozen=True, slots=True)
class ProjectImportResult:
    """Validated read-only result for one imported project."""

    project_id: str
    project_name: str
    repository: str
    manifest_path: str
    default_branch: str
    private: bool
    archived: bool
    status: ProjectImportStatus
    manifest: DeploymentManifest | None

    def as_subentry_data(self) -> dict[str, object]:
        """Return secret-free persistent Home Assistant subentry data."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "repository": self.repository,
            "manifest_path": self.manifest_path,
            "default_branch": self.default_branch,
            "private": self.private,
            "archived": self.archived,
            "status": self.status.value,
        }


async def async_probe_project(
    session: ClientSession,
    repository: str,
    *,
    token: str | None = None,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
) -> ProjectImportResult:
    """Probe repository metadata and its default-branch Deploy Relay manifest."""
    normalized_repository = normalize_repository(repository)
    normalized_manifest_path = normalize_relative_path(manifest_path).as_posix()
    client = GitHubClient(session, token)

    info: GitHubRepositoryInfo = await client.async_get_repository(normalized_repository)
    if info.disabled:
        raise ProjectImportError("repository is disabled")

    try:
        raw_manifest = await client.async_get_text_file(
            info.full_name,
            normalized_manifest_path,
            ref=info.default_branch,
        )
    except GitHubNotFoundError:
        return ProjectImportResult(
            project_id=provisional_project_id(info.full_name),
            project_name=provisional_project_name(info.full_name),
            repository=info.full_name,
            manifest_path=normalized_manifest_path,
            default_branch=info.default_branch,
            private=info.private,
            archived=info.archived,
            status=ProjectImportStatus.MANIFEST_PENDING,
            manifest=None,
        )

    try:
        manifest = parse_manifest(
            raw_manifest,
            expected_repository=info.full_name,
        )
    except ManifestError as err:
        raise ProjectImportError(f"invalid deployment manifest: {err}") from err

    return ProjectImportResult(
        project_id=manifest.project_id,
        project_name=manifest.project_name,
        repository=info.full_name,
        manifest_path=normalized_manifest_path,
        default_branch=info.default_branch,
        private=info.private,
        archived=info.archived,
        status=ProjectImportStatus.READY,
        manifest=manifest,
    )
