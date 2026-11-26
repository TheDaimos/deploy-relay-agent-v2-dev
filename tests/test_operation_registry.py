"""V2-30 isolated registry tests. No tasks, Home Assistant or real I/O."""
import asyncio
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'custom_components' / 'deploy_relay'))
from operation_model import OperationContractError, OperationPhase, OperationStatus, OperationType
from operation_registry import OperationRegistry


class RegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_register_list_get(self):
        store = OperationRegistry()
        op = await store.register(operation_type=OperationType.PREVIEW, project_key='pr_1')
        self.assertEqual(len(await store.list()), 1)
        self.assertEqual((await store.get(op['operation_id']))['status'], 'queued')
        self.assertEqual((await store.list(active_only=True))[0]['operation_id'], op['operation_id'])

    async def test_idempotent_repeat_uses_existing_operation(self):
        store = OperationRegistry()
        key = 'req-unique-00000001'
        opts = dict(operation_type=OperationType.PREVIEW, project_key='p1', request_id=key)
        first = await store.register(**opts)
        second = await store.register(**opts)
        self.assertEqual(first['operation_id'], second['operation_id'])
        self.assertEqual(len(await store.list()), 1)

    async def test_duplicate_key_for_different_project_is_rejected(self):
        store = OperationRegistry()
        await store.register(operation_type=OperationType.PREVIEW, project_key='p1', request_id='req-unique-00000002')
        with self.assertRaises(OperationContractError):
            await store.register(operation_type=OperationType.PREVIEW, project_key='p2', request_id='req-unique-00000002')

    async def test_second_mutation_blocked_until_terminal(self):
        store = OperationRegistry()
        first = await store.register(operation_type=OperationType.INSTALL, project_key='p1')
        with self.assertRaises(OperationContractError):
            await store.register(operation_type=OperationType.RESTORE, project_key='p2')
        await store.transition(first['operation_id'], OperationStatus.RUNNING)
        await store.transition(first['operation_id'], OperationStatus.SUCCESS)
        second = await store.register(operation_type=OperationType.RESTORE, project_key='p2')
        self.assertNotEqual(first['operation_id'], second['operation_id'])

    async def test_readonly_capacity_limit(self):
        store = OperationRegistry(max_readonly=2)
        await store.register(operation_type=OperationType.PREVIEW, project_key='p1')
        await store.register(operation_type=OperationType.SOURCE_CHECK, project_key='p2')
        with self.assertRaises(OperationContractError):
            await store.register(operation_type=OperationType.PREVIEW, project_key='p3')

    async def test_queued_cancellation_immediately_terminal(self):
        store = OperationRegistry()
        op = await store.register(operation_type=OperationType.INSTALL, project_key='p1')
        result = await store.request_cancel(op['operation_id'])
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(len(await store.list(active_only=True)), 0)

    async def test_active_cancellation_never_cancels_the_task(self):
        store = OperationRegistry()
        op = await store.register(operation_type=OperationType.INSTALL, project_key='p1')
        await store.transition(op['operation_id'], OperationStatus.RUNNING)
        requested = await store.request_cancel(op['operation_id'])
        self.assertEqual(requested['status'], 'cancel_requested')
        result = await store.transition(op['operation_id'], OperationStatus.SUCCESS)
        self.assertEqual(result['status'], 'success')

    async def test_bounded_terminal_retention(self):
        store = OperationRegistry(max_completed=2)
        ids = []
        for n in range(4):
            op = await store.register(operation_type=OperationType.PREVIEW, project_key=f'p{n}')
            ids.append(op['operation_id'])
            await store.transition(op['operation_id'], OperationStatus.RUNNING)
            await store.transition(op['operation_id'], OperationStatus.SUCCESS)
        self.assertEqual(len(await store.list()), 2)
        self.assertIsNone(await store.get(ids[0]))
        self.assertIsNone(await store.get(ids[1]))
        self.assertIsNotNone(await store.get(ids[3]))

    async def test_idempotency_mapping_evicted_with_old_result(self):
        store = OperationRegistry(max_completed=1)
        req='req-unique-00000003'
        first = await store.register(operation_type=OperationType.PREVIEW, project_key='p1', request_id=req)
        await store.transition(first['operation_id'], OperationStatus.RUNNING)
        await store.transition(first['operation_id'], OperationStatus.SUCCESS)
        second = await store.register(operation_type=OperationType.PREVIEW, project_key='p2')
        await store.transition(second['operation_id'], OperationStatus.RUNNING)
        await store.transition(second['operation_id'], OperationStatus.SUCCESS)
        third = await store.register(operation_type=OperationType.PREVIEW, project_key='p1', request_id=req)
        self.assertNotEqual(first['operation_id'], third['operation_id'])

    async def test_progress_is_safe_snapshot(self):
        store = OperationRegistry()
        op = await store.register(operation_type=OperationType.PREVIEW, project_key='p1')
        await store.transition(op['operation_id'], OperationStatus.RUNNING)
        updated = await store.progress(op['operation_id'], phase=OperationPhase.INVENTORY, current=10, total=10)
        self.assertEqual(updated['phase_percent'], 100)
        self.assertIsNone(updated['progress_percent'])
        self.assertNotIn('token', json.dumps(updated))

    async def test_snapshot_copy_cannot_modify_store(self):
        store = OperationRegistry()
        op = await store.register(operation_type=OperationType.PREVIEW, project_key='p1')
        op['status'] = 'success'
        self.assertEqual((await store.get(op['operation_id']))['status'], 'queued')

    async def test_bad_request_id_is_rejected(self):
        store=OperationRegistry()
        for request in ('x', '../a', 'secret with space', 'a'*129):
            with self.subTest(key=request), self.assertRaises(OperationContractError):
                await store.register(operation_type=OperationType.PREVIEW,project_key='p1',request_id=request)

    async def test_concurrent_mutating_admission_is_serialized(self):
        store=OperationRegistry()
        async def attempt(i):
            try:
                return await store.register(operation_type=OperationType.INSTALL,project_key=f'p{i}')
            except OperationContractError:
                return None
        got=await asyncio.gather(*(attempt(i) for i in range(16)))
        self.assertEqual(sum(x is not None for x in got),1)

    async def test_mutable_operations_are_not_active_task_objects(self):
        store=OperationRegistry()
        op=await store.register(operation_type=OperationType.INSTALL, project_key='p1')
        self.assertEqual(op['status'], 'queued')
        self.assertFalse(hasattr(store,'start_task'))
        self.assertFalse(hasattr(store,'install'))


if __name__ == '__main__':
    unittest.main()
