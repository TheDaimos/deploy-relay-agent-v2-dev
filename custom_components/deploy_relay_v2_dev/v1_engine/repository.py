"""GitHub repository identity helpers."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_PROJECT_ID_INVALID = re.compile(r"[^a-z0-9_]+")


class RepositoryIdentityError(ValueError):
    """Raised when a repository identity is invalid."""


def normalize_repository(value: str) -> str:
    """Normalize owner/repository or a supported GitHub URL."""
    if not isinstance(value, str):
        raise RepositoryIdentityError("repository must be a string")

    candidate = value.strip()
    if not candidate:
        raise RepositoryIdentityError("repository must not be empty")

    if candidate.startswith("git@github.com:"):
        candidate = candidate.removeprefix("git@github.com:")
    elif "://" in candidate:
        parsed = urlparse(candidate)
        if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
            raise RepositoryIdentityError("only https://github.com repository URLs are supported")
        if parsed.query or parsed.fragment or parsed.params:
            raise RepositoryIdentityError("repository URL must not contain query or fragment data")
        candidate = parsed.path.strip("/")

    if candidate.endswith(".git"):
        candidate = candidate[:-4]

    if not _REPOSITORY.fullmatch(candidate):
        raise RepositoryIdentityError("repository must use owner/repository format")

    owner, repository = candidate.split("/", 1)
    if owner in {".", ".."} or repository in {".", ".."}:
        raise RepositoryIdentityError("invalid repository identity")

    return f"{owner}/{repository}"


def provisional_project_id(repository: str) -> str:
    """Create a safe provisional id for a repository without a manifest."""
    normalized = normalize_repository(repository)
    name = normalized.split("/", 1)[1].lower().replace("-", "_").replace(".", "_")
    name = _PROJECT_ID_INVALID.sub("_", name).strip("_")
    if not name:
        name = "project"
    if not name[0].isalpha():
        name = f"project_{name}"
    return name


def provisional_project_name(repository: str) -> str:
    """Return a human-readable provisional project name."""
    normalized = normalize_repository(repository)
    return normalized.split("/", 1)[1]
