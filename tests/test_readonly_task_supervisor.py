"""Contract tests for the isolated read-only task owner."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay"))
from operation_model import OperationPhase
from operation_registry import OperationRegistry
from readonly_task_supervisor import ReadOnlyTaskSupervisor


class PreviewTaskOwnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_remains_visible_after_request(self):
        registry = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(registry, asyncio.create_task)
        started = asyncio.Event()
        finish = asyncio.Event()

        async def job(progress):
            started.set()
            await finish.wait()
            await progress(OperationPhase.INVENTORY, 1, 1)

        receipt = await owner.start_preview(project_key="project1",
                                            request_id="request-abcdefghijklmnop", work=job)
        await started.wait()
        self.assertEqual((await registry.get(receipt["operation_id"]))["status"], "running")
        finish.set()
        for _ in range(100):
            result = await registry.get(receipt["operation_id"])
            if result["status"] == "success":
                break
            await asyncio.sleep(0)
        self.assertEqual(result["status"], "success")
        await owner.close()

    async def test_idempotent_concurrent_start(self):
        registry = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(registry, asyncio.create_task)
        finish = asyncio.Event()
        count = 0

        async def job(_progress):
            nonlocal count
            count += 1
            await finish.wait()

        async def request():
            return await owner.start_preview(project_key="p1",
                request_id="request-bcdefghijklmnopq", work=job)

        results = await asyncio.gather(*(request() for _ in range(30)))
        self.assertEqual(len({r["operation_id"] for r in results}), 1)
        await asyncio.sleep(0)
        self.assertEqual(count, 1)
        finish.set()
        await owner.close()

    async def test_shutdown_marks_readonly_interrupted(self):
        registry = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(registry, asyncio.create_task)
        started = asyncio.Event()

        async def job(_progress):
            started.set()
            await asyncio.Event().wait()

        receipt = await owner.start_preview(project_key="p1",
            request_id="request-cdefghijklmnopqr", work=job)
        await started.wait()
        await owner.close()
        result = await registry.get(receipt["operation_id"])
        self.assertEqual(result["status"], "interrupted")


if __name__ == "__main__":
    unittest.main()
