"""Server-only private central archive export of sanitized V2 DEV measurements.

The writer never touches V1 configuration, project files or the operation
journal. Each upload is administrator-triggered and targets an explicitly selected private repository.
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

SOURCE_REPOSITORY = "TheDaimos/deploy-relay-agent-v2-dev"
APPLICATION_ID = "deploy-relay-agent-v2"
APPLICATION_NAME = "Deploy Relay Agent V2"
STANDARD_SCHEMA = "daimos-project-log-export-v1"
QUEUE_SCHEMA = "dra-v2-dev-central-export-queue.v2"
LEGACY_QUEUE_SCHEMA = "dra-v2-dev-central-export-queue.v1"
SERVER_TOKEN_ENV = "DRA_V2_CENTRAL_EXPORT_TOKEN"
CREDENTIAL_SCHEMA = "dra-v2-dev-archive-credentials.v1"
BRANCH = "main"
ROOT = "exports/deploy-relay-agent-v2"
MEASUREMENT_SCHEMA = "dra-v2-dev-measurement.v2"
EXPORT_SCHEMA = "dra-v2-dev-git-measurement.v2"
SCOPE = "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY"
MAX_EXPORT_BYTES = 8192
TOKEN_RE = re.compile(r"[^\s\x00-\x1f\x7f]{10,256}\Z", re.ASCII)
HEX_RE = re.compile(r"[0-9a-f]{32}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
REPO_RE = re.compile(r"[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}\Z")
BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.\/-]{0,99}\Z")
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


def _validated_measurement_snapshot(value: object) -> dict:
    """Recheck persisted sanitized measurements without private operation IDs."""
    keys = {"scope", "base_seconds", "work_seconds", "after_seconds",
            "memory", *COUNTERS.keys()}
    if type(value) is not dict or set(value) != keys:
        raise GitMeasurementError("invalid archived measurement")
    if (value["scope"] != SCOPE or
            (value["base_seconds"], value["work_seconds"], value["after_seconds"])
            != (10, 20, 10)):
        raise GitMeasurementError("invalid archived measurement timing")
    metrics = {}
    for key, maximum in COUNTERS.items():
        n = value[key]
        if type(n) is not int or not 0 <= n <= maximum:
            raise GitMeasurementError("invalid archived measurement counters")
        metrics[key] = n
    return {
        "scope": SCOPE, "base_seconds": 10, "work_seconds": 20,
        "after_seconds": 10, **metrics,
        "memory": sanitized_memory(value["memory"]),
    }


def _validated_snapshot(value: object) -> tuple[dict, str]:
    """Rebuild only known diagnostic content, stripping no unknown fields."""
    if type(value) is not dict:
        raise GitMeasurementError("invalid archived snapshot")
    if set(value) == {
        "schema", "created_at", "component", "version", "mode", "suite", "note",
    } and value["schema"] == SUITE_EXPORT_SCHEMA:
        report = value["suite"]
        if type(report) is not dict or set(report) != {
            "schema", "mode", "readonly_steps", "measurement", "multicore",
        } or report["schema"] != SUITE_SCHEMA or report["mode"] not in ("full", "multicore"):
            raise GitMeasurementError("invalid archived suite")
        if type(report["mode"]) is not str or type(report["readonly_steps"]) is not int:
            raise GitMeasurementError("invalid archived suite mode")
        if report["readonly_steps"] != (40 if report["mode"] == "full" else 0):
            raise GitMeasurementError("invalid archived suite steps")
        if report["mode"] == "full":
            measurement = _validated_measurement_snapshot(report["measurement"])
        else:
            if report["measurement"] is not None:
                raise GitMeasurementError("invalid archived multicore-only suite")
            measurement = None
        sanitized = {
            "schema": SUITE_SCHEMA, "mode": report["mode"],
            "readonly_steps": report["readonly_steps"],
            "measurement": measurement,
            "multicore": sanitized_multicore(report["multicore"]),
        }
        expected_note = "Synthetic subprocess comparison, not individual DRA CPU attribution."
        test_id = "V2-READONLY-FULL" if report["mode"] == "full" else "V2-MULTICORE"
        key = "suite"
    elif set(value) == {
        "schema", "created_at", "component", "version", "mode", "measurement", "note",
    } and value["schema"] == EXPORT_SCHEMA:
        sanitized = _validated_measurement_snapshot(value["measurement"])
        expected_note = "Synthetic workload. CPU measured across the whole HA process, not DRA alone."
        test_id = "V2-CPU-RAM"
        key = "measurement"
    else:
        raise GitMeasurementError("unknown archived diagnostic")
    if (value["component"] != "deploy_relay_v2_dev" or value["mode"] != "READ_ONLY_TEST"
            or value["note"] != expected_note):
        raise GitMeasurementError("invalid archived measurement provenance")
    return {
        "schema": value["schema"], "created_at": value["created_at"],
        "component": "deploy_relay_v2_dev", "version": value["version"],
        "mode": "READ_ONLY_TEST", key: sanitized, "note": expected_note,
    }, test_id


def validate_archive_repository(repository: object) -> str:
    """Explicit GitHub owner/repo only, never a URL, preset or arbitrary host."""
    if type(repository) is not str or not REPO_RE.fullmatch(repository):
        raise GitMeasurementError("invalid archive repository")
    owner, name = repository.split("/", 1)
    if owner.startswith("-") or owner.endswith("-") or name in (".", ".."):
        raise GitMeasurementError("invalid archive repository")
    if name.startswith(".") or name.endswith("."):
        raise GitMeasurementError("invalid archive repository")
    return repository


def validate_archive_branch(branch: object) -> str:
    if (type(branch) is not str or not BRANCH_RE.fullmatch(branch)
            or branch.endswith((".", "/", ".lock")) or ".." in branch
            or "//" in branch or "/." in branch or "@{" in branch):
        raise GitMeasurementError("invalid private archive default branch")
    return branch


def _validate_pending(value: object) -> dict | None:
    if value is None:
        return None
    if type(value) is not dict or set(value) != {"path", "export_id", "raw", "repository"}:
        raise GitMeasurementError("invalid central export recovery data")
    validate_archive_repository(value["repository"])
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
        if (document["exportSchema"] != STANDARD_SCHEMA or
                type(app["name"]) is not str or not 1 <= len(app["name"]) <= 80 or
                any(ord(char) < 32 or ord(char) > 126 for char in app["name"])):
            raise ValueError()
        commit = source["commit"]
        if commit is not None and (type(commit) is not str or not COMMIT_RE.fullmatch(commit)):
            raise ValueError()
        rebuilt, expected_test = _validated_snapshot(snap)
        if (rebuilt != snap or test["id"] != expected_test or
                type(test["id"]) is not str or
                json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" != raw):
            raise ValueError()
        if any(secret in raw.casefold() for secret in (
                "github_pat_", "ghp_", "gho_", "password", "authorization:", "access_token",
        )):
            raise ValueError()
    except (ValueError, KeyError, TypeError, AttributeError):
        raise GitMeasurementError("invalid central export recovery data") from None
    return dict(value)


class MeasurementGitExport:
    """Private opt-in archive export with no predefined destination repository.

    Credentials may be entered once via authenticated HA websocket and are
    immediately stored in an independent private HA server Store, or supplied
    by the legacy environment variable. Neither queue nor exports contain keys.
    An unsent report is bound to its original repository and cannot be sent
    elsewhere by changing preferences.
    """

    def __init__(self, store: SecretStore, session: object, *,
                 token_provider=None, credential_store=None) -> None:
        self._store = store
        self._session = session
        self._token_provider = token_provider or (lambda: os.environ.get(SERVER_TOKEN_ENV))
        self._credential_store = credential_store
        self._credential_repository: str | None = None
        self._credential_token: str | None = None
        self._lock = asyncio.Lock()
        self._ready = False
        self._repository: str | None = None
        self._pending: dict | None = None

    @property
    def available(self) -> bool:
        return self._ready

    @property
    def repository(self) -> str | None:
        return self._repository

    def _current_token(self) -> str | None:
        """Never reuse a saved token for a different repository."""
        if self._credential_repository is not None:
            if self._credential_repository != self._repository:
                return None
            return self._credential_token
        try:
            token = self._token_provider()
        except Exception:
            return None
        return token if type(token) is str and bool(TOKEN_RE.fullmatch(token)) else None

    @property
    def server_token_available(self) -> bool:
        return self._current_token() is not None

    @property
    def configured(self) -> bool:
        return self._repository is not None and self.server_token_available

    @property
    def pending(self) -> bool:
        return self._pending is not None

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "repository_configured": self._repository is not None,
            "server_token_available": self.server_token_available,
            "pending": self.pending,
            "repository": self._repository,
        }

    async def load(self) -> None:
        try:
            value = await self._store.async_load()
        except Exception:
            raise GitMeasurementError("central export configuration unavailable") from None
        if value is None:
            # No user or vendor repository is ever configured by default.
            repository = None
            pending = None
        elif (type(value) is dict and set(value) == {"schema", "pending"}
              and value["schema"] == LEGACY_QUEUE_SCHEMA):
            # Safe migration only of an EMPTY old queue. Previous records
            # lacked target binding, so silently redirecting them is forbidden.
            if value["pending"] is not None:
                raise GitMeasurementError("legacy archive pending item requires review")
            repository = None
            pending = None
        elif (type(value) is dict and set(value) == {"schema", "repository", "pending"}
              and value["schema"] == QUEUE_SCHEMA):
            repository = value["repository"]
            if repository is not None:
                repository = validate_archive_repository(repository)
            pending = _validate_pending(value["pending"])
            if pending is not None and (repository is None or
                                        pending["repository"] != repository):
                raise GitMeasurementError("central export target mismatch")
        else:
            raise GitMeasurementError("central export configuration schema invalid")
        credential_repo = None
        credential_token = None
        if self._credential_store is not None:
            try:
                credentials = await self._credential_store.async_load()
            except Exception:
                raise GitMeasurementError("private archive credentials unavailable") from None
            if credentials is not None:
                if (type(credentials) is not dict or set(credentials) !=
                        {"schema", "repository", "token"} or
                        credentials["schema"] != CREDENTIAL_SCHEMA):
                    raise GitMeasurementError("private archive credential schema invalid")
                credential_repo = validate_archive_repository(credentials["repository"])
                credential_token = credentials["token"]
                if (type(credential_token) is not str or
                        not TOKEN_RE.fullmatch(credential_token)):
                    raise GitMeasurementError("private archive credential invalid")
        self._credential_repository = credential_repo
        self._credential_token = credential_token
        self._repository = repository
        self._pending = pending
        self._ready = True

    async def _persist(self, repository: str | None, pending: dict | None) -> None:
        if repository is not None:
            validate_archive_repository(repository)
        if pending is not None:
            pending = _validate_pending(pending)
            if repository != pending["repository"]:
                raise GitMeasurementError("central export target mismatch")
        try:
            await self._store.async_save({
                "schema": QUEUE_SCHEMA, "repository": repository,
                "pending": pending,
            })
        except Exception:
            raise GitMeasurementError("central archive configuration could not be saved") from None
        self._repository = repository
        self._pending = pending

    async def configure_archive(self, repository: str, token: str) -> dict:
        """Verify an explicitly entered private GitHub destination and secret.

        The token is presented once by an HA admin over WebSocket, then only
        stored server-side in the independent HA credential Store. Changes do
        not affect an unfinished diagnostic. Failure cannot redirect a token
        to a different previously configured repository.
        """
        selected = validate_archive_repository(repository)
        if type(token) is not str or not TOKEN_RE.fullmatch(token):
            raise GitMeasurementError("invalid GitHub archive credential")
        async with self._lock:
            if not self._ready or self._credential_store is None:
                raise GitMeasurementError("private archive credentials unavailable")
            if self._pending is not None:
                raise GitMeasurementError("pending archive export must be resolved first")
            # Establish privacy and read access before accepting configuration.
            await self._ensure_private_repository(token, selected)
            try:
                await self._credential_store.async_save({
                    "schema": CREDENTIAL_SCHEMA,
                    "repository": selected,
                    "token": token,
                })
            except Exception:
                raise GitMeasurementError("private archive credential could not be saved") from None
            self._credential_repository = selected
            self._credential_token = token
            if self._repository != selected:
                await self._persist(selected, None)
            return self.status()

    async def set_repository(self, repository: str) -> dict:
        """Explicit admin selection; cannot redirect a pending report."""
        selected = validate_archive_repository(repository)
        async with self._lock:
            if not self._ready:
                raise GitMeasurementError("central archive unavailable")
            if self._pending is not None:
                raise GitMeasurementError("finish pending export before changing archive")
            if self._repository != selected:
                await self._persist(selected, None)
            return self.status()

    async def clear_repository(self) -> dict:
        async with self._lock:
            if not self._ready:
                raise GitMeasurementError("central archive unavailable")
            if self._pending is not None:
                raise GitMeasurementError("finish pending export before changing archive")
            # Revoke the saved credential first so an interrupted clear never
            # leaves a reusable token paired with an unintended destination.
            if self._credential_store is not None and self._credential_repository is not None:
                try:
                    await self._credential_store.async_save(None)
                except Exception:
                    raise GitMeasurementError("private archive credential could not be cleared") from None
                self._credential_repository = None
                self._credential_token = None
            if self._repository is not None:
                await self._persist(None, None)
            return self.status()

    async def configure(self, *, token: str = "", clear: bool = False) -> None:
        """Never accept browser-entered GitHub credentials."""
        raise GitMeasurementError("central export access must be configured on the server")

    def local_download(self, summary: object, *, version: str,
                       display_name: str = APPLICATION_NAME,
                       source_commit: str | None = None) -> dict[str, str]:
        """Return a sanitized JSON file independently of GitHub configuration.

        A download NEVER touches the queue, uses tokens or sends any network
        requests. It produces the same mandatory archive metadata and immutable
        technical application ID as a GitHub upload.
        """
        now = datetime.now(timezone.utc)
        payload = _archive_payload(
            summary, version, now, secrets.token_hex(16),
            display_name, source_commit,
        )
        filename = payload["path"].rsplit("/", 1)[-1]
        return {
            "filename": filename,
            "content": payload["raw"],
            "export_id": payload["export_id"],
            "application_id": APPLICATION_ID,
            "mime_type": "application/json",
        }

    async def export(self, summary: object, *, version: str,
                     display_name: str = APPLICATION_NAME,
                     source_commit: str | None = None) -> dict[str, str]:
        async with self._lock:
            if not self._ready:
                raise GitMeasurementError("central archive unavailable")
            if self._repository is None:
                raise GitMeasurementError("configure a private destination repository first")
            if not self.server_token_available:
                raise GitMeasurementError("central archive server permission not configured")
            if self._pending is not None:
                raise GitMeasurementError("unsent central export pending; retry it first")
            now = datetime.now(timezone.utc)
            data = _archive_payload(
                summary, version, now, secrets.token_hex(16),
                display_name, source_commit,
            )
            data["repository"] = self._repository
            await self._persist(self._repository, data)
            return await self._upload_pending()

    async def retry_pending(self) -> dict[str, str]:
        async with self._lock:
            if not self._ready or self._pending is None:
                raise GitMeasurementError("no local export awaiting upload")
            if not self.configured:
                raise GitMeasurementError("central archive target or permission not configured")
            return await self._upload_pending()

    async def _ensure_private_repository(self, token: str, repository: str) -> str:
        """Verify explicitly selected target is private before EVERY upload."""
        repository = validate_archive_repository(repository)
        url = f"https://api.github.com/repos/{repository}"
        try:
            async with asyncio.timeout(8):
                async with self._session.get(
                    url,
                    allow_redirects=False,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "Authorization": f"Bearer {token}",
                        "User-Agent": "DRA-V2-Private-Central-Export",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                ) as response:
                    if response.status != 200:
                        raise GitMeasurementError(
                            "central archive cannot verify private repository access"
                        )
                    payload = await response.content.read(8193)
                    if len(payload) > 8192:
                        raise GitMeasurementError("central archive repository response too large")
                    metadata = json.loads(payload)
        except GitMeasurementError:
            raise
        except Exception:
            raise GitMeasurementError("central archive visibility unavailable") from None
        if (type(metadata) is not dict or
                metadata.get("full_name") != repository or
                metadata.get("private") is not True):
            raise GitMeasurementError("central archive is not confirmed private")
        return validate_archive_branch(metadata.get("default_branch"))

    async def _upload_pending(self) -> dict[str, str]:
        data = self._pending
        if data is None:
            raise GitMeasurementError("no local export awaiting upload")
        token = self._current_token()
        if token is None:
            raise GitMeasurementError("central archive permission not configured on server")
        repository = data["repository"]
        if self._repository != repository:
            raise GitMeasurementError("central archive pending target mismatch")
        branch = await self._ensure_private_repository(token, repository)
        path = data["path"]
        url_path = "/".join(quote(piece, safe="") for piece in path.split("/"))
        url = f"https://api.github.com/repos/{repository}/contents/{url_path}"
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
                        "content": content, "branch": branch,
                        # No 'sha': GitHub CREATE only, never overwrites a file.
                    },
                ) as response:
                    if response.status != 201:
                        raise GitMeasurementError(
                            "private archive upload rejected (check permission or collision)"
                        )
                    result = await response.json()
        except GitMeasurementError:
            raise
        except Exception:
            raise GitMeasurementError("private archive upload failed; local report retained") from None
        commit = result.get("commit") if type(result) is dict else None
        sha = commit.get("sha") if type(commit) is dict else None
        if type(sha) is not str or not COMMIT_RE.fullmatch(sha):
            raise GitMeasurementError("archive confirmation invalid; local report retained")
        await self._persist(repository, None)
        url_branch = quote(branch, safe="/")
        return {
            "repository": repository, "branch": branch, "path": path,
            "export_id": data["export_id"], "commit_sha": sha,
            "file_url": f"https://github.com/{repository}/blob/{url_branch}/{path}",
        }
