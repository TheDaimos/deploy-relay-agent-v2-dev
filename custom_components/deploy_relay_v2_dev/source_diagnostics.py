"""Bounded server-owned, allowlisted source-preview diagnostic records.

No repository names, refs, file paths, token values, raw exceptions, response
bodies or contents may enter a report or an export. Logs are session-local,
read-only, and cannot authorize a deployment.
"""
from __future__ import annotations

from collections import deque
import hashlib
import secrets

from .project_catalog import CatalogError, normalize_repo
from datetime import datetime, timezone
import re
from time import monotonic, process_time
from uuid import uuid4

SCHEMA = "dra-v2-dev-source-diagnostic.v1"
ALLOWED_STAGES = frozenset({
    "admission", "repository", "commit", "manifest", "tree",
    "local_inventory", "comparison", "target_claims",
})
ALLOWED_REASONS = frozenset({
    "none", "source_unavailable", "repository_access", "commit_unavailable",
    "manifest_invalid", "manifest_resource_limit", "manifest_remote_authentication",
    "manifest_remote_forbidden", "manifest_remote_not_found",
    "manifest_remote_rate_limited", "manifest_remote_http",
    "manifest_transport_invalid", "manifest_response_too_large",
    "manifest_json_invalid", "manifest_size_invalid",
    "manifest_encoding_invalid", "manifest_content_integrity",
    "manifest_schema_invalid", "manifest_identity_invalid",
    "manifest_source_unsupported", "manifest_policy_invalid",
    "manifest_groups_invalid", "manifest_target_protected", "tree_invalid",
    "tree_remote_authentication", "tree_remote_forbidden", "tree_remote_not_found",
    "tree_remote_rate_limited", "tree_remote_http", "tree_transport_invalid",
    "tree_response_too_large", "tree_json_invalid", "tree_incomplete",
    "tree_entry_limit", "tree_path_invalid", "tree_entry_invalid",
    "tree_file_invalid", "tree_source_empty", "tree_budget_exceeded",
    "local_inventory_invalid", "compare_invalid", "target_claim_invalid",
    "timeout", "unexpected_error",
})
MAX_REPORTS = 8
_FIELDS = frozenset({
    "schema", "run_id", "captured_at", "status", "stage",
    "reason", "duration_ms", "process_cpu_ms", "sources_verified", "installation_enabled",
    "resources", "steps", "project_ref",
})
_DATE_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
_HEX = re.compile(r"[a-f0-9]{32}\Z")
_PROJECT_REF = re.compile(r"P-[A-F0-9]{12}\Z")


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
        (value["project_ref"] is not None and (type(value["project_ref"]) is not str or
          not _PROJECT_REF.fullmatch(value["project_ref"]))) or
        type(value["captured_at"]) is not str or
        not _DATE_RE.fullmatch(value["captured_at"]) or
        type(value["stage"]) is not str or value["stage"] not in ALLOWED_STAGES or
        type(value["reason"]) is not str or value["reason"] not in ALLOWED_REASONS or
        value["status"] not in ("success", "failed") or
        type(value["status"]) is not str or
        type(value["duration_ms"]) is not int or not 0 <= value["duration_ms"] <= 60000 or
        type(value["process_cpu_ms"]) is not int or not 0 <= value["process_cpu_ms"] <= 1000000000 or
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
        # Exact fixed error text only, never arbitrary exceptions, raw GitHub
        # responses, secrets, repository identities or local filesystem paths.
        known = {
            "github_http_authentication": "manifest_remote_authentication",
            "github_http_forbidden": "manifest_remote_forbidden",
            "github_http_not_found": "manifest_remote_not_found",
            "github_http_rate_limited": "manifest_remote_rate_limited",
            "GitHub source unavailable or inaccessible": "manifest_remote_http",
            "GitHub request unsuccessful": "manifest_remote_http",
            "GitHub response could not be verified": "manifest_transport_invalid",
            "GitHub response exceeds size limit": "manifest_response_too_large",
            "invalid GitHub JSON": "manifest_json_invalid",
            "invalid manifest size": "manifest_size_invalid",
            "manifest is not an encoded file": "manifest_encoding_invalid",
            "manifest base64 invalid": "manifest_encoding_invalid",
            "invalid manifest encoding": "manifest_encoding_invalid",
            "manifest content integrity failed": "manifest_content_integrity",
            "unsupported manifest schema": "manifest_schema_invalid",
            "invalid project identity": "manifest_identity_invalid",
            "invalid source repository": "manifest_identity_invalid",
            "repository identity mismatch": "manifest_identity_invalid",
            "artifact source is not yet supported": "manifest_source_unsupported",
            "deployment root not approved": "manifest_policy_invalid",
            "symlinks not permitted": "manifest_policy_invalid",
            "invalid resource limit": "manifest_resource_limit",
            "invalid deployment groups": "manifest_groups_invalid",
            "deployment mode not approved": "manifest_groups_invalid",
            "overlapping deployment targets": "manifest_groups_invalid",
            "deployment target not approved for V2": "manifest_target_protected",
            "protected deployment target": "manifest_target_protected",
        }
        return known.get(str(error), "manifest_invalid")
    if stage == "tree":
        # Match only exact, internally authored exception messages.
        # Unknown or dynamically supplied error text is NEVER exported.
        lookup = {
            "github_http_authentication": "tree_remote_authentication",
            "github_http_forbidden": "tree_remote_forbidden",
            "github_http_not_found": "tree_remote_not_found",
            "github_http_rate_limited": "tree_remote_rate_limited",
            "GitHub source unavailable or inaccessible": "tree_remote_http",
            "GitHub request unsuccessful": "tree_remote_http",
            "GitHub response could not be verified": "tree_transport_invalid",
            "GitHub response exceeds size limit": "tree_response_too_large",
            "invalid GitHub JSON": "tree_json_invalid",
            "GitHub tree is incomplete": "tree_incomplete",
            "repository tree incomplete or too large": "tree_entry_limit",
            "invalid source path": "tree_path_invalid",
            "unsafe source path": "tree_path_invalid",
            "duplicate repository path": "tree_entry_invalid",
            "unsupported source entry (possibly symlink/submodule)": "tree_entry_invalid",
            "inconsistent source entry type": "tree_entry_invalid",
            "invalid repository tree entry": "tree_entry_invalid",
            "invalid source size": "tree_file_invalid",
            "invalid Git blob identity": "tree_file_invalid",
            "source directory empty": "tree_source_empty",
            "duplicate deployment file": "tree_entry_invalid",
            "source exceeds manifest budget": "tree_budget_exceeded",
        }
        return lookup.get(str(error), "tree_invalid")
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
        self._project_secret = secrets.token_bytes(32)
        self._private_repositories: dict[str, str] = {}

    def begin(self) -> dict:
        start = monotonic()
        return {"run_id": uuid4().hex, "started": start, "process_started": process_time(),
                "stage": "admission", "project_ref": None, "repository": None,
                "steps": [{"stage": "admission", "elapsed_ms": 0}]}

    def bind_project(self, context: dict, repository: str) -> str:
        """Attach server-verified project identity, never sent in ordinary logs."""
        try:
            canonical = normalize_repo(repository)
        except CatalogError:
            raise SourceDiagnosticsError("invalid project identity") from None
        if context.get("repository") is not None:
            raise SourceDiagnosticsError("diagnostic project already bound")
        digest = hashlib.blake2s(canonical.casefold().encode("ascii"),
                                  key=self._project_secret, digest_size=6).hexdigest().upper()
        reference = "P-" + digest
        context["repository"] = canonical
        context["project_ref"] = reference
        return reference

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
            # Shared HA process CPU time, NOT the CPU cost of DRA alone.
            "process_cpu_ms": min(1000000000, max(0, round(
                (process_time()-context["process_started"])*1000))),
            "resources": resources, "steps": steps,
            "project_ref": context["project_ref"],
            "sources_verified": bool(success),
            "installation_enabled": False,
        })
        if context["repository"] is not None:
            self._private_repositories[record["run_id"]] = context["repository"]
        if len(self._entries) == MAX_REPORTS:
            removed = self._entries[0]["run_id"]
            self._private_repositories.pop(removed, None)
        self._entries.append(record)
        return dict(record)

    def count(self) -> int:
        return len(self._entries)

    def private_repository_for(self, run_id: str) -> str | None:
        """Private Git sink only; never expose through generic WS / JSON."""
        return self._private_repositories.get(run_id)

    def clear(self, *, expected_run_id: str) -> int:
        """CAS clearing of ephemeral logs only; no Git files or export queue."""
        if (type(expected_run_id) is not str or not _HEX.fullmatch(expected_run_id)
                or not self._entries or self._entries[-1]["run_id"] != expected_run_id):
            raise SourceDiagnosticsError("logs changed or unavailable")
        cleared = len(self._entries)
        self._entries.clear()
        self._private_repositories.clear()
        return cleared

    def latest(self) -> dict | None:
        return sanitize_source_diagnostic(self._entries[-1]) if self._entries else None

    def entries(self) -> list[dict]:
        return [sanitize_source_diagnostic(row) for row in reversed(self._entries)]
