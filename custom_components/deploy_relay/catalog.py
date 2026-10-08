"""Project catalog parsing for Deploy Relay."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from .const import CATALOG_SCHEMA_VERSION
from .path_policy import normalize_relative_path

_PROJECT_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ALLOWED_STATUS = frozenset({"manifest_pending", "ready", "paused"})


class CatalogError(ValueError):
    """Raised when the central project catalog is invalid."""


@dataclass(frozen=True, slots=True)
class CatalogProject:
    id: str
    name: str
    repository: str
    manifest_path: str
    status: str
    channel: str


def parse_catalog(raw: str | bytes | dict[str, Any]) -> tuple[CatalogProject, ...]:
    """Parse the central project catalog."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as err:
            raise CatalogError(f"invalid JSON: {err.msg}") from err
    else:
        data = raw

    if not isinstance(data, dict) or data.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise CatalogError("unsupported catalog schema")

    values = data.get("projects")
    if not isinstance(values, list):
        raise CatalogError("projects must be a list")

    seen: set[str] = set()
    projects: list[CatalogProject] = []
    for item in values:
        if not isinstance(item, dict):
            raise CatalogError("project entry must be an object")
        project_id = item.get("id")
        name = item.get("name")
        repository = item.get("repository")
        manifest_path = item.get("manifest_path")
        status = item.get("status")
        channel = item.get("channel")

        if not isinstance(project_id, str) or not _PROJECT_ID.fullmatch(project_id):
            raise CatalogError("invalid project id")
        if project_id in seen:
            raise CatalogError(f"duplicate project id {project_id!r}")
        seen.add(project_id)
        if not isinstance(name, str) or not name:
            raise CatalogError("invalid project name")
        if not isinstance(repository, str) or not _REPOSITORY.fullmatch(repository):
            raise CatalogError("invalid repository")
        if not isinstance(manifest_path, str):
            raise CatalogError("invalid manifest path")
        manifest_path = normalize_relative_path(manifest_path).as_posix()
        if status not in _ALLOWED_STATUS:
            raise CatalogError("invalid project status")
        if not isinstance(channel, str) or not channel:
            raise CatalogError("invalid channel")

        projects.append(
            CatalogProject(
                id=project_id,
                name=name,
                repository=repository,
                manifest_path=manifest_path,
                status=status,
                channel=channel,
            )
        )

    return tuple(projects)
