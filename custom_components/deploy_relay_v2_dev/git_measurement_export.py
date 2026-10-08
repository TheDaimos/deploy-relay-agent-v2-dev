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
MEASUREMENT_SCHEMA = "dra-v2-dev-measurement.v2"
EXPORT_SCHEMA = "dra-v2-dev-git-measurement.v2"
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
    "after_seconds", "memory", *COUNTERS.keys(),
})


class GitMeasurementError(ValueError):
    """Public error without tokens, API body or raw exceptions."""


class SecretStore(Protocol):
    async def async_load(self) -> object: ...
    async def async_save(self, value: dict[str, object]) -> None: ...




MEMORY_SCHEMA = "dra-v2-dev-memory.v1"
MEMORY_SOURCE = "LINUX_PROCFS_VISIBLE_TO_HA"
MEMORY_REASON = "SHARED_HA_PROCESS_CANNOT_ATTRIBUTE"
MEMORY_POINTS = ("start", "base_end", "work_end", "end")
MEMORY_FIELDS = frozenset({
    "total_kib", "used_effective_kib", "free_kib", "available_kib",
    "ha_process_rss_kib",
})
MAX_MEMORY_KIB = 1 << 44


def sanitized_memory(value: object) -> dict[str, object]:
    """Validate and copy fixed numeric snapshots, never arbitrary memory data."""
    if type(value) is not dict or set(value) != {
        "schema", "source", "snapshots", "component_memory"
    }:
        raise GitMeasurementError("invalid memory snapshot")
    if value["schema"] != MEMORY_SCHEMA or value["source"] != MEMORY_SOURCE:
        raise GitMeasurementError("invalid memory scope")
    attribution = value["component_memory"]
    if (type(attribution) is not dict or set(attribution) != {
        "dra_v1_kib", "dra_v2_kib", "reason"
    } or attribution["dra_v1_kib"] is not None or
        attribution["dra_v2_kib"] is not None or
        attribution["reason"] != MEMORY_REASON):
        raise GitMeasurementError("invalid component attribution")
    snaps = value["snapshots"]
    if type(snaps) is not dict or set(snaps) != set(MEMORY_POINTS):
        raise GitMeasurementError("invalid memory samples")
    checked = {}
    for name in MEMORY_POINTS:
        sample = snaps[name]
        if type(sample) is not dict or set(sample) != MEMORY_FIELDS:
            raise GitMeasurementError("invalid memory sample")
        clean = {}
        for key in MEMORY_FIELDS:
            number = sample[key]
            if number is not None and (
                type(number) is not int or number < 0 or number > MAX_MEMORY_KIB
            ):
                raise GitMeasurementError("invalid memory quantity")
            clean[key] = number
        t, u, free, available = (
            clean["total_kib"], clean["used_effective_kib"],
            clean["free_kib"], clean["available_kib"],
        )
        if not (
            (t is None and u is None and free is None and available is None)
            or (type(t) is int and t > 0 and type(u) is int and
                type(free) is int and type(available) is int and
                free <= t and available <= t and u == t - available)
        ):
            raise GitMeasurementError("inconsistent memory quantities")
        checked[name] = clean
    return {
        "schema": MEMORY_SCHEMA,
        "source": MEMORY_SOURCE,
        "snapshots": checked,
        "component_memory": {
            "dra_v1_kib": None, "dra_v2_kib": None,
            "reason": MEMORY_REASON,
        },
    }

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
        "memory": sanitized_memory(source["memory"]),
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



SUITE_SCHEMA = "dra-v2-dev-suite.v1"
MULTICORE_SCHEMA = "dra-v2-dev-multicore.v1"
SUITE_EXPORT_SCHEMA = "dra-v2-dev-git-suite.v1"
_WORKER_COUNTS = (1, 2, 4)


def sanitized_multicore(data: object) -> dict[str, object]:
    if type(data) is not dict or set(data) != {
        "schema", "method", "logical_cpus_visible",
        "affinity_cpus_visible", "levels",
    }:
        raise GitMeasurementError("invalid multicore report")
    if data["schema"] != MULTICORE_SCHEMA or data["method"] != "BOUNDED_CHILD_PROCESSES":
        raise GitMeasurementError("invalid multicore method")
    cpu = {}
    for key in ("logical_cpus_visible", "affinity_cpus_visible"):
        value = data[key]
        if value is not None and (type(value) is not int or not 1 <= value <= 1024):
            raise GitMeasurementError("invalid multicore core count")
        cpu[key] = value
    stages = data["levels"]
    if type(stages) is not list or len(stages) != 3:
        raise GitMeasurementError("invalid multicore levels")
    checked = []
    for workers, row in zip(_WORKER_COUNTS, stages):
        if type(row) is not dict or set(row) != {
            "workers", "status", "wall_ms",
            "aggregate_worker_cpu_ms", "iterations_total",
        } or type(row["workers"]) is not int or row["workers"] != workers:
            raise GitMeasurementError("invalid worker count")
        if row["status"] not in ("ok", "unavailable") or type(row["status"]) is not str:
            raise GitMeasurementError("invalid worker status")
        wall, cpu_ms, iterations = (
            row["wall_ms"], row["aggregate_worker_cpu_ms"], row["iterations_total"],
        )
        if row["status"] == "ok":
            if (type(wall) is not int or not 0 <= wall <= 30000
                or type(cpu_ms) is not int or not 0 <= cpu_ms <= 30000
                or type(iterations) is not int or iterations != workers * 400000):
                raise GitMeasurementError("invalid worker measurements")
        elif any(x is not None for x in (wall, cpu_ms, iterations)):
            raise GitMeasurementError("invalid unavailable measurements")
        checked.append({
            "workers": workers, "status": row["status"],
            "wall_ms": wall, "aggregate_worker_cpu_ms": cpu_ms,
            "iterations_total": iterations,
        })
    return {
        "schema": MULTICORE_SCHEMA, "method": "BOUNDED_CHILD_PROCESSES",
        **cpu, "levels": checked,
    }


def sanitized_suite(data: object) -> dict[str, object]:
    if type(data) is not dict or set(data) != {
        "schema", "operation_id", "mode", "readonly_steps",
        "measurement", "multicore",
    } or data["schema"] != SUITE_SCHEMA:
        raise GitMeasurementError("invalid suite report")
    if type(data["operation_id"]) is not str or not HEX_RE.fullmatch(data["operation_id"]):
        raise GitMeasurementError("invalid suite identity")
    mode = data["mode"]
    if mode not in ("full", "multicore") or type(mode) is not str:
        raise GitMeasurementError("invalid suite mode")
    if type(data["readonly_steps"]) is not int or data["readonly_steps"] != (40 if mode == "full" else 0):
        raise GitMeasurementError("invalid suite trial")
    if mode == "full":
        if type(data["measurement"]) is not dict or data["measurement"].get("operation_id") != data["operation_id"]:
            raise GitMeasurementError("invalid suite measurement")
        measurement = sanitized_measurement(data["measurement"])
    else:
        if data["measurement"] is not None:
            raise GitMeasurementError("unexpected suite measurement")
        measurement = None
    return {
        "schema": SUITE_SCHEMA, "mode": mode,
        "readonly_steps": data["readonly_steps"],
        "measurement": measurement,
        "multicore": sanitized_multicore(data["multicore"]),
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
            if type(summary) is dict and summary.get("schema") == SUITE_SCHEMA:
                if type(version) is not str or not re.fullmatch(r"0\\.1\\.[0-9]{1,3}", version):
                    raise GitMeasurementError("invalid suite version")
                document = {
                    "schema": SUITE_EXPORT_SCHEMA,
                    "created_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "component": "deploy_relay_v2_dev",
                    "version": version,
                    "mode": "READ_ONLY_TEST",
                    "suite": sanitized_suite(summary),
                    "note": "Synthetic subprocess comparison, not individual DRA CPU attribution.",
                }
                output_schema = SUITE_EXPORT_SCHEMA
            else:
                document = public_export_document(summary, version=version, now=now)
                output_schema = EXPORT_SCHEMA
            stamp = now.strftime("%Y%m%dT%H%M%SZ")
            day = now.strftime("%Y-%m-%d")
            path = f"{ROOT}/{day}/{stamp}-{secrets.token_hex(4)}.json"
            body = {
                "schema": output_schema,
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
                async with asyncio.timeout(10):
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
