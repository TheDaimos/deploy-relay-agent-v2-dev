"""Bounded server-owned, allowlisted source-preview diagnostic records.

No repository names, refs, file paths, token values, raw exceptions, response
bodies or contents may enter a report or an export. Logs are session-local,
read-only, and cannot authorize a deployment.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import re
from time import monotonic
from uuid import uuid4

SCHEMA = "dra-v2-dev-source-diagnostic.v1"
ALLOWED_STAGES = frozenset({
    "admission", "repository", "commit", "manifest", "tree",
    "local_inventory", "comparison", "target_claims",
})
ALLOWED_REASONS = frozenset({
    "none", "source_unavailable", "repository_access", "commit_unavailable",
    "manifest_invalid", "manifest_resource_limit", "tree_invalid",
    "local_inventory_invalid", "compare_invalid", "target_claim_invalid",
    "timeout", "unexpected_error",
})
MAX_REPORTS = 8
_FIELDS = frozenset({
    "schema", "run_id", "captured_at", "status", "stage",
    "reason", "duration_ms", "sources_verified", "installation_enabled",
    "resources", "steps",
})
_DATE_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
_HEX = re.compile(r"[a-f0-9]{32}\Z")


RESOURCE_FIELDS = frozenset({
    "available_cores", "configured_readonly_jobs", "configured_worker_processes",
    "configured_mode", "active_readonly_limit", "active_mutation_limit",
    "worker_budget_enforced",
})


def sanitize_resources(value: object) -> dict:
    if type(value) is not dict or set(value) != RESOURCE_FIELDS:
        raise SourceDiagnosticsError("invalid resources")
    if (value["available_cores"] is not None and
        (type(value["available_cores"]) is not int or
         not 1 <= value["available_cores"] <= 4096)):
        raise SourceDiagnosticsError("invalid available cores")
    if (type(value["configured_readonly_jobs"]) is not int or
        not 1 <= value["configured_readonly_jobs"] <= 4 or
        type(value["configured_worker_processes"]) is not int or
        not 1 <= value["configured_worker_processes"] <= 12 or
        value["configured_mode"] not in ("sequential", "controlled") or
        type(value["configured_mode"]) is not str or
        value["active_readonly_limit"] != 1 or
        type(value["active_readonly_limit"]) is not int or
        value["active_mutation_limit"] != 0 or
        type(value["active_mutation_limit"]) is not int or
        value["worker_budget_enforced"] is not False):
        raise SourceDiagnosticsError("invalid runtime resource limits")
    return dict(value)


def resource_snapshot(settings) -> dict:
    configured = settings.snapshot()
    observed = settings.core_status()
    effective = settings.effective()
    return sanitize_resources({
        "available_cores": observed["available_cores"],
        "configured_readonly_jobs": configured["max_readonly_jobs"],
        "configured_worker_processes": configured["max_worker_processes"],
        "configured_mode": configured["mode"],
        "active_readonly_limit": effective["active_readonly_limit"],
        "active_mutation_limit": effective["mutation_limit"],
        "worker_budget_enforced": effective["worker_budget_enforced"],
    })


def sanitize_steps(steps: object, duration: int) -> list[dict]:
    if type(steps) is not list or not 1 <= len(steps) <= 12:
        raise SourceDiagnosticsError("invalid diagnostic stage sequence")
    checked = []
    prev = -1
    for step in steps:
        if (type(step) is not dict or set(step) != {"stage", "elapsed_ms"} or
            type(step["stage"]) is not str or step["stage"] not in ALLOWED_STAGES or
            type(step["elapsed_ms"]) is not int or
            not prev <= step["elapsed_ms"] <= duration):
            raise SourceDiagnosticsError("invalid diagnostic stage")
        prev = step["elapsed_ms"]
        checked.append(dict(step))
    return checked


class SourceDiagnosticsError(ValueError):
    """Invalid or forged diagnostic payload, no raw details."""


def sanitize_source_diagnostic(value: object) -> dict:
    if type(value) is not dict or set(value) != _FIELDS:
        raise SourceDiagnosticsError("invalid source diagnostic schema")
    if (value["schema"] != SCHEMA or
        type(value["run_id"]) is not str or not _HEX.fullmatch(value["run_id"]) or
        type(value["captured_at"]) is not str or
        not _DATE_RE.fullmatch(value["captured_at"]) or
        type(value["stage"]) is not str or value["stage"] not in ALLOWED_STAGES or
        type(value["reason"]) is not str or value["reason"] not in ALLOWED_REASONS or
        value["status"] not in ("success", "failed") or
        type(value["status"]) is not str or
        type(value["duration_ms"]) is not int or not 0 <= value["duration_ms"] <= 60000 or
        type(value["sources_verified"]) is not bool or
        value["installation_enabled"] is not False or
        (value["status"] == "success") != (value["sources_verified"] is True) or
        (value["status"] == "success" and value["reason"] != "none") or
        (value["status"] == "failed" and value["reason"] == "none")):
        raise SourceDiagnosticsError("invalid source diagnostic")
    resources = sanitize_resources(value["resources"])
    steps = sanitize_steps(value["steps"], value["duration_ms"])
    try:
        datetime.strptime(value["captured_at"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SourceDiagnosticsError("invalid diagnostic time") from None
    return {**value, "resources": resources, "steps": steps}


def classify_source_failure(stage: str, error: BaseException) -> str:
    # Never serialize str(error). All output is a fixed category.
    if isinstance(error, TimeoutError):
        return "timeout"
    if stage == "repository":
        return "repository_access"
    if stage == "commit":
        return "commit_unavailable"
    if stage == "manifest":
        if str(error) == "invalid resource limit":
            return "manifest_resource_limit"
        return "manifest_invalid"
    if stage == "tree":
        return "tree_invalid"
    if stage == "local_inventory":
        return "local_inventory_invalid"
    if stage == "comparison":
        return "compare_invalid"
    if stage == "target_claims":
        return "target_claim_invalid"
    return "source_unavailable"


class SourceDiagnosticLog:
    def __init__(self) -> None:
        self._entries: deque[dict] = deque(maxlen=MAX_REPORTS)

    def begin(self) -> dict:
        start = monotonic()
        return {"run_id": uuid4().hex, "started": start, "stage": "admission",
                "steps": [{"stage": "admission", "elapsed_ms": 0}]}

    @staticmethod
    def stage(context: dict, name: str) -> None:
        if name not in ALLOWED_STAGES:
            raise SourceDiagnosticsError("invalid diagnostic stage")
        context["stage"] = name
        context["steps"].append({
            "stage": name,
            "elapsed_ms": min(60000, max(0, round((monotonic()-context["started"])*1000))),
        })

    def finish(self, context: dict, *, success: bool, resources: dict,
               reason: str = "none") -> dict:
        duration = min(60000, max(0, round((monotonic()-context["started"])*1000)))
        steps = [dict(row, elapsed_ms=min(row["elapsed_ms"], duration))
                 for row in context["steps"]]
        record = sanitize_source_diagnostic({
            "schema": SCHEMA,
            "run_id": context["run_id"],
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "success" if success else "failed",
            "stage": context["stage"],
            "reason": reason,
            "duration_ms": duration,
            "resources": resources, "steps": steps,
            "sources_verified": bool(success),
            "installation_enabled": False,
        })
        self._entries.append(record)
        return dict(record)

    def latest(self) -> dict | None:
        return sanitize_source_diagnostic(self._entries[-1]) if self._entries else None

    def entries(self) -> list[dict]:
        return [sanitize_source_diagnostic(row) for row in reversed(self._entries)]
