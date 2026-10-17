"""V2-40 lifecycle: durable acceptance before start; no replay after restart."""
from __future__ import annotations

import asyncio
import copy
import importlib
import sys
import types
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_40_lifecycle_isolated"
package = types.ModuleType(PKG)
package.__path__ = [str(LAB)]
sys.modules[PKG] = package
model = importlib.import_module(f"{PKG}.operation_model")
registry_mod = importlib.import_module(f"{PKG}.operation_registry")
owner_mod = importlib.import_module(f"{PKG}.readonly_task_supervisor")
journal_mod = importlib.import_module(f"{PKG}.operation_journal")


class FakeStore:
    def __init__(self, document=None):
        self.document = copy.deepcopy(document)
        self.fail = False
        self.writes = 0

    async def async_load(self):
        return copy.deepcopy(self.document)

    async def async_save(self, data):
        if self.fail:
            raise OSError("SECRET DO NOT REPEAT")
        self.document = copy.deepcopy(data)
        self.writes += 1


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = FakeStore()
        self.journal = journal_mod.OperationJournal(self.store)
        await self.journal.load()
        self.registry = registry_mod.OperationRegistry(max_completed=12, max_readonly=1)
        self.owner = owner_mod.ReadOnlyTaskSupervisor(
            self.registry, asyncio.create_task,
            on_registered=self.journal.capture,
            on_terminal=self.journal.capture,
        )

    async def asyncTearDown(self):
        await self.owner.close()

    async def test_queue_durable_before_task_invocation(self):
        observed = []
        finished = asyncio.Event()

        async def work(progress):
            observed.append(self.store.document["records"][0]["status"])
            await progress(model.OperationPhase.INVENTORY, 1, 1)
            finished.set()

        receipt = await self.owner.start_preview(
            project_key="lab_readonly_preview",
            request_id="request-abcdefghijklmnnn", work=work,
        )
        await finished.wait()
        for _ in range(100):
            state = await self.journal.get(receipt["operation_id"])
            if state and state["status"] == "success":
                break
            await asyncio.sleep(0)
        self.assertEqual(observed, ["queued"])
        self.assertEqual(state["status"], "success")
        self.assertEqual(self.store.writes, 2)
        recovered = journal_mod.OperationJournal(self.store)
        await recovered.load()
        self.assertEqual((await recovered.get(receipt["operation_id"]))["status"], "success")

    async def test_write_failure_blocks_any_work(self):
        called = False

        async def work(_progress):
            nonlocal called
            called = True

        self.store.fail = True
        with self.assertRaises(model.OperationContractError):
            await self.owner.start_preview(
                project_key="lab_readonly_preview",
                request_id="request-zbcdefghijklmnop", work=work,
            )
        await asyncio.sleep(0)
        self.assertFalse(called)
        self.assertIsNone(self.store.document)

    async def test_unload_persists_interruption_without_resume(self):
        started = asyncio.Event()

        async def work(_progress):
            started.set()
            await asyncio.Event().wait()

        receipt = await self.owner.start_preview(
            project_key="lab_readonly_preview",
            request_id="request-qbcdefghijklmnop", work=work,
        )
        await started.wait()
        await self.owner.close()
        persisted = await self.journal.get(receipt["operation_id"])
        self.assertEqual(persisted["status"], "interrupted")
        next_journal = journal_mod.OperationJournal(self.store)
        await next_journal.load()
        self.assertEqual((await next_journal.get(receipt["operation_id"]))["status"],
                         "interrupted")
        self.assertEqual(len(self.store.document["records"]), 1)

    async def test_task_factory_failure_is_persisted(self):
        def failed_factory(coroutine):
            raise RuntimeError("SECRET TASK FACTORY")

        self.owner = owner_mod.ReadOnlyTaskSupervisor(
            self.registry, failed_factory,
            on_registered=self.journal.capture,
            on_terminal=self.journal.capture,
        )

        async def work(_progress):
            raise AssertionError("must never run")

        with self.assertRaises(model.OperationContractError):
            await self.owner.start_preview(
                project_key="lab_readonly_preview",
                request_id="request-rbcdefghijklmnop", work=work,
            )
        self.assertEqual(self.store.document["records"][0]["status"], "failed")
        self.assertEqual(self.store.document["records"][0]["error_family"], "resource")

    async def test_restart_history_never_spawns_a_task(self):
        descriptor = await self.registry.register(
            operation_type=model.OperationType.PREVIEW,
            project_key="lab_readonly_preview",
        )
        await self.journal.capture(descriptor)
        reloaded = journal_mod.OperationJournal(self.store)
        await reloaded.load()
        self.assertEqual((await reloaded.get(descriptor["operation_id"]))["status"],
                         "interrupted")
        # Neither journal.load nor get accepts a callback or owns a task.
        self.assertEqual(self.owner._tasks, {})


if __name__ == "__main__":
    unittest.main()
