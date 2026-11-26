"""Security regression contracts for unpublished DRA V2 state primitives."""

import asyncio
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay"))
from operation_model import (MAX_WORK_ITEMS, OperationContractError, OperationPhase,
                             OperationRecord, OperationStatus, OperationType)
from operation_registry import OperationRegistry


class ModelHardeningTests(unittest.TestCase):
    def new(self):
        return OperationRecord(operation_type=OperationType.PREVIEW, project_key="opaque1")

    def test_no_forged_constructor_state(self):
        values = {
            "operation_id": "a" * 32, "status": "success",
            "phase": "complete", "created_at": "1980", "started_at": "1980",
            "finished_at": "1980", "current_index": 2, "total_count": 2,
            "phase_percent": 100, "progress_percent": 100,
            "progress_exact": True, "error_family": "unknown",
            "restart_required": True, "frontend_reload_possible": True,
            "completed_items": 5, "failed_items": 1,
        }
        for key, value in values.items():
            with self.subTest(key=key), self.assertRaises(TypeError):
                OperationRecord(operation_type=OperationType.PREVIEW, project_key="opaque1", **{key: value})

    def test_valid_internal_defaults(self):
        op = self.new()
        self.assertEqual(op.status, OperationStatus.QUEUED)
        self.assertEqual(len(op.operation_id), 32)
        self.assertIsNone(op.progress_percent)
        self.assertIn("T", op.created_at)

    def test_wait_then_run_resets_waiting_phase(self):
        op = self.new()
        op.transition(OperationStatus.WAITING_FOR_RESOURCE)
        self.assertEqual(op.phase, OperationPhase.WAITING)
        op.transition(OperationStatus.RUNNING)
        self.assertEqual(op.phase, OperationPhase.PREPARE)

    def test_non_success_cannot_claim_complete(self):
        op = self.new()
        op.transition(OperationStatus.RUNNING)
        for status in (OperationStatus.FAILED, OperationStatus.CANCEL_REQUESTED):
            with self.subTest(status=status), self.assertRaises(OperationContractError):
                op.transition(status, phase=OperationPhase.COMPLETE)
            self.assertEqual(op.status, OperationStatus.RUNNING)

    def test_max_progress_work_items(self):
        op = self.new()
        op.transition(OperationStatus.RUNNING)
        with self.assertRaises(OperationContractError):
            op.update_progress(phase=OperationPhase.INVENTORY, current=1, total=MAX_WORK_ITEMS + 1)
        self.assertIsNone(op.total_count)

    def test_max_completed_items(self):
        op = self.new()
        op.transition(OperationStatus.RUNNING)
        with self.assertRaises(OperationContractError):
            op.update_item_counts(completed=MAX_WORK_ITEMS + 1, failed=0)
        self.assertEqual(op.completed_items, 0)

    def test_phase_complete_is_not_operation_complete(self):
        op = self.new()
        op.transition(OperationStatus.RUNNING)
        op.update_progress(phase=OperationPhase.BACKUP, current=10, total=10)
        self.assertEqual(op.phase_percent, 100)
        self.assertIsNone(op.progress_percent)

    def test_total_100_only_after_success(self):
        op = self.new()
        op.transition(OperationStatus.RUNNING)
        op.update_progress(phase=OperationPhase.VERIFY, current=1, total=1, overall=True)
        self.assertEqual(op.progress_percent, 99)
        op.transition(OperationStatus.SUCCESS)
        self.assertEqual(op.progress_percent, 100)


class RegistryHardeningTests(unittest.IsolatedAsyncioTestCase):
    async def test_idempotency_run_context_matters(self):
        reg = OperationRegistry()
        opts = dict(operation_type=OperationType.PREVIEW, project_key="p1",
                    request_id="request-0123456789")
        first = await reg.register(run_id="run_1", **opts)
        replay = await reg.register(run_id="run_1", **opts)
        self.assertEqual(first["operation_id"], replay["operation_id"])
        with self.assertRaises(OperationContractError):
            await reg.register(run_id="run_2", **opts)
        self.assertEqual(len(await reg.list()), 1)

    async def test_invalid_operation_ids_rejected_everywhere(self):
        reg = OperationRegistry()
        target = await reg.register(operation_type=OperationType.PREVIEW, project_key="p1")
        for bad in (None, [], {}, 1, "invalid", "../token", "a" * 300):
            with self.subTest(kind=str(type(bad))), self.assertRaises(OperationContractError):
                await reg.get(bad)
            with self.assertRaises(OperationContractError):
                await reg.transition(bad, OperationStatus.SUCCESS)
            with self.assertRaises(OperationContractError):
                await reg.request_cancel(bad)
            with self.assertRaises(OperationContractError):
                await reg.progress(bad, phase=OperationPhase.PREVIEW, current=0, total=1)
        self.assertEqual((await reg.get(target["operation_id"]))["status"], "queued")

    async def test_active_only_boolean_only(self):
        reg = OperationRegistry()
        for bad in ("false", 1, None, []):
            with self.subTest(value=str(bad)), self.assertRaises(OperationContractError):
                await reg.list(active_only=bad)

    async def test_terminal_request_replay_uses_same_result(self):
        reg = OperationRegistry()
        opts = dict(operation_type=OperationType.PREVIEW, project_key="p1",
                    request_id="request-9876543210")
        op = await reg.register(**opts)
        await reg.transition(op["operation_id"], OperationStatus.RUNNING)
        await reg.transition(op["operation_id"], OperationStatus.SUCCESS)
        replay = await reg.register(**opts)
        self.assertEqual(replay["operation_id"], op["operation_id"])
        self.assertEqual(replay["status"], "success")

    async def test_concurrent_retries_single_mutation(self):
        reg = OperationRegistry()
        opts = dict(operation_type=OperationType.INSTALL, project_key="p1",
                    request_id="request-2222222222")
        snapshots = await asyncio.gather(*(reg.register(**opts) for _ in range(100)))
        self.assertEqual(len({x["operation_id"] for x in snapshots}), 1)
        self.assertEqual(len(await reg.list()), 1)

    async def test_retention_eviction_clears_replay_mapping(self):
        reg = OperationRegistry(max_completed=1)
        old = await reg.register(operation_type=OperationType.PREVIEW, project_key="p1",
                                 request_id="request-3333333333")
        await reg.transition(old["operation_id"], OperationStatus.RUNNING)
        await reg.transition(old["operation_id"], OperationStatus.SUCCESS)
        other = await reg.register(operation_type=OperationType.PREVIEW, project_key="p2")
        await reg.transition(other["operation_id"], OperationStatus.RUNNING)
        await reg.transition(other["operation_id"], OperationStatus.SUCCESS)
        self.assertIsNone(await reg.get(old["operation_id"]))
        newer = await reg.register(operation_type=OperationType.PREVIEW, project_key="p1",
                                   request_id="request-3333333333")
        self.assertNotEqual(newer["operation_id"], old["operation_id"])

    async def test_snapshots_are_not_mutable_handles(self):
        reg = OperationRegistry()
        op = await reg.register(operation_type=OperationType.PREVIEW, project_key="p1")
        op["status"] = "success"
        current = await reg.get(op["operation_id"])
        self.assertEqual(current["status"], "queued")
        self.assertNotIn("token", json.dumps(current))


if __name__ == "__main__":
    unittest.main()
