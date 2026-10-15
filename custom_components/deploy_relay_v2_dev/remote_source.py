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
import re
from pathlib import Path, PurePosixPath
from stat import S_ISDIR, S_ISLNK, S_ISREG
from urllib.parse import quote

from .project_catalog import normalize_repo, CatalogError
from .v1_engine.version_markers import extract_version_markers, MAX_VERSION_MARKER_SCAN_BYTES
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

    async def rename(self, old_repository, new_repository):
        from .project_catalog import normalize_repo
        old = normalize_repo(old_repository).casefold()
        new = normalize_repo(new_repository).casefold()
        if old == new:
            return
        async with self._lock:
            if self._tokens is None or new in self._tokens:
                raise GitReadAuthError("project auth rename unavailable")
            copy = dict(self._tokens)
            secret = copy.pop(old, None)
            if secret is not None:
                copy[new] = secret
            try:
                await self._store.async_save({"schema":self.SCHEMA,"tokens":copy})
            except Exception:
                raise GitReadAuthError("project auth rename failed") from None
            self._tokens = copy

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


async def _get(session, url: str, *, token: str | None = None, allow_list: bool = False):
    """Bounded read-only GitHub GET, one retry for transient transport errors.

    Never retry explicit GitHub denials, source-policy errors, excessive bodies
    or malformed JSON. No redirects, hosts, writes, or returned raw errors.
    """
    if not url.startswith(API + "/"):
        raise PreflightError("invalid source endpoint")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Deploy-Relay-V2-Read-Only-Preflight",
    }
    if token is not None:
        if not GitReadAuth._valid_token(token):
            raise PreflightError("GitHub read-auth invalid")
        headers["Authorization"] = "Bearer " + token
    for attempt in range(2):
        try:
            async with asyncio.timeout(12):
                async with session.get(url, allow_redirects=False, headers=headers) as response:
                    if response.status != 200:
                        # Fixed, sanitized categories only; never expose response
                        # headers, URLs, repository names or GitHub body content.
                        if response.status == 401:
                            raise PreflightError("github_http_authentication")
                        if response.status == 403:
                            raise PreflightError("github_http_forbidden")
                        if response.status == 404:
                            raise PreflightError("github_http_not_found")
                        if response.status == 429:
                            raise PreflightError("github_http_rate_limited")
                        raise PreflightError("GitHub request unsuccessful")
                    size = response.headers.get("Content-Length", "")
                    if size.isdigit() and int(size) > MAX_RESPONSE:
                        raise PreflightError("GitHub response exceeds size limit")
                    # aiohttp StreamReader.read(n) may return *fewer* than n
                    # bytes before EOF. A single read produced partial Git
                    # tree JSON and a false "invalid GitHub JSON" diagnosis.
                    # Keep collecting until EOF, with a hard 4-MiB budget.
                    chunks = bytearray()
                    while True:
                        remaining = MAX_RESPONSE + 1 - len(chunks)
                        part = await response.content.read(min(64 * 1024, remaining))
                        if not part:
                            break
                        chunks.extend(part)
                        if len(chunks) > MAX_RESPONSE:
                            raise PreflightError("GitHub response exceeds size limit")
                    raw = bytes(chunks)
        except PreflightError:
            raise  # Denials, oversize, and trust-boundary failures never retry.
        except Exception:
            # Only bounded, idempotent HTTPS GET; no raw exception or secrets.
            # CancelledError is a BaseException and must not be swallowed.
            if attempt == 0:
                await asyncio.sleep(0.15)
                continue
            raise PreflightError("GitHub response could not be verified") from None
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError):
            # A received but malformed body is not a transient network failure.
            raise PreflightError("invalid GitHub JSON") from None
        if type(obj) is not dict and not (allow_list and type(obj) is list):
            raise PreflightError("invalid GitHub JSON")
        return obj
    raise PreflightError("GitHub response could not be verified")



async def inspect_source_choices(session, repository: str, *, token: str | None = None,
                                 expected_project_id: str | None = None) -> dict:
    """Bounded, read-only GitHub branches/tags for the UI; never install authorization."""
    try:
        repository = normalize_repo(repository)
    except CatalogError:
        raise PreflightError("invalid source selection") from None
    owner, name = repository.split("/")
    base = f"{API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    meta = await _get(session, base, token=token)
    if meta.get("full_name", "").casefold() != repository.casefold():
        raise PreflightError("repository mismatch")
    default = source_ref(meta.get("default_branch", ""))
    if not default:
        raise PreflightError("missing default branch")
    choices = []
    for kind, endpoint in (("branch", "branches"), ("tag", "tags")):
        rows = await _get(session, base + "/" + endpoint + "?per_page=100", token=token, allow_list=True)
        if len(rows) > 100:
            raise PreflightError("source list too large")
        for row in rows:
            if type(row) is not dict or type(row.get("commit")) is not dict:
                raise PreflightError("invalid source entry")
            ref = source_ref(row.get("name"))
            sha = row["commit"].get("sha")
            if not ref or type(sha) is not str or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
                raise PreflightError("invalid source entry")
            choices.append({"kind": kind, "ref": ref, "commit": sha})
    # Same project-owned recommendation file as DRA V1; never borrow V1 state.
    recommended = {"kind": "branch", "ref": default, "channel": "default",
                   "explicit": False, "commit": None}
    try:
        policy_obj = await _get(session, base + "/contents/deploy-relay-channel.json?ref=" +
                                quote(default, safe=""), token=token)
    except PreflightError as exc:
        if str(exc) != "github_http_not_found":
            raise
    else:
        if (policy_obj.get("encoding") != "base64" or
                type(policy_obj.get("content")) is not str or
                type(policy_obj.get("size")) is not int or
                policy_obj["size"] > 8192):
            raise PreflightError("invalid deployment recommendation")
        try:
            raw = base64.b64decode(policy_obj["content"], validate=False)
            if len(raw) != policy_obj["size"] or git_blob_sha(raw) != policy_obj.get("sha"):
                raise PreflightError("invalid recommendation blob")
            policy = json.loads(raw.decode("utf-8"))
        except (UnicodeError, binascii.Error, ValueError):
            raise PreflightError("invalid recommendation format") from None
        if (type(policy) is not dict or
                set(policy) != {"schema", "project_id", "recommended"} or
                policy.get("schema") != "deploy-relay.channel.v1" or
                (expected_project_id is not None and policy.get("project_id") != expected_project_id) or
                type(policy.get("recommended")) is not dict or
                set(policy["recommended"]) != {"channel", "kind", "ref"} or
                policy["recommended"].get("kind") not in ("branch", "tag") or
                type(policy["recommended"].get("channel")) is not str or
                not policy["recommended"]["channel"].strip()):
            raise PreflightError("invalid deployment recommendation")
        preferred_ref = source_ref(policy["recommended"].get("ref"))
        if not preferred_ref:
            raise PreflightError("invalid recommended reference")
        recommended = {"kind": policy["recommended"]["kind"], "ref": preferred_ref,
                       "channel": policy["recommended"]["channel"],
                       "explicit": True, "commit": None}
    for item in choices:
        if item["kind"] == recommended["kind"] and item["ref"] == recommended["ref"]:
            recommended["commit"] = item["commit"]
            break
    if recommended["commit"] is None:
        resolved = await inspect_source_head(session, repository, recommended["ref"], token=token)
        recommended["commit"] = resolved["commit"]
    return {"schema": "dra-v2-source-choices.v1", "repository": repository,
            "default_ref": default, "choices": choices, "recommended": recommended,
            "limited": sum(c["kind"] == "branch" for c in choices) == 100 or
                       sum(c["kind"] == "tag" for c in choices) == 100}


async def inspect_source_head(session, repository: str, ref: str = "", *, token: str | None = None) -> dict:
    """Read only the current GitHub commit. No manifest, file inventory or installation."""
    try:
        repository = normalize_repo(repository)
        ref = source_ref(ref)
    except (CatalogError, PreflightError):
        raise PreflightError("invalid source selection") from None
    owner, name = repository.split("/")
    base = f"{API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    if not ref:
        meta = await _get(session, base, token=token)
        if meta.get("full_name", "").casefold() != repository.casefold():
            raise PreflightError("repository mismatch")
        ref = source_ref(meta.get("default_branch", ""))
        if not ref:
            raise PreflightError("missing default branch")
    head = await _get(session, base + "/commits/" + quote(ref, safe=""), token=token)
    sha = head.get("sha")
    if type(sha) is not str or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise PreflightError("invalid source commit")
    return {"schema": "dra-v2-source-head.v1", "repository": repository, "ref": ref, "commit": sha}


async def inspect_repository_connection(session, repository: str, *, token: str | None = None) -> dict:
    """Check GitHub repository visibility using GET only, independent of a DRA manifest.

    This deliberately does not grant, exercise or certify write rights. GitHub's
    advertised push permission is metadata, not a successful write transaction.
    """
    try:
        repository = normalize_repo(repository)
    except CatalogError:
        raise PreflightError("invalid registered repository") from None
    owner, name = repository.split("/")
    endpoint = f"{API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    meta = await _get(session, endpoint, token=token)
    if type(meta.get("full_name")) is not str or meta["full_name"].casefold() != repository.casefold():
        raise PreflightError("GitHub repository identity does not match")
    if type(meta.get("private")) is not bool:
        raise PreflightError("GitHub repository visibility not verified")
    # Metadata alone is insufficient: actually read a Git tree using this credential.
    default_branch = meta.get("default_branch")
    if type(default_branch) is not str or not default_branch or len(default_branch) > 180:
        raise PreflightError("default branch not available")
    tree_endpoint = f"{API}/repos/{quote(owner, safe='')}/{quote(name, safe='')}/git/trees/{quote(default_branch, safe='')}"
    tree = await _get(session, tree_endpoint, token=token)
    if type(tree.get("sha")) is not str or not re.fullmatch(r"[a-f0-9]{40}", tree["sha"]) or type(tree.get("tree")) is not list:
        raise PreflightError("repository content read not verified")
    permissions = meta.get("permissions")
    advertised_push = permissions.get("push") if type(permissions) is dict else None
    if type(advertised_push) is not bool:
        advertised_push = None
    return {
        "connected": True, "read_verified": True, "repository": repository,
        "private": meta["private"], "authenticated": token is not None,
        "advertised_push": advertised_push, "write_tested": False,
        "access_level": "RW" if advertised_push is True else "RO",
    }


def _version_order(source: str, local: str) -> str:
    """Preserve V1's conservative numeric marker comparison."""
    if source == local:
        return "same"
    a = tuple(int(x) for x in re.findall(r"\d+", source)[:8])
    b = tuple(int(x) for x in re.findall(r"\d+", local)[:8])
    if not a or not b:
        return "unknown"
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return "downgrade" if a < b else "upgrade" if a > b else "unknown"


def _read_local_version_file(config_root: Path, relative: str, expected: str) -> bytes | None:
    """Bounded regular-file read outside HA event loop, matched to prior inventory."""
    root = config_root.resolve(strict=True)
    file = root.joinpath(*relative.split("/"))
    if not file.resolve(strict=True).is_relative_to(root):
        return None
    st = file.lstat()
    if not S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size > MAX_VERSION_MARKER_SCAN_BYTES:
        return None
    fd = os.open(file, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        with os.fdopen(fd, "rb", closefd=False) as handle:
            payload = handle.read(MAX_VERSION_MARKER_SCAN_BYTES + 1)
    finally:
        os.close(fd)
    return payload if git_blob_sha(payload) == expected else None


async def _preview_version_guard(session, config_root: Path, base: str, commit: str,
                                 manifest: dict, remote: list[dict], local: dict[str, str],
                                 report: dict, token: str | None) -> dict:
    """Read only a bounded set of manifest-managed version files at the pinned SHA."""
    result = {"status": "unknown", "source_version": None, "local_version": None,
              "marker": None, "reason": "no_common_version_marker",
              "regression": False, "warning": bool(report["remove"])}
    if report["remove"]:
        result["reason"] = "no_common_version_marker_with_removals"
    candidates = []
    for group in manifest["groups"]:
        prefix = group["target"] + "/"
        for item in remote:
            path = item["path"]
            if not path.startswith(prefix) or item["size"] > MAX_VERSION_MARKER_SCAN_BYTES:
                continue
            rel = path[len(prefix):]
            # Common V1-compatible build markers, not arbitrary code or secrets.
            if PurePosixPath(rel).name.casefold() in (
                    "build_info.py", "manifest.json", "version.py", "const.py", "__init__.py"):
                candidates.append((group, item, rel))
    # The strongest BUILD_VERSION marker usually lives in build_info.py.
    priority = {"build_info.py": 0, "version.py": 1, "const.py": 2,
                "__init__.py": 3, "manifest.json": 4}
    candidates.sort(key=lambda row: (priority.get(PurePosixPath(row[2]).name.casefold(), 5),
                                     row[2]))
    matches = []
    for group, item, relative in candidates[:12]:
        target_relative = item["path"]
        expected_local = local.get(target_relative)
        if expected_local is None:
            continue
        source_path = group["source"] + "/" + relative
        try:
            entry = await _get(session, base + "/contents/" +
                               quote(source_path, safe="/") + "?ref=" + commit, token=token)
            if entry.get("encoding") != "base64" or type(entry.get("content")) is not str:
                continue
            remote_bytes = base64.b64decode(entry["content"], validate=False)
            if (len(remote_bytes) != item["size"] or
                    git_blob_sha(remote_bytes) != item["sha"]):
                raise PreflightError("version source blob integrity failed")
            local_bytes = await asyncio.to_thread(
                _read_local_version_file, config_root, target_relative, expected_local)
            if local_bytes is None:
                continue
        except (OSError, ValueError, binascii.Error):
            continue
        source_markers = extract_version_markers(group["target"], relative, remote_bytes)
        local_markers = extract_version_markers(group["target"], relative, local_bytes)
        for a in source_markers:
            for b in local_markers:
                if a.name == b.name and a.relative_path == b.relative_path:
                    matches.append((a.rank, a, b, target_relative))
    if matches:
        matches.sort(key=lambda row: (-row[0], row[1].name, row[1].relative_path))
        _, source_marker, local_marker, target = matches[0]
        relation = _version_order(source_marker.value, local_marker.value)
        destructive = bool(report["change"] or report["remove"])
        return {
            "status": relation, "source_version": source_marker.value,
            "local_version": local_marker.value, "marker": source_marker.name,
            "source_path": source_marker.relative_path, "target_path": target,
            "regression": relation == "downgrade",
            "warning": relation == "downgrade" or (relation == "same" and destructive),
            "reason": ("source_older_than_local" if relation == "downgrade" else
                       "source_newer_than_local" if relation == "upgrade" else
                       "same_version_with_file_changes" if destructive and relation == "same" else
                       "same_version" if relation == "same" else "version_order_unknown"),
        }
    return result


async def inspect_public_repository(session, config_root: Path, repository: str, ref: str = "", *, token: str | None = None, stage_hook=None) -> dict:
    """Actual pinned remote tree versus read-only HA inventory; no write capability.

    An unavailable source is reported as unavailable, never as up-to-date.
    """
    if stage_hook is not None:
        stage_hook("repository")
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
    if stage_hook is not None:
        stage_hook("commit")
    commit = await _get(session, base + "/commits/" + quote(selected, safe=""), token=token)
    sha = commit.get("sha")
    tree = commit.get("commit", {}).get("tree") if type(commit.get("commit")) is dict else None
    tree_sha = tree.get("sha") if type(tree) is dict else None
    from .source_preflight import SHA
    if type(sha) is not str or not SHA.fullmatch(sha):
        raise PreflightError("source commit was not pinned")
    if type(tree_sha) is not str or not SHA.fullmatch(tree_sha):
        raise PreflightError("source tree was not pinned")
    if stage_hook is not None:
        stage_hook("manifest")
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
    if stage_hook is not None:
        stage_hook("tree")
    tree_obj = await _get(session, base + "/git/trees/" + tree_sha + "?recursive=1", token=token)
    if tree_obj.get("truncated") is not False or type(tree_obj.get("tree")) is not list:
        raise PreflightError("GitHub tree is incomplete")
    remote = inspect_tree(manifest, tree_obj["tree"])
    if stage_hook is not None:
        stage_hook("local_inventory")
    local = await asyncio.to_thread(
        _local_inventory, config_root, manifest["groups"],
        max_files=manifest["max_files"], max_bytes=manifest["max_bytes"],
    )
    if stage_hook is not None:
        stage_hook("comparison")
    report = compare_blobs(manifest, remote, local, source_commit=sha)
    report["source_ref"] = selected
    report["source_name"] = "GitHub V2 read-only access" if token else "GitHub public (no V1 credentials)"
    report["total_local_files"] = len(local)
    report["version_guard"] = await _preview_version_guard(
        session, config_root, base, sha, manifest, remote, local, report, token)
    return report
