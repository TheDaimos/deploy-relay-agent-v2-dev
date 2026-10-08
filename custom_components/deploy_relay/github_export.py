"""Narrow GitHub writer for sanitized Deploy Relay diagnostic exports."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from aiohttp import ClientSession

from .const import DIAGNOSTIC_GIT_ROOT
from .github_client import (
    GitHubAccessError,
    GitHubApiError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
)
from .path_policy import normalize_relative_path
from .redaction import redact_value
from .repository import normalize_repository

_GITHUB_API = "https://api.github.com"
_API_VERSION = "2022-11-28"
_USER_AGENT = "Deploy-Relay-Agent"
_SLUG_INVALID = re.compile(r"[^a-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class DiagnosticGitExportResult:
    """Result of one sanitized diagnostic Git export."""

    repository: str
    branch: str
    path: str
    commit_sha: str
    commit_url: str | None
    file_url: str | None


def _slug(value: str, *, fallback: str) -> str:
    normalized = _SLUG_INVALID.sub("-", value.casefold()).strip("-._")
    return normalized[:80] or fallback


def build_diagnostic_export_path(
    *,
    project_id: str,
    source_ref: str | None,
    source_commit: str | None,
    now: datetime | None = None,
) -> str:
    """Return a unique reserved repository path for one support bundle."""
    current = now or datetime.now(UTC)
    project = _slug(project_id, fallback="project")
    ref = _slug(source_ref or "source", fallback="source")
    commit = _slug((source_commit or "no-commit")[:12], fallback="no-commit")
    stamp = current.strftime("%Y%m%dT%H%M%SZ")
    day = current.strftime("%Y-%m-%d")
    suffix = uuid4().hex[:8]
    path = (
        f"{DIAGNOSTIC_GIT_ROOT}/{project}/{day}/"
        f"{stamp}-{ref}-{commit}-{suffix}.json"
    )
    return normalize_relative_path(path).as_posix()


class DiagnosticGitExportClient:
    """Write sanitized support bundles to the reserved diagnostics path only."""

    def __init__(self, session: ClientSession, token: str) -> None:
        token = token.strip()
        if not token:
            raise ValueError("diagnostic Git export token is required")
        self._session = session
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _USER_AGENT,
        }

    @staticmethod
    def _contents_url(repository: str, path: str) -> str:
        normalized = normalize_repository(repository)
        owner, name = normalized.split("/", 1)
        safe_path = "/".join(quote(part, safe="") for part in path.split("/"))
        return (
            f"{_GITHUB_API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
            f"/contents/{safe_path}"
        )

    async def _raise_for_status(self, response: Any) -> None:
        if response.status < 400:
            return
        if response.status == 401:
            raise GitHubAuthenticationError("GitHub authentication failed")
        if response.status == 403:
            if response.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubRateLimitError("GitHub API rate limit exhausted")
            raise GitHubAccessError("GitHub write access forbidden")
        raise GitHubApiError(
            f"GitHub diagnostic export returned HTTP {response.status}"
        )

    async def async_export(
        self,
        *,
        repository: str,
        branch: str,
        project_id: str,
        source_ref: str | None,
        source_commit: str | None,
        support_bundle: dict[str, Any],
    ) -> DiagnosticGitExportResult:
        """Commit one redacted JSON support bundle as a new file."""
        if not branch.strip():
            raise ValueError("diagnostic Git export branch is required")

        path = build_diagnostic_export_path(
            project_id=project_id,
            source_ref=source_ref,
            source_commit=source_commit,
        )
        reserved_prefix = f"{DIAGNOSTIC_GIT_ROOT}/"
        if not path.startswith(reserved_prefix):
            raise ValueError("diagnostic export path escaped reserved Git root")

        payload = {
            "format": "deploy-relay-git-diagnostics-v1",
            "exported_at": datetime.now(UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "repository": normalize_repository(repository),
            "branch": branch,
            "path": path,
            "support_bundle": support_bundle,
        }
        sanitized = redact_value(payload, [self._token])
        encoded = base64.b64encode(
            (
                json.dumps(
                    sanitized,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
        ).decode("ascii")

        body = {
            "message": "chore(diagnostics): export Deploy Relay support bundle [skip ci]",
            "content": encoded,
            "branch": branch,
        }

        async with self._session.put(
            self._contents_url(repository, path),
            headers=self._headers(),
            json=body,
        ) as response:
            await self._raise_for_status(response)
            result = await response.json()

        if not isinstance(result, dict):
            raise GitHubApiError("GitHub diagnostic export response is invalid")

        commit = result.get("commit")
        content = result.get("content")
        commit_sha = commit.get("sha") if isinstance(commit, dict) else None
        commit_url = commit.get("html_url") if isinstance(commit, dict) else None
        file_url = content.get("html_url") if isinstance(content, dict) else None

        if not isinstance(commit_sha, str) or not commit_sha:
            raise GitHubApiError("GitHub diagnostic export commit SHA is missing")

        return DiagnosticGitExportResult(
            repository=normalize_repository(repository),
            branch=branch,
            path=path,
            commit_sha=commit_sha,
            commit_url=commit_url if isinstance(commit_url, str) else None,
            file_url=file_url if isinstance(file_url, str) else None,
        )
