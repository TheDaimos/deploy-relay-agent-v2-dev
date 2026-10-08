"""V2-40: fail-closed persistence and restart recognition, no HA needed."""
from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "custom_components" / "deploy_relay_v2_dev" / "operation_journal.py"
spec = importlib.util.spec_from_file_location("v2_dev_operation_journal", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Journal = module.OperationJournal
JournalError = module.JournalError
TIME = "2026-10-08T15:00:00.000+00:00"


def record(index=1, status="queued"):
    finished = status in module.TERMINAL
    running = status in ("running", "success", "failed")
    return {
        "schema": "dra-operation-v2.v1", "operation_id": f"{index:032x}",
        "operation_type": "preview", "project_key": "lab_readonly_preview",
        "source_commit": None, "run_id": None, "status": status,
        "phase": "complete" if status == "success" else (
            "inventory" if running else "prepare"),
        "created_at": TIME, "started_at": TIME if running else None,
        "finished_at": TIME if finished else None,
        "current_index": 20 if status == "success" else None,
        "total_count": 20 if status == "success" else None,
        "phase_percent": 100 if status == "success" else None,
        "progress_percent": 100 if status == "success" else None,
        "progress_exact": status == "success",
        "error_family": None, "restart_required": False,
        "frontend_reload_possible": False, "recovery_required": False,
        "completed_items": 0, "failed_items": 0,
    }


class FakeStore:
    def __init__(self, data=None):
        self.data = copy.deepcopy(data)
        self.writes = 0
        self.fail_read = False
        self.fail_write = False

    async def async_load(self):
        if self.fail_read:
            raise RuntimeError("DO NOT LOG MY PRIVATE STORAGE")
        return copy.deepcopy(self.data)

    async def async_save(self, document):
        if self.fail_write:
            raise RuntimeError("DO NOT LOG MY PRIVATE PATH")
        self.data = copy.deepcopy(document)
        self.writes += 1


class JournalTests(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_and_terminal_survive_new_instance(self):
        store = FakeStore()
        first = Journal(store)
        await first.load()
        self.assertEqual(store.writes, 0)
        await first.capture(record(1, "queued"))
        await first.capture(record(1, "success"))
        second = Journal(store)
        await second.load()
        result = await second.get(f"{1:032x}")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["progress_percent"], 100)
        self.assertEqual(store.writes, 2)
        self.assertEqual(len(store.data["events"]), 2)

    async def test_running_and_queued_become_interrupted_once(self):
        store = FakeStore()
        first = Journal(store)
        await first.load()
        await first.capture(record(1, "running"))
        await first.capture(record(2, "queued"))
        recovered = Journal(store)
        await recovered.load()
        self.assertEqual((await recovered.get(f"{1:032x}"))["status"], "interrupted")
        self.assertEqual((await recovered.get(f"{2:032x}"))["status"], "interrupted")
        self.assertTrue((await recovered.get(f"{1:032x}"))["finished_at"])
        self.assertFalse((await recovered.get(f"{1:032x}"))["progress_exact"])
        count = store.writes
        next_start = Journal(store)
        await next_start.load()
        self.assertEqual(count, store.writes)

    async def test_cancel_requested_is_interrupted(self):
        store = FakeStore()
        job = record(1, "cancel_requested")
        await Journal(store).load()  # document not yet written
        store.data = {"schema": module.SCHEMA, "records": [job], "events": []}
        restarted = Journal(store)
        await restarted.load()
        self.assertEqual((await restarted.get(job["operation_id"]))["status"], "interrupted")

    async def test_strict_invalid_documents_do_not_overwrite(self):
        valid = {"schema": module.SCHEMA, "records": [record()], "events": []}
        variants = []
        bad = copy.deepcopy(valid); bad["schema"] = "unexpected.v4"; variants.append(bad)
        bad = copy.deepcopy(valid); bad["admin"] = True; variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["token"] = "PRIVATE"; variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["project_key"] = "PRIVATE"; variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["operation_type"] = "install"; variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["status"] = "success"; variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"].append(record()); variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["created_at"] = "not-a-time"; variants.append(bad)
        bad = copy.deepcopy(valid); bad["events"].append({"operation_id": "f"*32, "status": "success", "at": TIME}); variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["current_index"] = True; variants.append(bad)
        bad = copy.deepcopy(valid); bad["records"][0]["restart_required"] = True; variants.append(bad)
        for item in variants:
            with self.subTest(item=str(item)[:70]):
                store = FakeStore(item)
                with self.assertRaises(JournalError):
                    await Journal(store).load()
                self.assertEqual(store.writes, 0)
                self.assertEqual(store.data, item)

    async def test_not_logging_sensitive_store_errors(self):
        store = FakeStore()
        store.fail_read = True
        with self.assertRaises(JournalError) as caught:
            await Journal(store).load()
        self.assertNotIn("PRIVATE", str(caught.exception))
        store.fail_read = False
        journal = Journal(store)
        await journal.load()
        store.fail_write = True
        with self.assertRaises(JournalError) as caught:
            await journal.capture(record())
        self.assertNotIn("PRIVATE", str(caught.exception))
        self.assertEqual(await journal.list(), [])

    async def test_recovery_write_failure_is_closed(self):
        store = FakeStore({"schema": module.SCHEMA, "records": [record()], "events": []})
        store.fail_write = True
        journal = Journal(store)
        with self.assertRaises(JournalError):
            await journal.load()
        with self.assertRaises(JournalError):
            await journal.capture(record(2))
        self.assertEqual(store.data["records"][0]["status"], "queued")

    async def test_terminal_record_is_immutable(self):
        journal = Journal(FakeStore())
        await journal.load()
        await journal.capture(record(1, "success"))
        with self.assertRaises(JournalError):
            await journal.capture(record(1, "failed"))
        self.assertEqual((await journal.get(f"{1:032x}"))["status"], "success")

    async def test_retention_and_journal_have_hard_caps(self):
        store = FakeStore()
        journal = Journal(store)
        await journal.load()
        for i in range(1, 22):
            await journal.capture(record(i, "success"))
        self.assertEqual(len(await journal.list()), 12)
        self.assertEqual(len(store.data["records"]), 12)
        self.assertLessEqual(len(store.data["events"]), 48)
        self.assertIsNone(await journal.get(f"{1:032x}"))
        self.assertEqual(len({s["operation_id"] for s in await journal.list()}), 12)

    async def test_defensive_snapshot_copy(self):
        journal = Journal(FakeStore())
        await journal.load()
        external = record()
        await journal.capture(external)
        external["status"] = "failed"
        first = await journal.get(external["operation_id"])
        first["project_key"] = "injected"
        second = await journal.get(external["operation_id"])
        self.assertEqual(second["status"], "queued")
        self.assertEqual(second["project_key"], "lab_readonly_preview")

    async def test_parallel_capture_serializes_writes(self):
        store = FakeStore()
        journal = Journal(store)
        await journal.load()
        await asyncio.gather(*(journal.capture(record(i)) for i in range(1, 10)))
        self.assertEqual(len(await journal.list()), 9)
        self.assertEqual(store.writes, 9)

    async def test_api_validation(self):
        journal = Journal(FakeStore())
        with self.assertRaises(JournalError):
            await journal.capture(record())
        await journal.load()
        with self.assertRaises(JournalError):
            await journal.get("../../deploy_relay")
        with self.assertRaises(JournalError):
            await journal.list(limit=100)
        with self.assertRaises(JournalError):
            await journal.load()


if __name__ == "__main__":
    unittest.main()
