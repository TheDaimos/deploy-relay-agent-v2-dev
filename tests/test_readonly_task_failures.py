"""Failure-mode contracts for the isolated read-only preview owner."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay"))
from operation_model import OperationContractError
from operation_registry import OperationRegistry
from readonly_task_supervisor import ReadOnlyTaskSupervisor


class PreviewTaskFailures(unittest.IsolatedAsyncioTestCase):
    async def test_failure_is_generic_and_terminal(self):
        reg = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(reg, asyncio.create_task)

        async def job(_progress):
            raise RuntimeError("synthetic-worker-failure")

        receipt = await owner.start_preview(project_key="p1",
            request_id="request-defghijklmnopqrs", work=job)
        for _ in range(100):
            state = await reg.get(receipt["operation_id"])
            if state["status"] == "failed":
                break
            await asyncio.sleep(0)
        self.assertEqual(state["status"], "failed")
        self.assertNotIn("synthetic-worker-failure", str(state))
        await owner.close()

    async def test_invalid_task_factory_is_fail_closed(self):
        reg = OperationRegistry()

        def broken(_coro):
            raise RuntimeError("synthetic-factory-failure")

        owner = ReadOnlyTaskSupervisor(reg, broken)
        async def job(_progress):
            return None

        with self.assertRaises(OperationContractError):
            await owner.start_preview(project_key="p1",
                request_id="request-efghijklmnopqrst", work=job)
        self.assertEqual((await reg.list())[0]["status"], "failed")
        await owner.close()

    async def test_immediate_close_never_leaves_queued(self):
        reg = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(reg, asyncio.create_task)

        async def job(_progress):
            return None

        receipt = await owner.start_preview(project_key="p1",
            request_id="request-fghijklmnopqrstu", work=job)
        await owner.close()
        self.assertEqual((await reg.get(receipt["operation_id"]))["status"], "interrupted")

    async def test_completed_retries_do_not_restart(self):
        reg = OperationRegistry()
        owner = ReadOnlyTaskSupervisor(reg, asyncio.create_task)
        count = 0

        async def job(_progress):
            nonlocal count
            count += 1

        args = dict(project_key="p1",
            request_id="request-ghijklmnopqrstuv", work=job)
        receipt = await owner.start_preview(**args)
        for _ in range(100):
            state = await reg.get(receipt["operation_id"])
            if state["status"] == "success":
                break
            await asyncio.sleep(0)
        replay = await owner.start_preview(**args)
        self.assertEqual(receipt["operation_id"], replay["operation_id"])
        self.assertEqual(count, 1)
        await owner.close()


if __name__ == "__main__":
    unittest.main()
