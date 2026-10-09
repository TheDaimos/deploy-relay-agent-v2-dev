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
        for directory, dirs, files in os.walk(target, topdown=True, followlinks=False):
            parent = Path(directory)
            for d in dirs:
                info = (parent / d).lstat()
                if not S_ISDIR(info.st_mode) or S_ISLNK(info.st_mode):
                    raise PreflightError("unsafe local directory")
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
                fd = os.open(item, flags)
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


async def _get(session, url: str) -> dict:
    """No redirects, no tokens, fixed HTTPS GitHub API, short bounded response."""
    if not url.startswith(API + "/"):
        raise PreflightError("invalid source endpoint")
    try:
        async with asyncio.timeout(12):
            async with session.get(url, allow_redirects=False, headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Deploy-Relay-V2-Read-Only-Preflight",
            }) as response:
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
    except (TimeoutError, OSError, ValueError, UnicodeError, TypeError, AttributeError):
        raise PreflightError("GitHub response could not be verified") from None
    if type(obj) is not dict:
        raise PreflightError("invalid GitHub JSON")
    return obj


async def inspect_public_repository(session, config_root: Path, repository: str, ref: str = "") -> dict:
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
    meta = await _get(session, base)
    branch = meta.get("default_branch")
    if type(branch) is not str or not source_ref(branch):
        raise PreflightError("repository has no supported default branch")
    if meta.get("archived") is True or meta.get("disabled") is True:
        raise PreflightError("repository is not an active installation source")
    selected = ref or branch
    commit = await _get(session, base + "/commits/" + quote(selected, safe=""))
    sha = commit.get("sha")
    tree = commit.get("commit", {}).get("tree") if type(commit.get("commit")) is dict else None
    tree_sha = tree.get("sha") if type(tree) is dict else None
    from .source_preflight import SHA
    if type(sha) is not str or not SHA.fullmatch(sha):
        raise PreflightError("source commit was not pinned")
    if type(tree_sha) is not str or not SHA.fullmatch(tree_sha):
        raise PreflightError("source tree was not pinned")
    manifest_obj = await _get(session, base + "/contents/deploy-relay.json?ref=" + sha)
    if manifest_obj.get("encoding") != "base64" or type(manifest_obj.get("content")) is not str:
        raise PreflightError("manifest is not an encoded file")
    try:
        manifest_bytes = base64.b64decode(manifest_obj["content"], validate=False)
    except (ValueError, binascii.Error):
        raise PreflightError("manifest base64 invalid") from None
    manifest = parse_manifest(manifest_bytes, repository=repository)
    tree_obj = await _get(session, base + "/git/trees/" + tree_sha + "?recursive=1")
    if tree_obj.get("truncated") is not False or type(tree_obj.get("tree")) is not list:
        raise PreflightError("GitHub tree is incomplete")
    remote = inspect_tree(manifest, tree_obj["tree"])
    local = await asyncio.to_thread(
        _local_inventory, config_root, manifest["groups"],
        max_files=manifest["max_files"], max_bytes=manifest["max_bytes"],
    )
    report = compare_blobs(manifest, remote, local, source_commit=sha)
    report["source_ref"] = selected
    report["source_name"] = "GitHub public (no V1 credentials)"
    report["total_local_files"] = len(local)
    return report
