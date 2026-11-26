"""G2-20: durable, secret-free, non-resumable HA source job history."""
from __future__ import annotations

import asyncio
import copy
import importlib
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_source_history_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
h = importlib.import_module(PKG + ".source_job_history")
j = importlib.import_module(PKG + ".source_preview_jobs")

REPO = "TheDaimos/gewitterradar"


class MemoryStore:
    def __init__(self):
        self.data = None
        self.fail_save = False
    async def async_load(self):
        return copy.deepcopy(self.data)
    async def async_save(self, doc):
        if self.fail_save:
            raise OSError("secrets: should never leak")
        self.data = copy.deepcopy(doc)


def safe_report():
    return {
        "schema": "dra-v2-dev-source-preview.v1",
        "repository": REPO,
        "source_commit": "a" * 40,
        "sources_verified": True,
        "local_inventory_readonly": True,
        "handover_required": True,
        "backup_verified": False,
        "installation_enabled": False,
        "add": ["custom_components/gewitterradar/main.py"],
        "target_claims": {
            "exclusive_ownership_verified": False,
            "cross_process_lock_verified": False,
            "backup_verified": False,
            "installation_enabled": False,
        },
    }


class SourceJobHistoryContract(unittest.IsolatedAsyncioTestCase):
    async def test_restart_interrupts_queued_and_never_restores_result(self):
        store = MemoryStore()
        history = h.SourceJobHistory(store)
        await history.load()
        await history.queued("a" * 32)
        self.assertEqual((await history.list())[0]["status"], "queued")
        self.assertNotIn("gewitterradar", json.dumps(store.data).lower())
        restarted = h.SourceJobHistory(store)
        await restarted.load()
        record = (await restarted.list())[0]
        self.assertEqual(record["status"], "interrupted")
        self.assertEqual(record["reason"], "interrupted")
        self.assertFalse(record["resume_allowed"])
        self.assertFalse(record["source_preview_saved"])
        self.assertFalse(record["installation_enabled"])
        self.assertIsNotNone(record["finished_at"])

    async def test_success_metadata_can_survive_but_not_authorize_preview(self):
        store = MemoryStore()
        history = h.SourceJobHistory(store)
        await history.load()
        await history.queued("b" * 32)
        await history.terminal("b" * 32, "success")
        check = h.SourceJobHistory(store)
        await check.load()
        record = (await check.list())[0]
        self.assertEqual(record["status"], "success")
        self.assertEqual(set(record), h.FIELDS)
        self.assertFalse(record["source_preview_saved"])
        self.assertFalse(record["installation_enabled"])
        self.assertNotIn("source_commit", json.dumps(store.data))
        self.assertNotIn("repository", json.dumps(store.data))
        self.assertNotIn("token", json.dumps(store.data))

    async def test_reject_corrupt_or_secret_bearing_history_without_replacing(self):
        store = MemoryStore()
        store.data = {"schema": h.SCHEMA, "records": [{
            "operation_id": "c" * 32, "status": "success",
            "created_at": h.utc_now(), "finished_at": h.utc_now(),
            "reason": None, "installation_enabled": False,
            "resume_allowed": False, "source_preview_saved": False,
            "github_token": "github_pat_must_not_leak",
        }]}
        original = copy.deepcopy(store.data)
        with self.assertRaises(h.SourceJobHistoryError):
            await h.SourceJobHistory(store).load()
        self.assertEqual(store.data, original)

    async def test_store_failure_is_transactional_and_fail_closed(self):
        store = MemoryStore()
        history = h.SourceJobHistory(store)
        await history.load()
        store.fail_save = True
        with self.assertRaises(h.SourceJobHistoryError):
            await history.queued("d" * 32)
        self.assertEqual(await history.list(), [])
        self.assertIsNone(store.data)
        store.fail_save = False
        await history.queued("d" * 32)
        store.fail_save = True
        with self.assertRaises(h.SourceJobHistoryError):
            await history.terminal("d" * 32, "success")
        self.assertEqual((await history.list())[0]["status"], "queued")
        self.assertEqual(store.data["records"][0]["status"], "queued")

    async def test_only_eight_metadata_records_remain(self):
        store = MemoryStore()
        history = h.SourceJobHistory(store)
        await history.load()
        for index in range(12):
            identifier = f"{index:032x}"
            await history.queued(identifier)
            await history.terminal(identifier, "failed", reason="source_unavailable")
        rows = await history.list()
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["operation_id"], f"{11:032x}")
        self.assertEqual(rows[-1]["operation_id"], f"{4:032x}")
        self.assertLess(len(json.dumps(store.data).encode()), h.MAX_BYTES)

    async def test_source_job_is_not_started_when_history_cannot_be_written(self):
        store = MemoryStore()
        hist = h.SourceJobHistory(store)
        await hist.load()
        store.fail_save = True
        scheduled = []
        async def work():
            raise AssertionError("network must never start")
        def factory(coro):
            scheduled.append(coro)
            return asyncio.create_task(coro)
        jobs = j.SourcePreviewJobs(factory, history=hist)
        self.addAsyncCleanup(jobs.close)
        with self.assertRaises(j.SourcePreviewJobError):
            await jobs.start(REPO, "", inspect=work)
        self.assertFalse(scheduled)
        self.assertIsNone(await jobs.latest())

    async def test_full_source_job_persists_only_metadata(self):
        store = MemoryStore()
        hist = h.SourceJobHistory(store)
        await hist.load()
        tasks = []
        def factory(coro):
            task = asyncio.create_task(coro)
            tasks.append(task)
            return task
        jobs = j.SourcePreviewJobs(factory, history=hist)
        self.addAsyncCleanup(jobs.close)
        admission = await jobs.start(REPO, "", inspect=lambda: asyncio.sleep(0, result=safe_report()))
        await asyncio.gather(*tasks)
        result = await jobs.get(admission["operation_id"])
        self.assertEqual(result["status"], "success")
        self.assertEqual((await hist.list())[0]["status"], "success")
        persisted = json.dumps(store.data)
        self.assertNotIn(REPO, persisted)
        self.assertNotIn("main.py", persisted)
        self.assertNotIn("a" * 40, persisted)
        restarted = h.SourceJobHistory(store)
        await restarted.load()
        self.assertEqual((await restarted.list())[0]["status"], "success")
        self.assertFalse((await restarted.list())[0]["source_preview_saved"])


if __name__ == "__main__":
    unittest.main()
