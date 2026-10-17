"""Contract tests for the inactive Home Assistant ConfigEntry task factory.

Uses a minimal fake ConfigEntry; not a Home Assistant end-to-end test.
"""

import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay")
)

from ha_preview_task_factory import PreviewTaskFactory
from operation_registry import OperationRegistry
from readonly_task_supervisor import ReadOnlyTaskSupervisor


class FakeEntry:
    def __init__(self) -> None:
        self.calls = []
        self.tasks = []

    def async_create_background_task(
        self, hass, target, name, *, eager_start=True
    ):
        self.calls.append((hass, name, eager_start))
        task = asyncio.create_task(target)
        self.tasks.append(task)
        return task

    async def unload(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)


class HomeAssistantPreviewFactoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_factory_registers_with_entry_not_hass(self):
        hass = object()
        entry = FakeEntry()
        factory = PreviewTaskFactory(hass, entry)
        finished = asyncio.Event()

        async def operation() -> None:
            finished.set()

        task = factory(operation())
        await task
        self.assertTrue(finished.is_set())
        self.assertEqual(len(entry.calls), 1)
        self.assertIs(entry.calls[0][0], hass)
        self.assertEqual(
            entry.calls[0][1], "Deploy Relay V2 read-only preview"
        )
        self.assertIs(entry.calls[0][2], False)

    async def test_preview_survives_original_caller_return(self):
        hass = object()
        entry = FakeEntry()
        reg = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(reg, PreviewTaskFactory(hass, entry))
        started = asyncio.Event()
        release = asyncio.Event()

        async def work(_report):
            started.set()
            await release.wait()

        receipt = await owner.start_preview(
            project_key="preview_p1",
            request_id="request-abcdef123456789",
            work=work,
        )
        await started.wait()
        status = await reg.get(receipt["operation_id"])
        self.assertEqual(status["status"], "running")
        release.set()
        for _ in range(100):
            status = await reg.get(receipt["operation_id"])
            if status["status"] == "success":
                break
            await asyncio.sleep(0)
        self.assertEqual(status["status"], "success")
        await owner.close()

    async def test_entry_unload_cancels_pending_preview(self):
        hass = object()
        entry = FakeEntry()
        reg = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(reg, PreviewTaskFactory(hass, entry))
        started = asyncio.Event()

        async def work(_report):
            started.set()
            await asyncio.Event().wait()

        receipt = await owner.start_preview(
            project_key="preview_p2",
            request_id="request-fedcba987654321",
            work=work,
        )
        await started.wait()
        await entry.unload()
        await asyncio.sleep(0)
        result = await reg.get(receipt["operation_id"])
        self.assertEqual(result["status"], "interrupted")
        await owner.close()

    async def test_invalid_entry_is_rejected(self):
        with self.assertRaises(ValueError):
            PreviewTaskFactory(object(), object())
        with self.assertRaises(ValueError):
            PreviewTaskFactory(None, FakeEntry())


if __name__ == "__main__":
    unittest.main()
