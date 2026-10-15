"""V2 backend-only two-step admission to the reused V1 deployment engine.

Source preparation reads Git and local files. A short-lived opaque challenge
binds the exact server-held immutable manifest, inventory and preview to a
second explicit administrator action. No browser-supplied file paths, manifest,
credentials, or commit objects are accepted. All writes remain inside the V1
engine's staging/backup/verify/rollback transaction.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
from secrets import token_hex
from time import monotonic
from typing import Any

from .operation_model import OperationContractError
from .server_deployment_jobs import ServerDeploymentJobs
from .v1_source_bridge import PreparedV1Source, prepare_frozen_v1_source

PREPARATION_LIFETIME_SECONDS = 120

def _require_resolved_v1_transactions(config_root: Path, active_ids: frozenset[str] = frozenset()) -> None:
    """Inspect only V2-owned V1-engine journals, never V1's data folder.

    A reboot during staging/backup/apply cannot be silently followed by a new
    install. The existing V1 transaction journal is authoritative for that
    safety decision; no new transaction persistence format is invented.
    """
    directory = config_root / "deploy_relay_v2_dev" / "transactions"
    if (config_root.is_symlink() or
        (directory.parent.exists() and directory.parent.is_symlink()) or
        directory.is_symlink()):
        raise OperationContractError("unsafe transaction journal location")
    if not directory.exists():
        return
    if not directory.is_dir():
        raise OperationContractError("invalid transaction journal directory")
    entries = sorted(directory.iterdir())
    if len(entries) > 512:
        raise OperationContractError("transaction history exceeds review limit")
    for entry in entries:
        if entry.is_symlink() or not entry.is_file() or entry.suffix != ".json":
            raise OperationContractError("unrecognized transaction journal entry")
        try:
            if entry.stat().st_size > 262144:
                raise ValueError("journal too large")
            raw = entry.read_bytes()
            row = json.loads(raw)
            if type(row) is not dict or row.get("schema") not in (
                None, "deploy-relay.transaction.v1"
            ):
                raise ValueError("invalid journal schema")
            if row.get("state") not in ("success", "failed_no_change", "rolled_back"):
                # The only acceptable nonterminal journal is the exact
                # transaction ID reported by a currently active V1 engine.
                # A stale journal from a terminated HA instance never qualifies.
                if entry.stem not in active_ids or row.get("transaction_id") != entry.stem:
                    raise ValueError("incomplete or uncertain transaction")
        except (OSError, ValueError, UnicodeError):
            raise OperationContractError("old transaction needs recovery review") from None



@dataclass(frozen=True, slots=True)
class PendingInstallation:
    challenge: str
    expires_at: float
    repository: str
    project_id: str
    source_ref: str
    commit: str
    prepared: PreparedV1Source


class DeploymentCoordinator:
    """Short-lived per-project confirmations for independent V1-backed jobs."""

    def __init__(self, jobs: ServerDeploymentJobs) -> None:
        if not isinstance(jobs, ServerDeploymentJobs):
            raise OperationContractError("deployment job owner required")
        self._jobs = jobs
        self._lock = asyncio.Lock()
        self._pending: dict[str, PendingInstallation] = {}
        self._closed = False

    async def prepare(
        self, *, session: Any, repository: str, source_ref: str,
        source_commit: str, expected_project_id: str,
        config_root: Path, token: str | None = None,
    ) -> dict[str, object]:
        """Prepare a new exact-commit V1 comparison, never mutate a target."""
        async with self._lock:
            if self._closed:
                raise OperationContractError("deployment coordinator closed")
            # Refresh only this project's pending confirmation. Different
            # approved projects may prepare while an independent V1 job runs.
            self._pending.pop(expected_project_id, None)
            if await self._jobs.project_active(expected_project_id):
                raise OperationContractError("project already has running installation")
            active_ids = await self._jobs.active_transaction_ids()
            await asyncio.to_thread(_require_resolved_v1_transactions,
                                    config_root, active_ids)
            prepared = await prepare_frozen_v1_source(
                session=session, repository=repository, source_ref=source_ref,
                source_commit=source_commit,
                expected_project_id=expected_project_id,
                config_root=config_root, token=token,
            )
            changed = prepared.preview.add_count + prepared.preview.change_count + prepared.preview.remove_count
            if not changed:
                raise OperationContractError("no project changes to install")
            challenge = token_hex(16)
            self._pending[expected_project_id] = PendingInstallation(
                challenge=challenge, expires_at=monotonic()+PREPARATION_LIFETIME_SECONDS,
                repository=repository, project_id=expected_project_id,
                source_ref=source_ref, commit=source_commit, prepared=prepared,
            )
            return {
                "schema": "dra-v2-install-preparation.v1",
                "challenge": challenge,
                "repository": repository,
                "source_ref": source_ref,
                "source_commit": source_commit,
                "project_id": expected_project_id,
                "add": prepared.preview.add_count,
                "change": prepared.preview.change_count,
                "remove": prepared.preview.remove_count,
                "unchanged": prepared.preview.unchanged_count,
                "confirmation_required": True,
                "expires_in_seconds": PREPARATION_LIFETIME_SECONDS,
                "installation_started": False,
            }

    async def pending_status(self, project_id: str) -> dict[str, object] | None:
        """Read HA-owned prepared transaction from any administrator session.

        The challenge remains server-owned, single-use, and time-limited.
        Returned metadata is never authorization without an explicit confirm.
        """
        async with self._lock:
            candidate = self._pending.get(project_id)
            if candidate is None:
                return None
            remaining = candidate.expires_at - monotonic()
            if self._closed or remaining <= 0:
                self._pending.pop(project_id, None)
                return None
            preview = candidate.prepared.preview
            return {
                "schema": "dra-v2-install-preparation.v1",
                "challenge": candidate.challenge,
                "repository": candidate.repository,
                "source_ref": candidate.source_ref,
                "source_commit": candidate.commit,
                "project_id": candidate.project_id,
                "add": preview.add_count,
                "change": preview.change_count,
                "remove": preview.remove_count,
                "unchanged": preview.unchanged_count,
                "confirmation_required": True,
                "expires_in_seconds": int(remaining),
                "installation_started": False,
            }

    async def confirm(
        self, *, challenge: str, repository: str, commit: str,
        confirm: bool, session: Any, config_root: Path,
        token: str | None = None,
        blocking_executor: Any = None,
    ) -> dict[str, object]:
        """Consume one backend-held challenge; never accept serialized plans."""
        async with self._lock:
            candidate = next((item for item in self._pending.values()
                              if item.challenge == challenge), None)
            if self._closed or confirm is not True or (
                type(challenge) is not str or len(challenge) != 32 or
                type(repository) is not str or type(commit) is not str or
                candidate is None or candidate.expires_at < monotonic() or
                candidate.repository.casefold() != repository.casefold() or
                candidate.commit != commit
            ):
                # Invalid confirmation must never invalidate other prepared
                # projects' independent tokens.
                if candidate is not None:
                    self._pending.pop(candidate.project_id, None)
                raise OperationContractError("installation confirmation invalid or expired")
            self._pending.pop(candidate.project_id, None)
            obj = candidate.prepared
            # The confirmed git SHA is immutable; V1 verifies the target
            # hashes again before backup and immediately before each write.
            return await self._jobs.start_verified(
                manifest=obj.manifest, inventory=obj.inventory,
                preview=obj.preview, session=session,
                config_root=config_root, request_id=challenge,
                token=token, blocking_executor=blocking_executor,
            )

    async def get(self, operation_id: str) -> dict[str, object] | None:
        return await self._jobs.get(operation_id)

    async def latest(self) -> dict[str, object] | None:
        return await self._jobs.latest()

    async def list(self) -> list[dict[str, object]]:
        return await self._jobs.list()

    async def close(self) -> None:
        async with self._lock:
            self._closed = True
            self._pending.clear()
        await self._jobs.finish_before_unload()
