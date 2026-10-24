"""Minimal read-only GitHub API client for Deploy Relay."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote

from aiohttp import ClientSession

from .repository import normalize_repository

_GITHUB_API = "https://api.github.com"
_API_VERSION = "2022-11-28"
_USER_AGENT = "Deploy-Relay-Agent"
_PAGE_SIZE = 100
_MAX_LIST_ITEMS = 500
_FILE_STREAM_CHUNK_BYTES = 256 * 1024
_MAX_TEXT_FILE_BYTES = 2 * 1024 * 1024


class GitHubApiError(RuntimeError):
    """Base error for GitHub API access."""


class GitHubAuthenticationError(GitHubApiError):
    """Authentication failed."""


class GitHubAccessError(GitHubApiError):
    """Repository access was forbidden."""


class GitHubNotFoundError(GitHubApiError):
    """Requested GitHub resource was not found."""


class GitHubRateLimitError(GitHubApiError):
    """GitHub API rate limit was exhausted."""


@dataclass(frozen=True, slots=True)
class GitHubRepositoryInfo:
    """Safe repository metadata used by project discovery."""

    full_name: str
    private: bool
    default_branch: str
    archived: bool
    disabled: bool


@dataclass(frozen=True, slots=True)
class GitHubNamedRef:
    """One GitHub branch or tag and its advertised commit."""

    name: str
    commit_sha: str


@dataclass(frozen=True, slots=True)
class GitHubRelease:
    """Safe release metadata required by source discovery."""

    tag_name: str
    name: str
    prerelease: bool
    draft: bool


@dataclass(frozen=True, slots=True)
class GitHubContentEntry:
    """One repository contents entry."""

    path: str
    type: str
    size: int
    sha: str


@dataclass(frozen=True, slots=True)
class GitHubListResult:
    """Bounded list result."""

    items: tuple[Any, ...]
    truncated: bool


class GitHubClient:
    """Small GitHub client with no write-capable methods."""

    def __init__(self, session: ClientSession, token: str | None = None) -> None:
        self._session = session
        self._token = token.strip() if token else None

    def _headers(self, *, raw: bool = False) -> dict[str, str]:
        headers = {
            "Accept": (
                "application/vnd.github.raw+json"
                if raw
                else "application/vnd.github+json"
            ),
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _USER_AGENT,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _raise_for_status(self, response: Any) -> None:
        if response.status < 400:
            return
        if response.status == 401:
            raise GitHubAuthenticationError("GitHub authentication failed")
        if response.status == 404:
            raise GitHubNotFoundError("GitHub resource not found")
        if response.status == 403:
            if response.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubRateLimitError("GitHub API rate limit exhausted")
            raise GitHubAccessError("GitHub access forbidden")
        raise GitHubApiError(f"GitHub API returned HTTP {response.status}")

    def _repository_url(self, repository: str, suffix: str = "") -> str:
        normalized = normalize_repository(repository)
        owner, name = normalized.split("/", 1)
        base = f"{_GITHUB_API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        return f"{base}{suffix}"

    def _contents_url(self, repository: str, path: str) -> str:
        safe_path = "/".join(quote(part, safe="") for part in path.split("/"))
        return self._repository_url(repository, f"/contents/{safe_path}")

    async def _async_get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        async with self._session.get(
            url,
            headers=self._headers(),
            params=params,
        ) as response:
            await self._raise_for_status(response)
            return await response.json()

    async def _async_list_json(
        self,
        url: str,
        *,
        limit: int = _MAX_LIST_ITEMS,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Read a bounded paginated GitHub list."""
        if limit < 1:
            raise ValueError("limit must be positive")

        items: list[dict[str, Any]] = []
        page = 1

        while len(items) < limit:
            payload = await self._async_get_json(
                url,
                params={"per_page": _PAGE_SIZE, "page": page},
            )
            if not isinstance(payload, list) or any(
                not isinstance(item, dict) for item in payload
            ):
                raise GitHubApiError("GitHub list response is invalid")

            remaining = limit - len(items)
            items.extend(payload[:remaining])

            if len(payload) < _PAGE_SIZE:
                return items, False
            if len(items) >= limit:
                return items, True

            page += 1

        return items, True

    async def async_get_repository(self, repository: str) -> GitHubRepositoryInfo:
        """Read repository metadata."""
        payload = await self._async_get_json(self._repository_url(repository))

        if not isinstance(payload, dict):
            raise GitHubApiError("GitHub repository response is invalid")

        full_name = payload.get("full_name")
        default_branch = payload.get("default_branch")
        if not isinstance(full_name, str) or not isinstance(default_branch, str):
            raise GitHubApiError("GitHub repository metadata is incomplete")

        return GitHubRepositoryInfo(
            full_name=normalize_repository(full_name),
            private=bool(payload.get("private", False)),
            default_branch=default_branch,
            archived=bool(payload.get("archived", False)),
            disabled=bool(payload.get("disabled", False)),
        )

    async def async_list_branches(self, repository: str) -> GitHubListResult:
        """List a bounded set of repository branches."""
        payload, truncated = await self._async_list_json(
            self._repository_url(repository, "/branches")
        )
        values: list[GitHubNamedRef] = []
        for item in payload:
            name = item.get("name")
            commit = item.get("commit")
            sha = commit.get("sha") if isinstance(commit, dict) else None
            if not isinstance(name, str) or not name or not isinstance(sha, str) or not sha:
                raise GitHubApiError("GitHub branch response is invalid")
            values.append(GitHubNamedRef(name=name, commit_sha=sha))
        return GitHubListResult(tuple(values), truncated)

    async def async_list_tags(self, repository: str) -> GitHubListResult:
        """List a bounded set of repository tags."""
        payload, truncated = await self._async_list_json(
            self._repository_url(repository, "/tags")
        )
        values: list[GitHubNamedRef] = []
        for item in payload:
            name = item.get("name")
            commit = item.get("commit")
            sha = commit.get("sha") if isinstance(commit, dict) else None
            if not isinstance(name, str) or not name or not isinstance(sha, str) or not sha:
                raise GitHubApiError("GitHub tag response is invalid")
            values.append(GitHubNamedRef(name=name, commit_sha=sha))
        return GitHubListResult(tuple(values), truncated)

    async def async_list_releases(self, repository: str) -> GitHubListResult:
        """List a bounded set of repository releases."""
        payload, truncated = await self._async_list_json(
            self._repository_url(repository, "/releases")
        )
        values: list[GitHubRelease] = []
        for item in payload:
            tag_name = item.get("tag_name")
            name = item.get("name")
            if not isinstance(tag_name, str) or not tag_name:
                raise GitHubApiError("GitHub release response is invalid")
            values.append(
                GitHubRelease(
                    tag_name=tag_name,
                    name=name if isinstance(name, str) and name else tag_name,
                    prerelease=bool(item.get("prerelease", False)),
                    draft=bool(item.get("draft", False)),
                )
            )
        return GitHubListResult(tuple(values), truncated)

    async def async_resolve_commit(self, repository: str, ref: str) -> str:
        """Resolve a branch, tag, release tag or commit ref to canonical commit SHA."""
        if not isinstance(ref, str) or not ref.strip():
            raise GitHubApiError("GitHub ref must be a non-empty string")
        payload = await self._async_get_json(
            self._repository_url(
                repository,
                f"/commits/{quote(ref.strip(), safe='')}",
            )
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("sha"), str):
            raise GitHubApiError("GitHub commit response is invalid")
        sha = payload["sha"]
        if not sha:
            raise GitHubApiError("GitHub commit SHA is empty")
        return sha

    async def async_list_directory(
        self,
        repository: str,
        path: str,
        *,
        ref: str,
    ) -> tuple[GitHubContentEntry, ...]:
        """List one repository directory at an exact ref."""
        payload = await self._async_get_json(
            self._contents_url(repository, path),
            params={"ref": ref},
        )
        if not isinstance(payload, list):
            raise GitHubApiError("GitHub contents path is not a directory")
        if len(payload) >= 1000:
            raise GitHubApiError(
                "GitHub contents directory may be truncated at 1000 entries"
            )

        entries: list[GitHubContentEntry] = []
        for item in payload:
            if not isinstance(item, dict):
                raise GitHubApiError("GitHub contents response is invalid")
            item_path = item.get("path")
            item_type = item.get("type")
            item_size = item.get("size", 0)
            item_sha = item.get("sha", "")
            if (
                not isinstance(item_path, str)
                or not item_path
                or not isinstance(item_type, str)
                or not item_type
                or not isinstance(item_size, int)
                or isinstance(item_size, bool)
                or item_size < 0
                or not isinstance(item_sha, str)
            ):
                raise GitHubApiError("GitHub contents entry is invalid")
            entries.append(
                GitHubContentEntry(
                    path=item_path,
                    type=item_type,
                    size=item_size,
                    sha=item_sha,
                )
            )
        return tuple(entries)

    async def async_iter_file_bytes(
        self,
        repository: str,
        path: str,
        *,
        ref: str,
        max_bytes: int | None = None,
        chunk_size: int = _FILE_STREAM_CHUNK_BYTES,
    ) -> AsyncIterator[bytes]:
        """Stream one repository file from an exact ref with a hard byte budget."""
        if max_bytes is not None and max_bytes < 0:
            raise ValueError("max_bytes must be non-negative")
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")

        async with self._session.get(
            self._contents_url(repository, path),
            headers=self._headers(raw=True),
            params={"ref": ref},
        ) as response:
            await self._raise_for_status(response)

            if max_bytes is not None:
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        advertised = int(content_length)
                    except ValueError:
                        advertised = -1
                    if advertised > max_bytes:
                        raise GitHubApiError("GitHub file exceeds allowed byte budget")

            total = 0
            async for chunk in response.content.iter_chunked(chunk_size):
                if not chunk:
                    continue
                total += len(chunk)
                if max_bytes is not None and total > max_bytes:
                    raise GitHubApiError("GitHub file exceeds allowed byte budget")
                yield bytes(chunk)

    async def async_get_file_bytes(
        self,
        repository: str,
        path: str,
        *,
        ref: str,
        max_bytes: int | None = None,
    ) -> bytes:
        """Read a bounded repository file as bytes from an exact ref."""
        chunks = bytearray()
        async for chunk in self.async_iter_file_bytes(
            repository,
            path,
            ref=ref,
            max_bytes=max_bytes,
        ):
            chunks.extend(chunk)
        return bytes(chunks)

    async def async_get_text_file(
        self,
        repository: str,
        path: str,
        *,
        ref: str,
        max_bytes: int = _MAX_TEXT_FILE_BYTES,
    ) -> str:
        """Read one bounded UTF-8 repository text file from GitHub."""
        raw = await self.async_get_file_bytes(
            repository,
            path,
            ref=ref,
            max_bytes=max_bytes,
        )
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as err:
            raise GitHubApiError("GitHub file is not valid UTF-8 text") from err
