"""Explicit Git diagnostic export of anonymous V2 DEV measurement results.

The writer never touches V1 configuration, project files or the operation
journal. Each upload is administrator-triggered and targets one fixed path.
"""
from __future__ import annotations

import asyncio
import base64
import json
import re
import secrets
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import quote

REPOSITORY = "TheDaimos/deploy-relay-agent-v2-dev"
BRANCH = "main"
ROOT = ".deploy-relay/diagnostics/v2-dev"
AUTH_SCHEMA = "dra-v2-dev-git-auth.v1"
MEASUREMENT_SCHEMA = "dra-v2-dev-measurement.v1"
EXPORT_SCHEMA = "dra-v2-dev-git-measurement.v1"
SCOPE = "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY"
MAX_EXPORT_BYTES = 4096
TOKEN_RE = re.compile(r"[^\s\x00-\x1f\x7f]{10,256}\Z", re.ASCII)
HEX_RE = re.compile(r"[0-9a-f]{32}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
COUNTERS = {
    "base_process_cpu_ms": 3600000,
    "work_process_cpu_ms": 3600000,
    "after_process_cpu_ms": 3600000,
    "max_wakeup_delay_ms": 60000,
    "elapsed_ms": 3600000,
    "synthetic_hashes": 640,
}
SUMMARY_KEYS = frozenset({
    "operation_id", "schema", "scope", "base_seconds", "work_seconds",
    "after_seconds", *COUNTERS.keys(),
})


class GitMeasurementError(ValueError):
    """Public error without tokens, API body or raw exceptions."""


class SecretStore(Protocol):
    async def async_load(self) -> object: ...
    async def async_save(self, value: dict[str, object]) -> None: ...


def sanitized_measurement(value: object) -> dict[str, object]:
    """Strict allowlist: no source IDs, arbitrary client JSON or project data."""
    if type(value) is not dict or set(value) != SUMMARY_KEYS:
        raise GitMeasurementError("measurement snapshot unavailable")
    source = value
    if (source["schema"] != MEASUREMENT_SCHEMA or
        source["scope"] != SCOPE or
        type(source["operation_id"]) is not str or
        not HEX_RE.fullmatch(source["operation_id"]) or
        (source["base_seconds"], source["work_seconds"],
         source["after_seconds"]) != (10, 20, 10)):
        raise GitMeasurementError("invalid measurement snapshot")
    numeric: dict[str, int] = {}
    for key, maximum in COUNTERS.items():
        number = source[key]
        if type(number) is not int or not 0 <= number <= maximum:
            raise GitMeasurementError("invalid measurement counters")
        numeric[key] = number
    return {
        "scope": SCOPE,
        "base_seconds": 10,
        "work_seconds": 20,
        "after_seconds": 10,
        **numeric,
    }


def public_export_document(summary: object, *, version: str, now: datetime) -> dict:
    if type(version) is not str or not re.fullmatch(r"0\.1\.[0-9]{1,3}", version):
        raise GitMeasurementError("invalid testlab version")
    if now.tzinfo is None:
        raise GitMeasurementError("invalid export time")
    normalized = now.astimezone(timezone.utc)
    return {
        "schema": EXPORT_SCHEMA,
        "created_at": normalized.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "component": "deploy_relay_v2_dev",
        "version": version,
        "mode": "READ_ONLY_TEST",
        "measurement": sanitized_measurement(summary),
        "note": "Synthetic workload. CPU measured across the whole HA process, not DRA alone.",
    }


class MeasurementGitExport:
    """One optional, narrowly scoped writer. No polling or background uploads."""

    def __init__(self, store: SecretStore, session: object) -> None:
        self._store = store
        self._session = session
        self._lock = asyncio.Lock()
        self._token: str | None = None
        self._ready = False

    @property
    def available(self) -> bool:
        return self._ready

    @property
    def configured(self) -> bool:
        return self._ready and self._token is not None

    async def load(self) -> None:
        try:
            value = await self._store.async_load()
        except Exception:
            raise GitMeasurementError("Git export configuration unavailable") from None
        if value is None:
            self._ready = True
            return
        if not isinstance(value, dict) or set(value) != {"schema", "token"} or value["schema"] != AUTH_SCHEMA:
            raise GitMeasurementError("Git export configuration invalid")
        token = value["token"]
        if token is not None and (type(token) is not str or not TOKEN_RE.fullmatch(token)):
            raise GitMeasurementError("Git export configuration invalid")
        self._token = token
        self._ready = True

    async def configure(self, *, token: str = "", clear: bool = False) -> None:
        async with self._lock:
            if not self._ready or type(clear) is not bool:
                raise GitMeasurementError("Git export unavailable")
            if not clear and (type(token) is not str or not TOKEN_RE.fullmatch(token)):
                raise GitMeasurementError("Invalid Git token")
            updated: str | None = None if clear else token
            try:
                await self._store.async_save({"schema": AUTH_SCHEMA, "token": updated})
            except Exception:
                raise GitMeasurementError("Git export configuration not saved") from None
            self._token = updated

    async def export(self, summary: object, *, version: str) -> dict[str, str]:
        async with self._lock:
            if not self.configured:
                raise GitMeasurementError("Git export not configured")
            now = datetime.now(timezone.utc)
            document = public_export_document(summary, version=version, now=now)
            stamp = now.strftime("%Y%m%dT%H%M%SZ")
            day = now.strftime("%Y-%m-%d")
            path = f"{ROOT}/{day}/{stamp}-{secrets.token_hex(4)}.json"
            body = {
                "schema": EXPORT_SCHEMA,
                "repository": REPOSITORY,
                "branch": BRANCH,
                "path": path,
                "snapshot": document,
            }
            raw = (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            if len(raw) > MAX_EXPORT_BYTES:
                raise GitMeasurementError("Git export exceeds limit")
            encoded = base64.b64encode(raw).decode("ascii")
            url_path = "/".join(quote(segment, safe="") for segment in path.split("/"))
            owner, repo = REPOSITORY.split("/")
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{url_path}"
            try:
                async with self._session.put(
                    url,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "Authorization": f"Bearer {self._token}",
                        "User-Agent": "DRA-V2-DEV-Measurement-Export",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                    json={
                        "message": "chore(diagnostics): export sanitized V2 DEV measurement [skip ci]",
                        "content": encoded,
                        "branch": BRANCH,
                    },
                    timeout=10,
                ) as response:
                    if response.status != 201:
                        raise GitMeasurementError("Git export rejected")
                    result = await response.json()
            except GitMeasurementError:
                raise
            except Exception:
                raise GitMeasurementError("Git export unavailable") from None
            commit = result.get("commit") if isinstance(result, dict) else None
            sha = commit.get("sha") if isinstance(commit, dict) else None
            if not isinstance(sha, str) or not COMMIT_RE.fullmatch(sha):
                raise GitMeasurementError("Git export confirmation invalid")
            return {
                "repository": REPOSITORY,
                "branch": BRANCH,
                "path": path,
                "commit_sha": sha,
                "file_url": f"https://github.com/{REPOSITORY}/blob/{BRANCH}/{path}",
            }
