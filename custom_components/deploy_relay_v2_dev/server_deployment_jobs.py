"""One HA-owned V2 job executes the *reused* V1 deployment engine.

Preparatory backend integration only: no WebSocket or UI enables mutation.
The authorization boundary belongs to a future admin-only entry point and
cannot be replaced by a browser field. This owner is independent of browsers
and delegates backup, install, verify, and rollback to the V1 engine.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from .operation_model import (
    ErrorFamily, OperationContractError, OperationPhase,
    OperationStatus, OperationType,
)
from .operation_registry import OperationRegistry
from .v1_engine import deployment as engine
from .v1_engine.manifest import DeploymentManifest
from .v1_engine.planner import build_plan, _paths_overlap
from .v1_engine.preview import PreviewResult
from .v1_engine.source_inventory import SourceInventory


class ServerDeploymentJobs:
    """Background owner for future explicitly authorized, HA-bound installs.

    Does not install by being constructed or loaded. Never start it from an
    arbitrary browser object: validated server-created Manifest, Inventory
    and Preview objects are mandatory, along with a separate admin gate.
    """

    def __init__(self, registry: OperationRegistry, task_factory: Callable,
                 *, on_terminal: Callable | None = None) -> None:
        if not isinstance(registry, OperationRegistry) or not callable(task_factory):
            raise OperationContractError("backend task owner is required")
        self._registry = registry
        self._spawn = task_factory
        self._on_terminal = on_terminal
        self._start_lock = asyncio.Lock()
        self._tasks: dict[str, asyncio.Task] = {}
        # The exact original V1 deployment target boundaries, never browser paths.
        self._reserved_targets: dict[str, tuple[str, ...]] = {}
        # Only transactions whose V1 engine actually reported their ID may
        # remain nonterminal during a second, independent project's preflight.
        self._reported_transactions: dict[str, str] = {}
        self._closed = False

    async def start_verified(
        self, *, manifest: DeploymentManifest,
        inventory: SourceInventory, preview: PreviewResult,
        session: Any, config_root: Path, request_id: str,
        token: str | None = None, blocking_executor: Callable | None = None,
    ) -> dict[str, object]:
        """Admit only trusted, fixed-commit V1 engine inputs, no browser payload.

        NOT exposed by the HA integration, and cannot serve as user write
        authorization. The caller will additionally need the authenticated
        admin/confirmation/target-exclusivity checks before it may be wired.
        """
        if (
            type(manifest) is not DeploymentManifest
            or type(inventory) is not SourceInventory
            or type(preview) is not PreviewResult
            or not isinstance(config_root, Path)
            or config_root.is_symlink()
            or token is not None and not isinstance(token, str)
            or inventory.project_id != manifest.project_id
            or preview.project_id != manifest.project_id
            or inventory.repository.casefold() != manifest.repository.casefold()
            or preview.repository.casefold() != manifest.repository.casefold()
            or inventory.source_commit != preview.source_commit
            or inventory.source_ref != preview.source_ref
            or len(inventory.source_commit) != 40
            or any(c not in "0123456789abcdef" for c in inventory.source_commit)
        ):
            raise OperationContractError("source, target or commit not verified")
        # Pre-validate the full deployment plan using the proven V1 contract.
        try:
            plan = build_plan(manifest, source_ref=inventory.source_ref,
                              source_commit=inventory.source_commit)
            targets = tuple(group.target.casefold() for group in plan.groups)
        except (ValueError, TypeError) as exc:
            raise OperationContractError("invalid V1 deployment plan") from None

        async with self._start_lock:
            if self._closed:
                raise OperationContractError("deployment task owner is closed")
            # Reject any parent/child/case-insensitive overlap before the V1
            # engine starts, but allow disjoint projects to run concurrently.
            if any(_paths_overlap(target, held) for target in targets
                   for reserved in self._reserved_targets.values() for held in reserved):
                raise OperationContractError("deployment target already reserved")
            entry = await self._registry.register(
                operation_type=OperationType.INSTALL,
                project_key=manifest.project_id,
                source_commit=inventory.source_commit,
                request_id=request_id,
            )
            identifier = str(entry["operation_id"])
            if identifier in self._tasks or entry["status"] != "queued":
                return entry
            self._reserved_targets[identifier] = targets

            async def run() -> None:
                try:
                    await self._registry.transition(identifier, OperationStatus.RUNNING)
                    phases = {
                        "staging": OperationPhase.STAGING,
                        "backup": OperationPhase.BACKUP,
                        "install": OperationPhase.APPLY,
                        "verify_install": OperationPhase.VERIFY,
                        "rollback": OperationPhase.ROLLBACK,
                    }
                    async def progress(stage: str, details: dict) -> None:
                        transaction_id = details.get("transaction_id")
                        if (type(transaction_id) is str and
                            transaction_id.startswith("dra-") and
                            len(transaction_id) <= 128 and
                            all(ch.isalnum() or ch == "-" for ch in transaction_id)):
                            self._reported_transactions[identifier] = transaction_id
                        phase = phases.get(stage)
                        if phase is not None:
                            await self._registry.progress(identifier, phase=phase,
                                                          current=0, total=1)
                    result = await engine.async_execute_deployment(
                        session, manifest, inventory, preview,
                        token=token, config_root=config_root,
                        progress=progress, blocking_executor=blocking_executor,
                    )
                    # The V1 engine completes its post-write verification and
                    # journal before returning successfully.
                    if result.state != engine.TransactionState.SUCCESS:
                        raise engine.DeploymentError("V1 engine did not finish")
                    await self._registry.post_action(
                        identifier, restart_required=result.restart_required,
                        frontend_reload_possible=(
                            result.lifecycle == "frontend_reload"
                            and not result.restart_required
                        ),
                    )
                    await self._registry.transition(identifier, OperationStatus.SUCCESS)
                except engine.RecoveryRequiredError:
                    await self._registry.transition(identifier,
                        OperationStatus.RECOVERY_REQUIRED,
                        error_family=ErrorFamily.ROLLBACK)
                except asyncio.CancelledError:
                    # No false success. The V1 on-disk transaction journal is
                    # the recovery source, not this in-memory status.
                    try:
                        await self._registry.transition(identifier, OperationStatus.INTERRUPTED)
                    except OperationContractError:
                        pass
                    raise
                except Exception:
                    await self._registry.transition(identifier, OperationStatus.FAILED,
                                                    error_family=ErrorFamily.FILESYSTEM)
                finally:
                    # Release target ownership only after V1 has returned or
                    # exhausted its rollback attempt. No unsafe parallel write.
                    self._reserved_targets.pop(identifier, None)
                    self._reported_transactions.pop(identifier, None)
                    if self._on_terminal is not None:
                        snapshot = await self._registry.get(identifier)
                        if snapshot is not None:
                            try:
                                await self._on_terminal(snapshot)
                            except Exception:
                                pass
            coroutine = run()
            try:
                task = self._spawn(coroutine)
                if not isinstance(task, asyncio.Task):
                    raise TypeError("task owner returned no asyncio Task")
            except Exception:
                coroutine.close()
                self._reserved_targets.pop(identifier, None)
                await self._registry.transition(identifier, OperationStatus.FAILED,
                                                error_family=ErrorFamily.RESOURCE)
                raise OperationContractError("cannot schedule server deployment") from None
            self._tasks[identifier] = task
            task.add_done_callback(lambda finished, key=identifier: self._tasks.pop(key, None))
            return entry

    async def get(self, operation_id: str) -> dict[str, object] | None:
        return await self._registry.get(operation_id)

    async def latest(self) -> dict[str, object] | None:
        records = await self._registry.list(limit=1)
        return records[0] if records else None

    async def active(self) -> bool:
        return bool(await self._registry.list(active_only=True, limit=1))

    async def active_transaction_ids(self) -> frozenset[str]:
        """Only IDs reported by actually running V1 engines are exempted."""
        return frozenset(self._reported_transactions.values())

    async def finish_before_unload(self) -> None:
        """Gracefully drain writes; NEVER cancel an in-progress mutation here."""
        async with self._start_lock:
            self._closed = True
            tasks = tuple(self._tasks.values())
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
