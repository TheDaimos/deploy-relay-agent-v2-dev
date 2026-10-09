"""Server-only private central archive export of sanitized V2 DEV measurements.

The writer never touches V1 configuration, project files or the operation
journal. Each upload is administrator-triggered and targets one fixed path.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import quote

REPOSITORY = "TheDaimos/Project-Log-And-Export"
SOURCE_REPOSITORY = "TheDaimos/deploy-relay-agent-v2-dev"
APPLICATION_ID = "deploy-relay-agent-v2"
APPLICATION_NAME = "Deploy Relay Agent V2"
STANDARD_SCHEMA = "daimos-project-log-export-v1"
QUEUE_SCHEMA = "dra-v2-dev-central-export-queue.v1"
SERVER_TOKEN_ENV = "DRA_V2_CENTRAL_EXPORT_TOKEN"
BRANCH = "main"
ROOT = "exports/deploy-relay-agent-v2"
AUTH_SCHEMA = "deprecated-public-writer-do-not-use"
MEASUREMENT_SCHEMA = "dra-v2-dev-measurement.v2"
EXPORT_SCHEMA = "dra-v2-dev-git-measurement.v2"
SCOPE = "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY"
MAX_EXPORT_BYTES = 8192
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



SUITE_SCHEMA = "dra-v2-dev-suite.v2"
MULTICORE_SCHEMA = "dra-v2-dev-multicore.v2"
SUITE_EXPORT_SCHEMA = "dra-v2-dev-git-suite.v2"
_WORKER_COUNTS = (1, 2, 4, 6, 8, 10, 12)


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
    if type(stages) is not list or len(stages) != len(_WORKER_COUNTS):
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


def archive_document(summary: object, *, version: str, now: datetime,
                     export_id: str, display_name: str = APPLICATION_NAME,
                     source_commit: str | None = None) -> dict:
    """Wrap an unchanged strictly sanitized diagnostic snapshot in the V1 standard."""
    if type(export_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", export_id):
        raise GitMeasurementError("invalid export identifier")
    if (type(display_name) is not str or not 1 <= len(display_name) <= 80
            or any(ord(char) < 32 or ord(char) > 126 for char in display_name)):
        raise GitMeasurementError("invalid application display name")
    if source_commit is not None and (
            type(source_commit) is not str or not COMMIT_RE.fullmatch(source_commit)):
        raise GitMeasurementError("invalid source commit")
    if type(version) is not str or not re.fullmatch(r"0\.1\.[0-9]{1,3}", version):
        raise GitMeasurementError("invalid testlab version")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise GitMeasurementError("invalid export time")
    normalized = now.astimezone(timezone.utc)
    captured = normalized.isoformat(timespec="seconds").replace("+00:00", "Z")
    if type(summary) is dict and summary.get("schema") == SUITE_SCHEMA:
        mode = summary.get("mode")
        snapshot = {
            "schema": SUITE_EXPORT_SCHEMA,
            "created_at": captured,
            "component": "deploy_relay_v2_dev",
            "version": version,
            "mode": "READ_ONLY_TEST",
            "suite": sanitized_suite(summary),
            "note": "Synthetic subprocess comparison, not individual DRA CPU attribution.",
        }
        test_id = "V2-READONLY-FULL" if mode == "full" else "V2-MULTICORE"
    else:
        snapshot = public_export_document(summary, version=version, now=normalized)
        test_id = "V2-CPU-RAM"
    return {
        "exportSchema": STANDARD_SCHEMA,
        "application": {
            "id": APPLICATION_ID, "name": display_name, "version": version,
        },
        "export": {"type": "diagnostics", "capturedAt": captured, "exportId": export_id},
        "source": {"repository": SOURCE_REPOSITORY, "commit": source_commit},
        "test": {
            "id": test_id, "capabilityId": None, "capabilityUiNumber": None,
        },
        # Full diagnostic schema remains unchanged inside snapshot.
        "snapshot": snapshot,
    }


def archive_path(document: dict) -> str:
    """Only fixed immutable technical application ID determines archive path."""
    if (type(document) is not dict or
            document.get("exportSchema") != STANDARD_SCHEMA or
            type(document.get("application")) is not dict or
            document["application"].get("id") != APPLICATION_ID or
            type(document.get("export")) is not dict or
            document["export"].get("type") != "diagnostics"):
        raise GitMeasurementError("invalid central export metadata")
    version = document["application"].get("version")
    if type(version) is not str or not re.fullmatch(r"0\.1\.[0-9]{1,3}", version):
        raise GitMeasurementError("invalid central export version")
    stamp = document["export"].get("capturedAt")
    eid = document["export"].get("exportId")
    if type(stamp) is not str or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", stamp):
        raise GitMeasurementError("invalid central export timestamp")
    if type(eid) is not str or not HEX_RE.fullmatch(eid):
        raise GitMeasurementError("invalid central export ID")
    # Validate actual UTC time, not just filename notation.
    try:
        when = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise GitMeasurementError("invalid central export timestamp") from None
    return (
        f"{ROOT}/{when:%Y-%m}/diagnostics/"
        f"{when:%Y-%m-%dT%H-%M-%SZ}__{APPLICATION_ID}__{version}__diagnostics__{eid}.json"
    )


def _archive_payload(summary, version: str, now: datetime,
                     export_id: str, display_name: str, source_commit: str | None):
    document = archive_document(
        summary, version=version, now=now, export_id=export_id,
        display_name=display_name, source_commit=source_commit,
    )
    path = archive_path(document)
    raw = (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
    if len(raw.encode("utf-8")) > MAX_EXPORT_BYTES:
        raise GitMeasurementError("central export exceeds size limit")
    # No arbitrary client-controlled text fields are carried over: snapshots
    # pass a complete allowlist, while all metadata comes from server constants.
    if any(word in raw.casefold() for word in (
            "authorization:", "github_pat_", "ghp_", "gho_", "ghu_",
            "password", "access_token", "private_key", "client_secret",
    )):
        raise GitMeasurementError("secret-like content blocked")
    return {"path": path, "export_id": export_id, "raw": raw}


def _validate_pending(value: object) -> dict | None:
    if value is None:
        return None
    if type(value) is not dict or set(value) != {"path", "export_id", "raw"}:
        raise GitMeasurementError("invalid central export recovery data")
    raw = value["raw"]
    if type(raw) is not str or len(raw.encode("utf-8")) > MAX_EXPORT_BYTES:
        raise GitMeasurementError("invalid central export recovery payload")
    try:
        document = json.loads(raw)
        app = document["application"]
        exp = document["export"]
        snap = document["snapshot"]
        source = document["source"]
        test = document["test"]
        if set(document) != {"exportSchema", "application", "export", "source", "test", "snapshot"}:
            raise ValueError()
        if (set(app) != {"id", "name", "version"} or set(exp) != {"type", "capturedAt", "exportId"}
                or set(source) != {"repository", "commit"} or source["repository"] != SOURCE_REPOSITORY
                or set(test) != {"id", "capabilityId", "capabilityUiNumber"}
                or test["capabilityId"] is not None or test["capabilityUiNumber"] is not None
                or type(test["id"]) is not str
                or set(snap) not in (
                    {"schema", "created_at", "component", "version", "mode", "suite", "note"},
                    {"schema", "created_at", "component", "version", "mode", "measurement", "note"},
                )
                or snap["version"] != app["version"]
                or snap["created_at"] != exp["capturedAt"]
                or value["export_id"] != exp["exportId"]
                or value["path"] != archive_path(document)):
            raise ValueError()
        if any(secret in raw.casefold() for secret in (
                "github_pat_", "ghp_", "gho_", "password", "authorization:", "access_token",
        )):
            raise ValueError()
    except (ValueError, KeyError, TypeError, AttributeError):
        raise GitMeasurementError("invalid central export recovery data") from None
    return dict(value)


class MeasurementGitExport:
    """One append-only private archive writer, never writes to source repository.

    Credentials must be provisioned to the Home Assistant server environment.
    The previous browser-entered public-export credential is never read or used.
    An unfinished sanitized report is persisted for explicit retry after failure.
    """

    def __init__(self, store: SecretStore, session: object, *,
                 token_provider=None) -> None:
        self._store = store
        self._session = session
        self._token_provider = token_provider or (lambda: os.environ.get(SERVER_TOKEN_ENV))
        self._lock = asyncio.Lock()
        self._ready = False
        self._pending: dict | None = None

    @property
    def available(self) -> bool:
        return self._ready

    @property
    def configured(self) -> bool:
        try:
            token = self._token_provider()
        except Exception:
            return False
        return type(token) is str and bool(TOKEN_RE.fullmatch(token))

    @property
    def pending(self) -> bool:
        return self._pending is not None

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "pending": self.pending,
            "repository": REPOSITORY,
        }

    async def load(self) -> None:
        try:
            value = await self._store.async_load()
        except Exception:
            raise GitMeasurementError("central export queue unavailable") from None
        if value is None:
            self._pending = None
        elif type(value) is dict and set(value) == {"schema", "pending"} and value["schema"] == QUEUE_SCHEMA:
            self._pending = _validate_pending(value["pending"])
        else:
            raise GitMeasurementError("central export recovery schema invalid")
        self._ready = True

    async def _persist(self, pending: dict | None) -> None:
        try:
            await self._store.async_save({"schema": QUEUE_SCHEMA, "pending": pending})
        except Exception:
            raise GitMeasurementError("central export cannot be saved locally") from None
        self._pending = pending

    async def configure(self, *, token: str = "", clear: bool = False) -> None:
        """Legacy browser token route deliberately disabled; no browser secrets."""
        raise GitMeasurementError("central export access must be configured on the server")

    async def export(self, summary: object, *, version: str,
                     display_name: str = APPLICATION_NAME,
                     source_commit: str | None = None) -> dict[str, str]:
        async with self._lock:
            if not self._ready:
                raise GitMeasurementError("central export unavailable")
            if not self.configured:
                raise GitMeasurementError("central archive permission not configured on server")
            if self._pending is not None:
                raise GitMeasurementError("unsent central export pending; retry it first")
            now = datetime.now(timezone.utc)
            data = _archive_payload(
                summary, version, now, secrets.token_hex(16),
                display_name, source_commit,
            )
            await self._persist(data)
            return await self._upload_pending()

    async def retry_pending(self) -> dict[str, str]:
        async with self._lock:
            if not self._ready or self._pending is None:
                raise GitMeasurementError("no local export awaiting upload")
            if not self.configured:
                raise GitMeasurementError("central archive permission not configured on server")
            return await self._upload_pending()

    async def _upload_pending(self) -> dict[str, str]:
        data = self._pending
        if data is None:
            raise GitMeasurementError("no local export awaiting upload")
        token = self._token_provider()
        if type(token) is not str or not TOKEN_RE.fullmatch(token):
            raise GitMeasurementError("central archive permission not configured on server")
        path = data["path"]
        url_path = "/".join(quote(piece, safe="") for piece in path.split("/"))
        url = f"https://api.github.com/repos/{REPOSITORY}/contents/{url_path}"
        content = base64.b64encode(data["raw"].encode("utf-8")).decode("ascii")
        try:
            async with asyncio.timeout(12):
                async with self._session.put(
                    url,
                    allow_redirects=False,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "Authorization": f"Bearer {token}",
                        "User-Agent": "DRA-V2-Private-Central-Export",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                    json={
                        "message": "chore(archive): new DRA V2 diagnostic [skip ci]",
                        "content": content, "branch": BRANCH,
                        # ABSENT sha: GitHub can CREATE, never UPDATE existing file.
                    },
                ) as response:
                    if response.status != 201:
                        raise GitMeasurementError(
                            "central archive upload rejected (check permission, path or collision)"
                        )
                    result = await response.json()
        except GitMeasurementError:
            raise
        except Exception:
            raise GitMeasurementError("central archive upload failed; local report retained") from None
        commit = result.get("commit") if type(result) is dict else None
        sha = commit.get("sha") if type(commit) is dict else None
        if type(sha) is not str or not COMMIT_RE.fullmatch(sha):
            raise GitMeasurementError("central archive confirmation invalid; local report retained")
        await self._persist(None)
        return {
            "repository": REPOSITORY, "branch": BRANCH, "path": path,
            "export_id": data["export_id"], "commit_sha": sha,
            "file_url": f"https://github.com/{REPOSITORY}/blob/{BRANCH}/{path}",
        }
