"""G2: server-owned and reconnectable read-only preview job contracts."""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_source_jobs_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
module = importlib.import_module(PKG + ".source_preview_jobs")
SourcePreviewJobs = module.SourcePreviewJobs
SourcePreviewJobError = module.SourcePreviewJobError
REPO = "TheDaimos/gewitterradar"


def successful(repo=REPO):
    return {
        "schema": "dra-v2-dev-source-preview.v1",
        "repository": repo, "sources_verified": True,
        "local_inventory_readonly": True, "handover_required": True,
        "backup_verified": False, "installation_enabled": False,
        "source_commit": "a" * 40,
        "add": ["custom_components/gewitterradar/a.py"],
        "target_claims": {
            "exclusive_ownership_verified": False,
            "cross_process_lock_verified": False,
            "backup_verified": False,
            "installation_enabled": False,
        },
    }


class SourcePreviewJobContract(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tasks = []
        def factory(coro):
            task = asyncio.create_task(coro)
            self.tasks.append(task)
            return task
        self.owner = SourcePreviewJobs(factory)
        self.addAsyncCleanup(self.owner.close)

    async def test_browser_detach_same_id_and_backend_owned_completion(self):
        started = asyncio.Event()
        release = asyncio.Event()
        count = 0
        async def inspect():
            nonlocal count
            count += 1
            started.set()
            await release.wait()
            return successful()
        first = await self.owner.start(REPO, "", inspect=inspect)
        self.assertEqual(first["status"], "queued")
        await asyncio.wait_for(started.wait(), 2)
        again = await self.owner.start("thedaimos/GEWITTERRADAR", "", inspect=inspect)
        self.assertEqual(first["operation_id"], again["operation_id"])
        self.assertEqual(count, 1)
        with self.assertRaises(SourcePreviewJobError):
            await self.owner.start("TheDaimos/weather-router-dev", "", inspect=inspect)
        # The websocket caller is gone, but this detached backend task finishes.
        release.set()
        await asyncio.gather(*self.tasks)
        restored = await self.owner.get(first["operation_id"])
        self.assertEqual(restored["status"], "success")
        self.assertEqual(restored["stage"], "complete")
        self.assertFalse(restored["installation_enabled"])
        self.assertEqual((await self.owner.latest())["operation_id"], first["operation_id"])
        restored["result"]["add"].append("fake.py")
        self.assertEqual(len((await self.owner.latest())["result"]["add"]), 1)

    async def test_read_only_self_preview_accepts_complete_false_security_claims(self):
        """Read-only DRA V2 may preview itself, but never grants install rights."""
        own_repo = "TheDaimos/deploy-relay-agent-v2-dev"
        async def inspect():
            report = successful(own_repo)
            report["self_preview_readonly"] = True
            report["target_claims"].update(
                schema="dra-v2-dev-target-claims.v1",
                handover_required=True, self_target_protected=True)
            return report
        job = await self.owner.start(own_repo, "feature/v2-10-inventory-operation-contract",
                                     inspect=inspect)
        await asyncio.gather(*self.tasks)
        result = await self.owner.get(job["operation_id"])
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["installation_enabled"])
        self.assertTrue(result["result"]["self_preview_readonly"])
        for field in ("exclusive_ownership_verified", "cross_process_lock_verified",
                      "backup_verified", "installation_enabled"):
            self.assertIs(result["result"]["target_claims"][field], False)

    async def test_read_only_self_preview_missing_protection_fields_fails_closed(self):
        own_repo = "TheDaimos/deploy-relay-agent-v2-dev"
        async def incomplete():
            report = successful(own_repo)
            report["self_preview_readonly"] = True
            # Regression for the previously broken self-preview response.
            del report["target_claims"]["cross_process_lock_verified"]
            del report["target_claims"]["backup_verified"]
            return report
        job = await self.owner.start(own_repo, "feature/v2-10-inventory-operation-contract",
                                     inspect=incomplete)
        await asyncio.gather(*self.tasks)
        result = await self.owner.get(job["operation_id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "source_unavailable")
        self.assertIsNone(result["result"])

    async def test_fixed_connection_test_wait_survives_browser_detach(self):
        self.assertEqual(module.CONNECTION_TEST_SECONDS, 60)
        waiting = asyncio.Event()
        release = asyncio.Event()
        calls = 0
        original = module._connection_test_delay

        async def controlled_wait():
            waiting.set()
            await release.wait()

        async def inspect():
            nonlocal calls
            calls += 1
            return successful()

        module._connection_test_delay = controlled_wait
        try:
            first = await self.owner.start(REPO, "", inspect=inspect,
                                           connection_test=True)
            self.assertTrue(first["connection_test"])
            self.assertFalse(first["installation_enabled"])
            await asyncio.wait_for(waiting.wait(), 2)
            pending = await self.owner.get(first["operation_id"])
            self.assertEqual(pending["stage"], "connection_test_wait")
            self.assertEqual(pending["status"], "running")
            self.assertEqual(calls, 0, "no source read before test window ends")
            # Simulate second browser, same test mode, not a new task.
            repeat = await self.owner.start(REPO, "", inspect=inspect,
                                            connection_test=True)
            self.assertEqual(repeat["operation_id"], first["operation_id"])
            with self.assertRaises(SourcePreviewJobError):
                await self.owner.start(REPO, "", inspect=inspect,
                                       connection_test=False)
            release.set()
            await asyncio.gather(*self.tasks)
            after = await self.owner.get(first["operation_id"])
            self.assertEqual(calls, 1)
            self.assertEqual(after["status"], "success")
            self.assertTrue(after["connection_test"])
            self.assertFalse(after["result"]["installation_enabled"])
            self.assertFalse(after["installation_enabled"])
        finally:
            release.set()
            module._connection_test_delay = original

    async def test_connection_mode_not_user_duration(self):
        async def inspect():
            return successful()
        for mode in (30, "30", None, [], {}):
            with self.subTest(mode=mode):
                with self.assertRaises(SourcePreviewJobError):
                    await self.owner.start(REPO, "", inspect=inspect,
                                           connection_test=mode)
        self.assertEqual(len(self.tasks), 0)


    async def test_error_does_not_produce_verified_source(self):
        async def fail():
            raise RuntimeError("token ghp_very_private /config/secrets.yaml")
        original = await self.owner.start(REPO, "main", inspect=fail)
        await asyncio.gather(*self.tasks)
        end = await self.owner.get(original["operation_id"])
        self.assertEqual(end["status"], "failed")
        self.assertEqual(end["reason"], "source_unavailable")
        self.assertIsNone(end["result"])
        self.assertNotIn("ghp_", str(end))

    async def test_unverified_or_writable_report_cannot_be_accepted(self):
        async def bad():
            return {"repository": REPO, "sources_verified": True,
                    "installation_enabled": True}
        await self.owner.start(REPO, "", inspect=bad)
        await asyncio.gather(*self.tasks)
        end = await self.owner.latest()
        self.assertEqual(end["status"], "failed")
        self.assertIsNone(end["result"])
        self.assertFalse(end["installation_enabled"])

    async def test_close_marks_running_job_interrupted(self):
        gate = asyncio.Event()
        async def suspended():
            await gate.wait()
            return successful()
        await self.owner.start(REPO, "", inspect=suspended)
        await asyncio.sleep(0)
        await self.owner.close()
        end = await self.owner.latest()
        self.assertEqual(end["status"], "interrupted")
        self.assertIsNone(end["result"])
        with self.assertRaises(SourcePreviewJobError):
            await self.owner.start(REPO, "", inspect=suspended)

    async def test_invalid_identity_and_reference_denied(self):
        for repo, ref in [
            ("https://evil.invalid", ""),
            (REPO, "../main"),
            (REPO, "main?token=secret"),
        ]:
            with self.subTest(repo=repo, ref=ref):
                with self.assertRaises(SourcePreviewJobError):
                    await self.owner.start(repo, ref, inspect=lambda: None)
        with self.assertRaises(SourcePreviewJobError):
            await self.owner.get("not-a-valid-id")

    async def test_bounded_terminal_history_does_not_hide_active_job(self):
        for index in range(8):
            async def inspect():
                return successful()
            await self.owner.start(REPO, f"test{index}", inspect=inspect)
            await asyncio.gather(*self.tasks)
        self.assertEqual(len(self.owner._jobs), module.MAX_JOBS)
        self.assertEqual((await self.owner.latest())["ref"], "test7")


if __name__ == "__main__":
    unittest.main()
