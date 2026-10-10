"""Bounded public GitHub source preview, never writes to Home Assistant.

Private repositories require a future independent V2 read-only credential flow:
V1 credentials and the public diagnostics export token must NEVER be borrowed.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import json
import os
from pathlib import Path
from stat import S_ISDIR, S_ISLNK, S_ISREG
from urllib.parse import quote

from .project_catalog import normalize_repo, CatalogError
from .source_preflight import (
    MAX_BYTES, MAX_FILES, MAX_MANIFEST_BYTES, MAX_TREE, PreflightError,
    compare_blobs, git_blob_sha, inspect_tree, parse_manifest, safe_path, target_path,
)

API = "https://api.github.com"
MAX_RESPONSE = 4 * 1024 * 1024
READ_AUTH_SCHEMA = "dra-v2-dev-git-read-auth.v1"



class GitReadAuthError(ValueError):
    """Redacted private GitHub read-auth configuration error."""


class GitReadAuth:
    """Private V2 HA Store, never V1 token or V2 measurement export credential."""

    def __init__(self, store):
        self._store = store
        self._lock = asyncio.Lock()
        self._token = None
        self._loaded = False

    @property
    def configured(self):
        return self._loaded and self._token is not None

    @property
    def token(self):
        # Internal server use only. Never put token into websocket result.
        if not self._loaded:
            return None
        return self._token

    async def load(self):
        try:
            obj = await self._store.async_load()
        except Exception:
            raise GitReadAuthError("GitHub read-auth not available") from None
        if obj is None:
            self._token = None
            self._loaded = True
            return
        if type(obj) is not dict or set(obj) != {"schema", "token"} or obj["schema"] != READ_AUTH_SCHEMA:
            raise GitReadAuthError("invalid GitHub read-auth store")
        token = obj["token"]
        if token is not None and not self._valid_token(token):
            raise GitReadAuthError("invalid GitHub read-auth token")
        self._token = token
        self._loaded = True

    @staticmethod
    def _valid_token(value):
        return (
            type(value) is str
            and 10 <= len(value) <= 512
            and all(c.isascii() and not c.isspace() and c.isprintable() for c in value)
            and "/" not in value and "\\" not in value and ":" not in value
        )

    async def configure(self, token):
        if not self._valid_token(token):
            raise GitReadAuthError("invalid GitHub read-auth value")
        async with self._lock:
            if not self._loaded:
                raise GitReadAuthError("GitHub read-auth unavailable")
            try:
                await self._store.async_save({"schema": READ_AUTH_SCHEMA, "token": token})
            except Exception:
                raise GitReadAuthError("GitHub read-auth save failed") from None
            self._token = token

    async def clear(self):
        async with self._lock:
            if not self._loaded:
                raise GitReadAuthError("GitHub read-auth unavailable")
            try:
                await self._store.async_save({"schema": READ_AUTH_SCHEMA, "token": None})
            except Exception:
                raise GitReadAuthError("GitHub read-auth clear failed") from None
            self._token = None

class ProjectReadAuth:
    """Separate per-project V2-only secret store. Never return raw tokens to the panel."""
    SCHEMA = "dra-v2-dev-project-read-auth.v1"

    def __init__(self, store):
        self._store = store
        self._lock = asyncio.Lock()
        self._tokens = None

    async def load(self):
        try:
            obj = await self._store.async_load()
        except Exception:
            raise GitReadAuthError("project auth unavailable") from None
        if obj is None:
            self._tokens = {}
            return
        if type(obj) is not dict or set(obj) != {"schema", "tokens"} or obj["schema"] != self.SCHEMA:
            raise GitReadAuthError("project auth store invalid")
        entries = obj["tokens"]
        if type(entries) is not dict or len(entries) > 32:
            raise GitReadAuthError("project auth records invalid")
        from .project_catalog import normalize_repo, CatalogError
        checked = {}
        for repo, token in entries.items():
            try:
                name = normalize_repo(repo).casefold()
            except CatalogError:
                raise GitReadAuthError("invalid project auth identity") from None
            if name in checked or not GitReadAuth._valid_token(token):
                raise GitReadAuthError("invalid project auth secret")
            checked[name] = token
        self._tokens = checked

    def token(self, repository):
        if self._tokens is None:
            return None
        return self._tokens.get(repository.casefold())

    def status(self, repository):
        value = self.token(repository)
        return {"configured": value is not None, "suffix": value[-5:] if value else None}

    async def save(self, repository, token):
        from .project_catalog import normalize_repo
        key = normalize_repo(repository).casefold()
        if not GitReadAuth._valid_token(token):
            raise GitReadAuthError("invalid project token")
        async with self._lock:
            if self._tokens is None:
                raise GitReadAuthError("project auth unavailable")
            new = {**self._tokens, key: token}
            if len(new) > 32:
                raise GitReadAuthError("too many project credentials")
            try:
                await self._store.async_save({"schema":self.SCHEMA,"tokens":new})
            except Exception:
                raise GitReadAuthError("project token store failed") from None
            self._tokens = new

    async def delete(self, repository):
        from .project_catalog import normalize_repo
        key = normalize_repo(repository).casefold()
        async with self._lock:
            if self._tokens is None:
                raise GitReadAuthError("project auth unavailable")
            new = {k:v for k,v in self._tokens.items() if k != key}
            try:
                await self._store.async_save({"schema":self.SCHEMA,"tokens":new})
            except Exception:
                raise GitReadAuthError("project token deletion failed") from None
            self._tokens = new


def source_ref(value: object) -> str:
    if type(value) is not str or len(value) > 100:
        raise PreflightError("invalid Git source reference")
    if not value:
        return ""
    if value.startswith(("/", ".", "-")) or value.endswith(("/", ".", ".")):
        raise PreflightError("invalid Git source reference")
    if "//" in value or ".." in value or "@{" in value or "\\" in value:
        raise PreflightError("invalid Git source reference")
    if any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-" for ch in value):
        raise PreflightError("invalid Git source reference")
    return value


def _local_inventory(config_root: Path, groups: list[dict], *, max_files: int, max_bytes: int) -> dict[str, str]:
    """Read limited regular files only in approved managed directories; no writes."""
    found: dict[str, str] = {}
    total = 0
    checked = set()
    root = config_root.resolve(strict=True)
    for group in groups:
        relative = target_path(group["target"])
        if relative in checked:
            raise PreflightError("duplicate local target")
        checked.add(relative)
        target = root.joinpath(*relative.split("/"))
        if not target.exists():
            continue
        if not target.is_dir() or target.is_symlink() or not target.resolve().is_relative_to(root):
            raise PreflightError("unsafe local target")
        def _walk_failed(_error):
            raise PreflightError("local inventory cannot be fully inspected")
        for directory, dirs, files in os.walk(
            target, topdown=True, followlinks=False, onerror=_walk_failed
        ):
            parent = Path(directory)
            for d in dirs[:]:
                info = (parent / d).lstat()
                if not S_ISDIR(info.st_mode) or S_ISLNK(info.st_mode):
                    raise PreflightError("unsafe local directory")
                if d == "__pycache__":
                    dirs.remove(d)  # Only compiled Python cache: never part of a deploy plan.
            for filename in files:
                item = parent / filename
                suffix = item.relative_to(target).as_posix()
                safe_path(suffix)
                st = item.lstat()
                if not S_ISREG(st.st_mode) or S_ISLNK(st.st_mode) or st.st_nlink != 1:
                    raise PreflightError("unsafe local file")
                if st.st_size > max_bytes or st.st_size < 0:
                    raise PreflightError("local inventory exceeds byte budget")
                total += st.st_size
                if total > max_bytes or len(found) >= max_files:
                    raise PreflightError("local inventory exceeds allowed limits")
                # O_NOFOLLOW also rejects a final-component symlink race.
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                try:
                    fd = os.open(item, flags)
                except OSError:
                    raise PreflightError("unsafe or unreadable local file") from None
                try:
                    opened = os.fstat(fd)
                    if (not S_ISREG(opened.st_mode) or opened.st_nlink != 1 or
                            opened.st_size != st.st_size or opened.st_ino != st.st_ino):
                        raise PreflightError("local inventory changed while reading")
                    with os.fdopen(fd, "rb", closefd=False) as handle:
                        content = handle.read(st.st_size + 1)
                    if len(content) != st.st_size:
                        raise PreflightError("local inventory changed while reading")
                finally:
                    os.close(fd)
                path = relative + "/" + suffix
                if path in found:
                    raise PreflightError("duplicate local file")
                found[path] = git_blob_sha(content)
    return found


async def _get(session, url: str, *, token: str | None = None) -> dict:
    """No redirects, no tokens, fixed HTTPS GitHub API, short bounded response."""
    if not url.startswith(API + "/"):
        raise PreflightError("invalid source endpoint")
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Deploy-Relay-V2-Read-Only-Preflight",
        }
        if token is not None:
            if not GitReadAuth._valid_token(token):
                raise PreflightError("GitHub read-auth invalid")
            headers["Authorization"] = "Bearer " + token
        async with asyncio.timeout(12):
            async with session.get(url, allow_redirects=False, headers=headers) as response:
                if response.status != 200:
                    if response.status in (401, 403, 404, 429):
                        raise PreflightError("GitHub source unavailable or inaccessible")
                    raise PreflightError("GitHub request unsuccessful")
                size = response.headers.get("Content-Length", "")
                if size.isdigit() and int(size) > MAX_RESPONSE:
                    raise PreflightError("GitHub response exceeds size limit")
                raw = await response.content.read(MAX_RESPONSE + 1)
                if len(raw) > MAX_RESPONSE:
                    raise PreflightError("GitHub response exceeds size limit")
        obj = json.loads(raw.decode("utf-8"))
    except PreflightError:
        raise
    except Exception:
        # Includes transport-specific aiohttp exceptions, but excludes task
        # cancellation (asyncio.CancelledError is a BaseException).
        raise PreflightError("GitHub response could not be verified") from None
    if type(obj) is not dict:
        raise PreflightError("invalid GitHub JSON")
    return obj


async def inspect_public_repository(session, config_root: Path, repository: str, ref: str = "", *, token: str | None = None) -> dict:
    """Actual pinned remote tree versus read-only HA inventory; no write capability.

    An unavailable source is reported as unavailable, never as up-to-date.
    """
    try:
        repository = normalize_repo(repository)
    except CatalogError:
        raise PreflightError("invalid registered repository") from None
    ref = source_ref(ref)
    owner, name = repository.split("/")
    base = f"{API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    meta = await _get(session, base, token=token)
    branch = meta.get("default_branch")
    if type(branch) is not str or not source_ref(branch):
        raise PreflightError("repository has no supported default branch")
    if meta.get("archived") is True or meta.get("disabled") is True:
        raise PreflightError("repository is not an active installation source")
    selected = ref or branch
    commit = await _get(session, base + "/commits/" + quote(selected, safe=""), token=token)
    sha = commit.get("sha")
    tree = commit.get("commit", {}).get("tree") if type(commit.get("commit")) is dict else None
    tree_sha = tree.get("sha") if type(tree) is dict else None
    from .source_preflight import SHA
    if type(sha) is not str or not SHA.fullmatch(sha):
        raise PreflightError("source commit was not pinned")
    if type(tree_sha) is not str or not SHA.fullmatch(tree_sha):
        raise PreflightError("source tree was not pinned")
    manifest_obj = await _get(session, base + "/contents/deploy-relay.json?ref=" + sha, token=token)
    if manifest_obj.get("encoding") != "base64" or type(manifest_obj.get("content")) is not str:
        raise PreflightError("manifest is not an encoded file")
    try:
        manifest_bytes = base64.b64decode(manifest_obj["content"], validate=False)
    except (ValueError, binascii.Error):
        raise PreflightError("manifest base64 invalid") from None
    if (type(manifest_obj.get("size")) is not int or
            manifest_obj["size"] != len(manifest_bytes) or
            manifest_obj.get("sha") != git_blob_sha(manifest_bytes)):
        raise PreflightError("manifest content integrity failed")
    manifest = parse_manifest(manifest_bytes, repository=repository)
    tree_obj = await _get(session, base + "/git/trees/" + tree_sha + "?recursive=1", token=token)
    if tree_obj.get("truncated") is not False or type(tree_obj.get("tree")) is not list:
        raise PreflightError("GitHub tree is incomplete")
    remote = inspect_tree(manifest, tree_obj["tree"])
    local = await asyncio.to_thread(
        _local_inventory, config_root, manifest["groups"],
        max_files=manifest["max_files"], max_bytes=manifest["max_bytes"],
    )
    report = compare_blobs(manifest, remote, local, source_commit=sha)
    report["source_ref"] = selected
    report["source_name"] = "GitHub V2 read-only access" if token else "GitHub public (no V1 credentials)"
    report["total_local_files"] = len(local)
    return report
