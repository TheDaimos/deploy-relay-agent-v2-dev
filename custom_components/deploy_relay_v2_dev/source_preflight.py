"""DRA V2: strict read-only GitHub manifest/tree planning.

This module NEVER installs, writes backups, deletes or changes HA files.
All names in reports are allowlisted and only admin-visible. Actual deployment
requires a separate reviewed transaction engine and user authorization.
"""
from __future__ import annotations

import hashlib
import json
import re

from .project_catalog import normalize_repo, CatalogError

SHA = re.compile(r"[0-9a-f]{40}\Z")
SAFE_SEGMENT = re.compile(r"[A-Za-z0-9_.@+-]{1,120}\Z")
MAX_TREE = 3000
MAX_GROUPS = 12
MAX_FILES = 1000
MAX_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 65536
DENIED_COMPONENTS = frozenset({".storage", ".git", ".cloud", "__pycache__"})
DENIED_TARGETS = frozenset({"deploy_relay", "deploy_relay_v2_dev"})


class PreflightError(ValueError):
    """Invalid or untrusted GitHub source. Never include user or token details."""


def safe_path(path: object) -> str:
    """Reject traversal, encoded paths, Unicode confusables, and separators."""
    if type(path) is not str or not 1 <= len(path) <= 320 or "\\" in path:
        raise PreflightError("invalid source path")
    parts = path.split("/")
    if not parts or any(
        not SAFE_SEGMENT.fullmatch(p) or p in (".", "..") or p.lower() in DENIED_COMPONENTS
        for p in parts
    ):
        raise PreflightError("unsafe source path")
    return "/".join(parts)


def target_path(path: object) -> str:
    text = safe_path(path)
    parts = text.split("/")
    # Protected HA and V1/V2 integration paths are never eligible even for preview.
    if len(parts) != 2 or parts[0] != "custom_components":
        raise PreflightError("deployment target not approved for V2")
    if parts[1].casefold() in DENIED_TARGETS or parts[1].startswith("."):
        raise PreflightError("protected deployment target")
    return text


def _required_dict(data: object) -> dict:
    if type(data) is not dict:
        raise PreflightError("invalid manifest object")
    return data


def _positive_int(value: object, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise PreflightError("invalid resource limit")
    return value


def parse_manifest(raw: bytes, *, repository: str) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_MANIFEST_BYTES:
        raise PreflightError("invalid manifest size")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise PreflightError("invalid manifest encoding") from None
    data = _required_dict(value)
    if data.get("schema") != "deploy-relay.deployment.v1":
        raise PreflightError("unsupported manifest schema")
    project = _required_dict(data.get("project"))
    identity = project.get("id")
    if type(identity) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", identity):
        raise PreflightError("invalid project identity")
    source = _required_dict(data.get("source"))
    try:
        claimed_repo = normalize_repo(source.get("repository"))
        requested_repo = normalize_repo(repository)
    except CatalogError:
        raise PreflightError("invalid source repository") from None
    if claimed_repo.casefold() != requested_repo.casefold():
        raise PreflightError("repository identity mismatch")
    if source.get("mode") != "repository_contents":
        raise PreflightError("artifact source is not yet supported")
    deployment = _required_dict(data.get("deployment"))
    if deployment.get("root") != "/config":
        raise PreflightError("deployment root not approved")
    policy = _required_dict(data.get("policy"))
    if policy.get("allow_symlinks") is not False:
        raise PreflightError("symlinks not permitted")
    max_files = _positive_int(policy.get("max_files"), MAX_FILES)
    max_bytes = _positive_int(policy.get("max_uncompressed_bytes"), MAX_BYTES)
    values = deployment.get("groups")
    if type(values) is not list or not 1 <= len(values) <= MAX_GROUPS:
        raise PreflightError("invalid deployment groups")
    groups: list[dict] = []
    used = set()
    for raw_group in values:
        g = _required_dict(raw_group)
        if g.get("mode") != "replace_directory":
            raise PreflightError("deployment mode not approved")
        source_dir = safe_path(g.get("source"))
        target_dir = target_path(g.get("target"))
        if target_dir in used:
            raise PreflightError("overlapping deployment targets")
        used.add(target_dir)
        groups.append({"source": source_dir, "target": target_dir})
    return {
        "schema": "dra-v2-dev-preflight-manifest.v1",
        "project_id": identity,
        "repository": requested_repo,
        "max_files": max_files, "max_bytes": max_bytes,
        "groups": groups,
    }


def inspect_tree(manifest: dict, entries: object) -> list[dict]:
    """Validate complete remote tree; reject symlinks, submodules and truncation."""
    if type(entries) is not list or len(entries) > MAX_TREE:
        raise PreflightError("repository tree incomplete or too large")
    found: dict[str, dict] = {}
    total = 0
    for item in entries:
        if type(item) is not dict:
            raise PreflightError("invalid repository tree entry")
        path = safe_path(item.get("path"))
        typ = item.get("type")
        mode = item.get("mode")
        if path in found:
            raise PreflightError("duplicate repository path")
        # For relevant entries only: this also prevents traversing a malformed
        # source tree before the manifest files are selected.
        found[path] = item
        if typ not in ("blob", "tree") or mode not in ("100644", "100755", "040000", "40000"):
            raise PreflightError("unsupported source entry (possibly symlink/submodule)")
        if (typ == "blob") != (mode in ("100644", "100755")):
            raise PreflightError("inconsistent source entry type")
        if typ == "blob":
            size = item.get("size")
            if type(size) is not int or not 0 <= size <= MAX_BYTES:
                raise PreflightError("invalid source size")
            sha = item.get("sha")
            if type(sha) is not str or not SHA.fullmatch(sha):
                raise PreflightError("invalid Git blob identity")
    selected = {}
    for group in manifest["groups"]:
        root = group["source"] + "/"
        files = [(path, row) for path, row in found.items()
                 if path.startswith(root) and row["type"] == "blob"]
        if not files:
            raise PreflightError("source directory empty")
        for path, row in files:
            suffix = path[len(root):]
            safe_path(suffix)
            destination = group["target"] + "/" + suffix
            if destination in selected:
                raise PreflightError("duplicate deployment file")
            selected[destination] = {
                "path": destination, "sha": row["sha"], "size": row["size"],
            }
            total += row["size"]
            if len(selected) > manifest["max_files"] or total > manifest["max_bytes"]:
                raise PreflightError("source exceeds manifest budget")
    return [selected[k] for k in sorted(selected)]


def compare_blobs(
    manifest: dict, remote_files: list[dict], local_blobs: dict[str, str],
    *, source_commit: str,
) -> dict:
    """Pure immutable-plan output from SHA-pinned remote and safe local blobs."""
    if type(source_commit) is not str or not SHA.fullmatch(source_commit):
        raise PreflightError("not a pinned commit")
    remote = {f["path"]: f["sha"] for f in remote_files}
    if len(remote) != len(remote_files):
        raise PreflightError("duplicate remote file")
    targets = tuple(group["target"] for group in manifest["groups"])
    for path, sha in local_blobs.items():
        if type(path) is not str or not any(path.startswith(t + "/") for t in targets):
            raise PreflightError("unmanaged local target in preview")
        if type(sha) is not str or not SHA.fullmatch(sha):
            raise PreflightError("invalid local blob identity")
    added = sorted(set(remote) - set(local_blobs))
    deleted = sorted(set(local_blobs) - set(remote))
    changed = sorted(p for p in set(remote) & set(local_blobs) if remote[p] != local_blobs[p])
    unchanged = len(set(remote) & set(local_blobs)) - len(changed)
    return {
        "schema": "dra-v2-dev-source-preview.v1",
        "repository": manifest["repository"], "source_commit": source_commit,
        "project_id": manifest["project_id"],
        "groups": [dict(g) for g in manifest["groups"]],
        "add": added, "change": changed, "remove": deleted,
        "unchanged_count": unchanged, "remote_file_count": len(remote),
        "total_remote_bytes": sum(f["size"] for f in remote_files),
        "sources_verified": True,
        "local_inventory_readonly": True,
        "installation_enabled": False,
        "handover_required": True,
        "backup_verified": False,
    }


def git_blob_sha(content: bytes) -> str:
    if type(content) is not bytes:
        raise PreflightError("invalid local file bytes")
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()
