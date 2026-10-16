"""HA-owned bounded sequential batch of frozen V1 deployment plans.

A browser can only request an explicitly confirmed batch. All individual
transactions continue to use ServerDeploymentJobs and its V1 rollback/journal.
There is deliberately no all-project rollback after a prior project succeeded.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from secrets import token_hex
from time import monotonic
from typing import Any, Callable

from .deployment_coordinator import _require_resolved_v1_transactions
from .operation_model import OperationContractError
from .server_deployment_jobs import ServerDeploymentJobs
from .v1_source_bridge import PreparedV1Source, prepare_frozen_v1_source
from .v1_engine.planner import build_plan, _paths_overlap

MAX_BATCH_PROJECTS = 8
LIFETIME_SECONDS = 900


@dataclass(frozen=True)
class BatchPlanItem:
    repository: str
    project_id: str
    commit: str
    source_ref: str
    prepared: PreparedV1Source


class BatchDeployment:
    def __init__(self, jobs: ServerDeploymentJobs, task_factory: Callable) -> None:
        if not isinstance(jobs, ServerDeploymentJobs) or not callable(task_factory):
            raise OperationContractError("HA batch task owner required")
        self._jobs = jobs
        self._spawn = task_factory
        self._lock = asyncio.Lock()
        self._pending: tuple[BatchPlanItem, ...] = ()
        self._challenge: str | None = None
        self._expires_at = 0.0
        self._controller: str | None = None
        self._controller_expiry = 0.0
        self._state: dict[str, Any] | None = None
        self._task: asyncio.Task | None = None
        self._closed = False

    @staticmethod
    def _client(value: str) -> None:
        if type(value) is not str or len(value) != 32 or any(ch not in "0123456789abcdef" for ch in value):
            raise OperationContractError("invalid batch controller")

    def _snapshot(self) -> dict[str, Any]:
        if self._state is None:
            return {"schema": "dra-v2-batch-status.v1", "status": "idle", "items": []}
        # Never return V1 objects, tokens or mutable state to a browser.
        return {**self._state, "items": [dict(item) for item in self._state["items"]]}

    async def status(self) -> dict[str, Any]:
        async with self._lock:
            return self._snapshot()

    async def prepare(self, specs: list[dict[str, str]], *, session: Any,
                      config_root: Path, client_id: str) -> dict[str, Any]:
        """Verify every requested exact SHA and local target, without writing."""
        self._client(client_id)
        if (type(specs) is not list or not 1 <= len(specs) <= MAX_BATCH_PROJECTS or
            not isinstance(config_root, Path) or config_root.is_symlink()):
            raise OperationContractError("invalid batch selection")
        async with self._lock:
            if self._closed or (self._task and not self._task.done()):
                raise OperationContractError("batch already running or closed")
            self._pending = ()
            self._challenge = None
            active_ids = await self._jobs.active_transaction_ids()
            await asyncio.to_thread(_require_resolved_v1_transactions, config_root, active_ids)
            plans: list[BatchPlanItem] = []
            display: list[dict[str, Any]] = []
            targets: list[str] = []
            seen: set[str] = set()
            for item in specs:
                if (type(item) is not dict or
                    set(item) != {"repository", "project_id", "ref", "commit", "token"} or
                    type(item["repository"]) is not str or
                    item["repository"].casefold() in seen or
                    item["project_id"] in {"deploy_relay", "deploy_relay_v2_dev",
                                           "deploy_relay_agent_v2_dev"}):
                    raise OperationContractError("invalid batch project")
                seen.add(item["repository"].casefold())
                if await self._jobs.project_active(item["project_id"]):
                    raise OperationContractError("project installation already active")
                frozen = await prepare_frozen_v1_source(
                    session=session, repository=item["repository"],
                    source_ref=item["ref"], source_commit=item["commit"],
                    expected_project_id=item["project_id"],
                    config_root=config_root, token=item["token"],
                )
                changed = (frozen.preview.add_count + frozen.preview.change_count +
                           frozen.preview.remove_count)
                if changed:
                    plan = build_plan(frozen.manifest, source_ref=item["ref"],
                                      source_commit=item["commit"])
                    group_targets = [g.target.casefold() for g in plan.groups]
                    if any(_paths_overlap(a, b) for a in group_targets for b in targets):
                        raise OperationContractError("batch target overlap")
                    targets.extend(group_targets)
                    plans.append(BatchPlanItem(item["repository"], item["project_id"],
                                               item["commit"], item["ref"], frozen))
                display.append({
                    "repository": item["repository"], "project_key": item["project_id"],
                    "source_ref": item["ref"], "source_commit": item["commit"],
                    "add": frozen.preview.add_count, "change": frozen.preview.change_count,
                    "remove": frozen.preview.remove_count,
                    "unchanged": frozen.preview.unchanged_count,
                    "status": "prepared" if changed else "up_to_date",
                    "operation_id": None,
                })
            self._state = {"schema": "dra-v2-batch-status.v1",
                           "status": "prepared" if plans else "up_to_date",
                           "batch_id": None, "items": display,
                           "current": 0, "total": len(plans),
                           "confirmation_required": bool(plans)}
            if not plans:
                return {"schema": "dra-v2-batch-preparation.v1",
                        "preparation": self._snapshot(), "challenge": None}
            self._pending = tuple(plans)
            self._challenge = token_hex(16)
            self._expires_at = monotonic() + LIFETIME_SECONDS
            self._controller = client_id
            self._controller_expiry = self._expires_at
            return {"schema": "dra-v2-batch-preparation.v1",
                    "preparation": self._snapshot(), "challenge": self._challenge,
                    "expires_in_seconds": LIFETIME_SECONDS}

    async def take_over(self, client_id: str, *, confirm: bool) -> dict[str, Any]:
        self._client(client_id)
        if confirm is not True:
            raise OperationContractError("explicit batch control required")
        async with self._lock:
            if self._closed or self._challenge is None or monotonic() >= self._expires_at:
                raise OperationContractError("batch preparation expired")
            self._controller = client_id
            self._controller_expiry = self._expires_at
            return {"schema": "dra-v2-batch-preparation.v1",
                    "preparation": self._snapshot(), "challenge": self._challenge,
                    "expires_in_seconds": int(self._expires_at - monotonic())}

    async def start(self, *, challenge: str, client_id: str, confirm: bool,
                    session: Any, config_root: Path,
                    token_for_repository: Callable[[str], str | None],
                    blocking_executor: Any) -> dict[str, Any]:
        self._client(client_id)
        async with self._lock:
            if (self._closed or confirm is not True or
                type(challenge) is not str or
                challenge != self._challenge or
                self._controller != client_id or
                monotonic() >= self._expires_at or
                self._task is not None and not self._task.done() or
                not self._pending):
                raise OperationContractError("batch confirmation invalid or consumed")
            plans = self._pending
            self._pending = ()
            self._challenge = None
            self._controller = None
            self._state["batch_id"] = token_hex(16)
            self._state["status"] = "queued"
            self._state["confirmation_required"] = False
            batch_id = self._state["batch_id"]

            async def run() -> None:
                try:
                    self._state["status"] = "running"
                    for index, plan in enumerate(plans):
                        row = next(item for item in self._state["items"]
                                   if item["project_key"] == plan.project_id)
                        row["status"] = "admitting"
                        try:
                            receipt = await self._jobs.start_verified(
                                manifest=plan.prepared.manifest,
                                inventory=plan.prepared.inventory,
                                preview=plan.prepared.preview,
                                session=session, config_root=config_root,
                                request_id=token_hex(16),
                                token=token_for_repository(plan.repository),
                                blocking_executor=blocking_executor,
                            )
                            row["operation_id"] = receipt["operation_id"]
                            row["status"] = "running"
                            terminal = await self._jobs.wait_completion(receipt["operation_id"])
                            row["status"] = terminal["status"]
                            self._state["current"] = index + 1
                            if terminal["status"] != "success":
                                self._state["status"] = "stopped"
                                return
                        except Exception:
                            row["status"] = "admission_failed"
                            self._state["status"] = "stopped"
                            return
                    self._state["status"] = "success"
                except asyncio.CancelledError:
                    self._state["status"] = "interrupted"
                    raise

            coroutine = run()
            try:
                task = self._spawn(coroutine)
                if not isinstance(task, asyncio.Task):
                    raise OperationContractError("batch task owner unavailable")
            except Exception:
                coroutine.close()
                self._state["status"] = "admission_failed"
                raise OperationContractError("batch task could not start") from None
            self._task = task
            return {"schema": "dra-v2-batch-start.v1", "batch_id": batch_id,
                    "status": "queued"}

    async def close(self) -> None:
        async with self._lock:
            self._closed = True
            self._pending = ()
            self._challenge = None
            task = self._task
        if task is not None:
            await asyncio.gather(task, return_exceptions=True)
