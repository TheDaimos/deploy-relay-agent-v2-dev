"""Structured diagnostics and persistent rotating logs for Deploy Relay."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from time import monotonic
import traceback
from typing import Any
from uuid import uuid4

from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant

from .const import DEPLOY_DATA_DIR, VERSION
from .error_fingerprint import (
    fingerprint_exception,
    fingerprint_serialized_event,
)
from .redaction import redact_value

_LOGGER = logging.getLogger(__name__)

_MEMORY_EVENTS = 5000
_MAX_LOG_BYTES = 2 * 1024 * 1024
_ROTATED_FILES = 5
_LOG_FILENAME = "deploy-relay.jsonl"


def _utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _run_id(operation: str) -> str:
    """Create a compact human-readable correlation id."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_operation = "".join(
        char if char.isalnum() else "-" for char in operation.casefold()
    ).strip("-")[:24] or "run"
    return f"dra-{timestamp}-{safe_operation}-{uuid4().hex[:8]}"


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """One already-redacted structured diagnostic event."""

    event_id: str
    timestamp: str
    level: str
    component: str
    operation: str | None
    phase: str | None
    run_id: str | None
    project_id: str | None
    repository: str | None
    message: str
    duration_ms: float | None
    details: dict[str, Any] | None
    exception: dict[str, Any] | None
    deploy_relay_version: str
    home_assistant_version: str
    error_fingerprint: str | None
    error_family_fingerprint: str | None


class DiagnosticRun:
    """One correlated operation with phase timing."""

    def __init__(
        self,
        store: "DiagnosticStore",
        *,
        operation: str,
        run_id: str,
        project_id: str | None,
        repository: str | None,
        context: dict[str, Any] | None,
    ) -> None:
        self._store = store
        self.operation = operation
        self.run_id = run_id
        self.project_id = project_id
        self.repository = repository
        self.context = context or {}
        self._started = monotonic()
        self._phase_started: dict[str, float] = {}
        self._finished = False

    async def event(
        self,
        level: str,
        component: str,
        message: str,
        *,
        phase: str | None = None,
        details: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Write one correlated event."""
        await self._store.async_event(
            level,
            component,
            message,
            operation=self.operation,
            phase=phase,
            run_id=self.run_id,
            project_id=self.project_id,
            repository=self.repository,
            details=details,
            duration_ms=duration_ms,
        )

    async def debug(self, component: str, message: str, **kwargs: Any) -> None:
        await self.event("DEBUG", component, message, **kwargs)

    async def info(self, component: str, message: str, **kwargs: Any) -> None:
        await self.event("INFO", component, message, **kwargs)

    async def warning(self, component: str, message: str, **kwargs: Any) -> None:
        await self.event("WARNING", component, message, **kwargs)

    def start_phase(self, phase: str) -> None:
        """Start timing one named phase."""
        self._phase_started[phase] = monotonic()

    def phase_duration_ms(self, phase: str) -> float | None:
        """Return elapsed milliseconds for one phase."""
        started = self._phase_started.pop(phase, None)
        if started is None:
            return None
        return round((monotonic() - started) * 1000, 3)

    async def success(
        self,
        *,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """Finish a run successfully."""
        if self._finished:
            return
        self._finished = True
        await self._store.async_event(
            "INFO",
            "operation",
            "Operation completed",
            operation=self.operation,
            phase="complete",
            run_id=self.run_id,
            project_id=self.project_id,
            repository=self.repository,
            details={"status": "success", **(summary or {})},
            duration_ms=round((monotonic() - self._started) * 1000, 3),
        )

    async def fail(
        self,
        err: BaseException,
        *,
        phase: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Finish a run with a redacted exception and traceback."""
        if self._finished:
            return
        self._finished = True
        await self._store.async_exception(
            err,
            component="operation",
            operation=self.operation,
            phase=phase or "failed",
            run_id=self.run_id,
            project_id=self.project_id,
            repository=self.repository,
            details={"status": "error", **(details or {})},
            duration_ms=round((monotonic() - self._started) * 1000, 3),
        )


class DiagnosticStore:
    """Secret-safe ring buffer plus rotating JSONL persistence."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._events: deque[dict[str, Any]] = deque(maxlen=_MEMORY_EVENTS)
        self._secrets: set[str] = set()
        self._lock = asyncio.Lock()
        self._log_dir = Path(hass.config.path(DEPLOY_DATA_DIR, "logs"))
        self._log_file = self._log_dir / _LOG_FILENAME

    def register_secret(self, secret: str | None) -> None:
        """Register a secret for exact-value redaction."""
        if secret and len(secret) >= 6:
            self._secrets.add(secret)

    async def async_initialize(self) -> None:
        """Create log storage and restore recent sanitized events."""
        loaded = await self._hass.async_add_executor_job(self._load_sync)
        self._events.extend(loaded)

        await self.async_event(
            "INFO",
            "runtime",
            "Deploy Relay diagnostics initialized",
            operation="runtime",
            phase="startup",
            details={
                "deploy_relay_version": VERSION,
                "home_assistant_version": HA_VERSION,
                "persistence": str(self._log_file),
                "memory_event_limit": _MEMORY_EVENTS,
                "rotation_bytes": _MAX_LOG_BYTES,
                "rotation_files": _ROTATED_FILES,
            },
        )

    def _paths_oldest_first(self) -> list[Path]:
        paths = [
            self._log_dir / f"deploy-relay.{index}.jsonl"
            for index in range(_ROTATED_FILES, 0, -1)
        ]
        paths.append(self._log_file)
        return paths

    def _load_sync(self) -> deque[dict[str, Any]]:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        events: deque[dict[str, Any]] = deque(maxlen=_MEMORY_EVENTS)
        for path in self._paths_oldest_first():
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        try:
                            payload = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(payload, dict):
                            events.append(payload)
            except OSError:
                continue
        return events

    def _rotate_sync(self, incoming_bytes: int) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)

        if self._log_file.exists():
            try:
                current_size = self._log_file.stat().st_size
            except OSError:
                current_size = 0
            if current_size + incoming_bytes <= _MAX_LOG_BYTES:
                return
        else:
            return

        oldest = self._log_dir / f"deploy-relay.{_ROTATED_FILES}.jsonl"
        if oldest.exists():
            oldest.unlink(missing_ok=True)

        for index in range(_ROTATED_FILES - 1, 0, -1):
            source = self._log_dir / f"deploy-relay.{index}.jsonl"
            target = self._log_dir / f"deploy-relay.{index + 1}.jsonl"
            if source.exists():
                source.replace(target)

        self._log_file.replace(self._log_dir / "deploy-relay.1.jsonl")

    def _append_sync(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ) + "\n"
        raw = encoded.encode("utf-8")
        self._rotate_sync(len(raw))
        self._log_dir.mkdir(parents=True, exist_ok=True)
        with self._log_file.open("ab") as handle:
            handle.write(raw)

    async def _persist(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            await self._hass.async_add_executor_job(self._append_sync, payload)

    def _sanitize(self, value: Any) -> Any:
        return redact_value(value, tuple(self._secrets))

    async def async_event(
        self,
        level: str,
        component: str,
        message: str,
        *,
        operation: str | None = None,
        phase: str | None = None,
        run_id: str | None = None,
        project_id: str | None = None,
        repository: str | None = None,
        details: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        exception: dict[str, Any] | None = None,
        error_fingerprint: str | None = None,
        error_family_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        """Record one event after central redaction."""
        normalized_level = level.upper()
        if normalized_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            normalized_level = "INFO"

        event = DiagnosticEvent(
            event_id=uuid4().hex,
            timestamp=_utc_now(),
            level=normalized_level,
            component=str(self._sanitize(component)),
            operation=str(self._sanitize(operation)) if operation else None,
            phase=str(self._sanitize(phase)) if phase else None,
            run_id=str(self._sanitize(run_id)) if run_id else None,
            project_id=str(self._sanitize(project_id)) if project_id else None,
            repository=str(self._sanitize(repository)) if repository else None,
            message=str(self._sanitize(message)),
            duration_ms=duration_ms,
            details=self._sanitize(details) if details is not None else None,
            exception=self._sanitize(exception) if exception is not None else None,
            deploy_relay_version=VERSION,
            home_assistant_version=HA_VERSION,
            error_fingerprint=error_fingerprint,
            error_family_fingerprint=error_family_fingerprint,
        )
        payload = asdict(event)
        self._events.append(payload)

        level_no = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }[normalized_level]
        _LOGGER.log(
            level_no,
            "[%s] %s/%s: %s",
            event.run_id or "-",
            event.operation or event.component,
            event.phase or "-",
            event.message,
        )

        await self._persist(payload)
        return payload

    async def async_exception(
        self,
        err: BaseException,
        *,
        component: str,
        operation: str | None = None,
        phase: str | None = None,
        run_id: str | None = None,
        project_id: str | None = None,
        repository: str | None = None,
        details: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> dict[str, Any]:
        """Record a full redacted exception payload."""
        fingerprint = fingerprint_exception(
            err,
            component=component,
            operation=operation,
            phase=phase,
        )
        previous_exact = 0
        previous_family = 0
        previous_variants: set[str] = set()
        for event in self._events:
            if project_id and event.get("project_id") != project_id:
                continue
            event_fp = event.get("error_fingerprint")
            family_fp = event.get("error_family_fingerprint")
            if not event_fp or not family_fp:
                derived = fingerprint_serialized_event(event)
                if derived is not None:
                    event_fp = derived.exact
                    family_fp = derived.family
            if event_fp == fingerprint.exact:
                previous_exact += 1
            if family_fp == fingerprint.family:
                previous_family += 1
                if isinstance(event_fp, str):
                    previous_variants.add(event_fp)

        exception = {
            "type": type(err).__name__,
            "message": str(err),
            "traceback": "".join(
                traceback.format_exception(type(err), err, err.__traceback__)
            ),
            "fingerprint": fingerprint.exact,
            "family_fingerprint": fingerprint.family,
            "stack_signature": list(fingerprint.stack_signature),
            "deploy_relay_version": VERSION,
            "home_assistant_version": HA_VERSION,
        }
        history_details = {
            **(details or {}),
            "error_history_before": {
                "exact_occurrences": previous_exact,
                "family_occurrences": previous_family,
                "family_variants": len(previous_variants),
                "known_exact": previous_exact > 0,
                "known_family": previous_family > 0,
            },
        }
        return await self.async_event(
            "ERROR",
            component,
            f"{type(err).__name__}: {err}",
            operation=operation,
            phase=phase,
            run_id=run_id,
            project_id=project_id,
            repository=repository,
            details=history_details,
            duration_ms=duration_ms,
            exception=exception,
            error_fingerprint=fingerprint.exact,
            error_family_fingerprint=fingerprint.family,
        )

    async def async_start_run(
        self,
        operation: str,
        *,
        project_id: str | None = None,
        repository: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> DiagnosticRun:
        """Start one correlated operation."""
        run = DiagnosticRun(
            self,
            operation=operation,
            run_id=_run_id(operation),
            project_id=project_id,
            repository=repository,
            context=context,
        )
        await self.async_event(
            "INFO",
            "operation",
            "Operation started",
            operation=operation,
            phase="start",
            run_id=run.run_id,
            project_id=project_id,
            repository=repository,
            details={"status": "running", **(context or {})},
        )
        return run

    def query(
        self,
        *,
        limit: int = 1000,
        levels: set[str] | None = None,
        operation: str | None = None,
        run_id: str | None = None,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return newest matching events in chronological order."""
        bounded_limit = max(1, min(int(limit), _MEMORY_EVENTS))
        normalized_levels = {item.upper() for item in levels} if levels else None

        matched: list[dict[str, Any]] = []
        for event in reversed(self._events):
            if normalized_levels and event.get("level") not in normalized_levels:
                continue
            if operation and event.get("operation") != operation:
                continue
            if run_id and event.get("run_id") != run_id:
                continue
            if project_id and event.get("project_id") != project_id:
                continue
            matched.append(event)
            if len(matched) >= bounded_limit:
                break

        matched.reverse()
        return matched

    def error_history(
        self,
        *,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Aggregate exact error variants into stable error families."""
        families: dict[str, dict[str, Any]] = {}

        for event in self._events:
            if event.get("level") != "ERROR":
                continue
            if project_id and event.get("project_id") != project_id:
                continue

            fingerprint = event.get("error_fingerprint")
            family_fingerprint = event.get("error_family_fingerprint")
            derived = None
            if not isinstance(fingerprint, str) or not isinstance(
                family_fingerprint, str
            ):
                derived = fingerprint_serialized_event(event)
                if derived is None:
                    continue
                fingerprint = derived.exact
                family_fingerprint = derived.family

            exception = event.get("exception")
            exception_type = (
                exception.get("type")
                if isinstance(exception, dict)
                and isinstance(exception.get("type"), str)
                else (
                    derived.exception_type
                    if derived is not None
                    else "Exception"
                )
            )
            timestamp = str(event.get("timestamp") or "")
            dr_version = str(
                event.get("deploy_relay_version")
                or (
                    exception.get("deploy_relay_version")
                    if isinstance(exception, dict)
                    else ""
                )
                or "unknown"
            )
            ha_version = str(
                event.get("home_assistant_version")
                or (
                    exception.get("home_assistant_version")
                    if isinstance(exception, dict)
                    else ""
                )
                or "unknown"
            )

            family = families.setdefault(
                family_fingerprint,
                {
                    "family_fingerprint": family_fingerprint,
                    "exception_type": exception_type,
                    "occurrences": 0,
                    "first_seen": timestamp,
                    "last_seen": timestamp,
                    "first_deploy_relay_version": dr_version,
                    "last_deploy_relay_version": dr_version,
                    "deploy_relay_versions": set(),
                    "home_assistant_versions": set(),
                    "operations": set(),
                    "phases": set(),
                    "projects": set(),
                    "repositories": set(),
                    "latest_message": "",
                    "latest_run_id": None,
                    "_variants": {},
                },
            )
            family["occurrences"] += 1
            family["deploy_relay_versions"].add(dr_version)
            family["home_assistant_versions"].add(ha_version)
            if event.get("operation"):
                family["operations"].add(str(event["operation"]))
            if event.get("phase"):
                family["phases"].add(str(event["phase"]))
            if event.get("project_id"):
                family["projects"].add(str(event["project_id"]))
            if event.get("repository"):
                family["repositories"].add(str(event["repository"]))

            if timestamp and (
                not family["first_seen"] or timestamp < family["first_seen"]
            ):
                family["first_seen"] = timestamp
                family["first_deploy_relay_version"] = dr_version
            if timestamp and (
                not family["last_seen"] or timestamp >= family["last_seen"]
            ):
                family["last_seen"] = timestamp
                family["last_deploy_relay_version"] = dr_version
                family["latest_message"] = str(event.get("message") or "")
                family["latest_run_id"] = event.get("run_id")

            variants = family["_variants"]
            variant = variants.setdefault(
                fingerprint,
                {
                    "fingerprint": fingerprint,
                    "occurrences": 0,
                    "first_seen": timestamp,
                    "last_seen": timestamp,
                    "first_deploy_relay_version": dr_version,
                    "last_deploy_relay_version": dr_version,
                    "deploy_relay_versions": set(),
                    "home_assistant_versions": set(),
                    "latest_run_id": None,
                    "stack_signature": (
                        exception.get("stack_signature")
                        if isinstance(exception, dict)
                        and isinstance(exception.get("stack_signature"), list)
                        else (
                            list(derived.stack_signature)
                            if derived is not None
                            else []
                        )
                    ),
                },
            )
            variant["occurrences"] += 1
            variant["deploy_relay_versions"].add(dr_version)
            variant["home_assistant_versions"].add(ha_version)
            if timestamp and (
                not variant["first_seen"] or timestamp < variant["first_seen"]
            ):
                variant["first_seen"] = timestamp
                variant["first_deploy_relay_version"] = dr_version
            if timestamp and (
                not variant["last_seen"] or timestamp >= variant["last_seen"]
            ):
                variant["last_seen"] = timestamp
                variant["last_deploy_relay_version"] = dr_version
                variant["latest_run_id"] = event.get("run_id")

        result: list[dict[str, Any]] = []
        for family in families.values():
            variants_out: list[dict[str, Any]] = []
            for variant in family.pop("_variants").values():
                variant["deploy_relay_versions"] = sorted(
                    variant["deploy_relay_versions"]
                )
                variant["home_assistant_versions"] = sorted(
                    variant["home_assistant_versions"]
                )
                variants_out.append(variant)
            variants_out.sort(
                key=lambda item: item.get("last_seen") or "",
                reverse=True,
            )

            family["variant_count"] = len(variants_out)
            family["changed_signature"] = len(variants_out) > 1
            family["variants"] = variants_out
            for key in (
                "deploy_relay_versions",
                "home_assistant_versions",
                "operations",
                "phases",
                "projects",
                "repositories",
            ):
                family[key] = sorted(family[key])
            result.append(family)

        result.sort(
            key=lambda item: item.get("last_seen") or "",
            reverse=True,
        )
        return result

    def stats(
        self,
        *,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Return aggregate ring-buffer statistics without copying the ring."""
        if history is None:
            history = self.error_history()
        return {
            "event_count": len(self._events),
            "debug_count": sum(item.get("level") == "DEBUG" for item in self._events),
            "info_count": sum(item.get("level") == "INFO" for item in self._events),
            "warning_count": sum(item.get("level") == "WARNING" for item in self._events),
            "error_count": sum(item.get("level") == "ERROR" for item in self._events),
            "error_family_count": len(history),
            "error_variant_count": sum(
                item.get("variant_count", 0) for item in history
            ),
            "latest_timestamp": (
                self._events[-1].get("timestamp") if self._events else None
            ),
            "persistence": str(self._log_file),
            "rotation_bytes": _MAX_LOG_BYTES,
            "rotation_files": _ROTATED_FILES,
        }

    def support_bundle(
        self,
        *,
        projects: list[dict[str, Any]],
        deployment_mode: str,
        project_id: str | None = None,
        limit: int = 2000,
    ) -> dict[str, Any]:
        """Build text and JSON support exports from already-redacted data."""
        events = self.query(limit=limit, project_id=project_id)
        filtered_projects = (
            [item for item in projects if item.get("project_id") == project_id]
            if project_id
            else projects
        )
        global_history = self.error_history()
        selected_history = (
            global_history
            if project_id is None
            else self.error_history(project_id=project_id)
        )
        payload = {
            "format": "deploy-relay-support-v1",
            "generated_at": _utc_now(),
            "deploy_relay_version": VERSION,
            "home_assistant_version": HA_VERSION,
            "deployment_mode": deployment_mode,
            "deployment_writes_enabled": False,
            "projects": self._sanitize(filtered_projects),
            "stats": self.stats(history=global_history),
            "error_history": selected_history,
            "events": events,
        }

        lines = [
            "=== DEPLOY RELAY SUPPORT BUNDLE ===",
            f"Generated: {payload['generated_at']}",
            f"Deploy Relay: {VERSION}",
            f"Home Assistant: {HA_VERSION}",
            f"Mode: {deployment_mode}",
            f"Events: {len(events)}",
            "",
            "Projects:",
        ]
        for project in payload["projects"]:
            lines.append(
                "  - "
                f"{project.get('project_name') or project.get('title') or project.get('project_id')}: "
                f"{project.get('repository')} | "
                f"{project.get('selected_source_kind') or '-'}:"
                f"{project.get('selected_source_ref') or '-'} | "
                f"{project.get('selected_source_commit') or '-'}"
            )

        lines.extend(["", "Error history:"])
        for family in payload["error_history"]:
            lines.append(
                "  - "
                f"{family.get('exception_type')} | "
                f"{family.get('family_fingerprint')} | "
                f"{family.get('occurrences')} occurrences | "
                f"{family.get('variant_count')} variants | "
                f"first {family.get('first_seen')} "
                f"(DR {family.get('first_deploy_relay_version')}) | "
                f"last {family.get('last_seen')} "
                f"(DR {family.get('last_deploy_relay_version')})"
            )

        lines.extend(["", "Events:"])
        for event in events:
            run = event.get("run_id") or "-"
            phase = event.get("phase") or "-"
            duration = (
                f" {event['duration_ms']:.3f}ms"
                if isinstance(event.get("duration_ms"), (int, float))
                else ""
            )
            lines.append(
                f"{event.get('timestamp')} {event.get('level'):7} "
                f"[{run}] {event.get('operation') or event.get('component')}/{phase}: "
                f"{event.get('message')}{duration}"
            )
            if event.get("details"):
                lines.append(
                    "    details="
                    + json.dumps(event["details"], ensure_ascii=False, sort_keys=True)
                )
            if event.get("exception"):
                lines.append(
                    "    exception="
                    + json.dumps(event["exception"], ensure_ascii=False, sort_keys=True)
                )

        lines.append("=== END DEPLOY RELAY SUPPORT BUNDLE ===")
        return {
            "text": "\n".join(lines),
            "json": payload,
        }

    async def async_clear(self) -> None:
        """Clear in-memory and persistent diagnostic logs."""
        self._events.clear()

        def _clear_sync() -> None:
            for path in self._paths_oldest_first():
                path.unlink(missing_ok=True)

        async with self._lock:
            await self._hass.async_add_executor_job(_clear_sync)

        await self.async_event(
            "INFO",
            "runtime",
            "Diagnostic log cleared",
            operation="diagnostics",
            phase="clear",
        )
