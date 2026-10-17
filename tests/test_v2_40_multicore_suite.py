"""Read-only multicore worker caps, sequencing and cancellation safety."""
import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_multicore_suite_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
m = importlib.import_module(f"{PKG}.readonly_benchmark")


def multicore():
    return {
        "schema": "dra-v2-dev-multicore.v2",
        "method": "BOUNDED_CHILD_PROCESSES",
        "logical_cpus_visible": 12,
        "affinity_cpus_visible": 12,
        "levels": [
            {"workers": n, "status": "ok", "wall_ms": 200,
             "aggregate_worker_cpu_ms": n * 120,
             "iterations_total": n * 400000}
            for n in (1, 2, 4, 6, 8, 10, 12)
        ],
    }


class SuiteTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_all_single_operation_monotonic_progress(self):
        measurement = m.ReadOnlyMeasurement()
        suite = m.ReadOnlySuite(measurement)
        suite.claim("a" * 32)
        records = []
        sample = {
            "total_kib": 4096, "used_effective_kib": 1024,
            "free_kib": 2048, "available_kib": 3072,
            "ha_process_rss_kib": 512,
        }
        async def sleep(_seconds): await asyncio.sleep(0)
        async def thread(fn):
            await asyncio.sleep(0)
            return sample if fn is m.snapshot_memory else 2
        async def cpu(progress):
            for i in range(1, 8):
                await progress(i)
            return multicore()
        async def progress(phase, index, total):
            self.assertEqual(phase.value, "inventory")
            records.append((index, total))
        with (patch.object(m, "sleep", sleep),
              patch.object(m, "to_thread", thread),
              patch.object(m, "_multiprocess_diagnostics", cpu)):
            await suite.run_all(progress)
        self.assertEqual(records, [(i, 87) for i in range(1, 88)])
        report = suite.summary()
        self.assertEqual(report["operation_id"], "a" * 32)
        self.assertEqual(report["mode"], "full")
        self.assertEqual(report["readonly_steps"], 40)
        self.assertEqual(report["measurement"]["memory"]["snapshots"]["end"], sample)
        self.assertEqual([r["workers"] for r in report["multicore"]["levels"]], [1, 2, 4, 6, 8, 10, 12])

    async def test_multicore_only_is_sequential_seven_steps(self):
        suite = m.ReadOnlySuite(m.ReadOnlyMeasurement())
        suite.claim("b" * 32)
        steps = []
        async def cpu(progress):
            for i in range(1, 8): await progress(i)
            return multicore()
        async def progress(_phase, index, total): steps.append((index, total))
        with patch.object(m, "_multiprocess_diagnostics", cpu):
            await suite.run_multicore(progress)
        self.assertEqual(steps, [(i, 7) for i in range(1, 8)])
        self.assertIsNone(suite.summary()["measurement"])
        self.assertEqual(suite.summary()["mode"], "multicore")

    async def test_interrupted_full_suite_must_have_no_exportable_report(self):
        suite = m.ReadOnlySuite(m.ReadOnlyMeasurement())
        suite.claim("c" * 32)
        async def sleep(_seconds): await asyncio.sleep(0)
        async def cancel(_phase, idx, _total):
            if idx == 3: raise asyncio.CancelledError()
        with patch.object(m, "sleep", sleep):
            with self.assertRaises(asyncio.CancelledError):
                await suite.run_all(cancel)
        self.assertIsNone(suite.summary())

    async def test_worker_command_is_fixed_and_sandboxed(self):
        calls = []
        class Child:
            returncode = None
            def __init__(self): self.returncode = None
            async def communicate(self):
                self.returncode = 0
                return (b'{"wall_ms":152,"cpu_ms":119,"iterations":400000}\n', b"")
            async def wait(self): return 0
            def kill(self): self.returncode = -9
        async def spawn(*args, **kwargs):
            calls.append((args, kwargs))
            return Child()
        with patch.object(m.asyncio, "create_subprocess_exec", spawn):
            measured = await m._single_multicore_stage(4)
        self.assertEqual(measured["status"], "ok")
        self.assertEqual(measured["iterations_total"], 1600000)
        self.assertEqual(len(calls), 4)
        for args, kwargs in calls:
            self.assertEqual(args[:4], (sys.executable, "-I", "-S", "-c"))
            self.assertIn("hashlib.pbkdf2_hmac", args[4])
            self.assertEqual(kwargs["env"], {"PYTHONHASHSEED": "0"})
            self.assertTrue(kwargs["close_fds"])

    async def test_twelve_workers_are_separate_and_bounded(self):
        calls = []
        class Child:
            returncode = None
            def __init__(self): self.returncode = None
            async def communicate(self):
                self.returncode = 0
                return (b'{"wall_ms":250,"cpu_ms":90,"iterations":400000}', b"")
            async def wait(self): return 0
            def kill(self): self.returncode = -9
        async def spawn(*args, **kwargs):
            calls.append((args, kwargs))
            return Child()
        with patch.object(m.asyncio, "create_subprocess_exec", spawn):
            result = await m._single_multicore_stage(12)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["iterations_total"], 4800000)
        self.assertEqual(len(calls), 12)
        self.assertTrue(all(args[1:4] == ("-I", "-S", "-c") for args, _ in calls))
        self.assertTrue(all(kw["env"] == {"PYTHONHASHSEED": "0"} for _, kw in calls))

    async def test_kill_and_reap_children_if_subprocess_fails(self):
        killed = []
        class Child:
            returncode = None
            async def communicate(self): raise OSError("permission denied")
            async def wait(self): return 0
            def kill(self): killed.append(True); self.returncode = -9
        async def spawn(*args, **kwargs): return Child()
        with patch.object(m.asyncio, "create_subprocess_exec", spawn):
            result = await m._single_multicore_stage(2)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(len(killed), 2)
        self.assertIsNone(result["wall_ms"])


    async def test_real_short_lived_workers_execute_and_exit(self):
        """CI smoke: fixed subprocess executable, no network or HA imports."""
        level = await asyncio.wait_for(m._single_multicore_stage(1), timeout=9)
        self.assertEqual(level["workers"], 1)
        self.assertEqual(level["status"], "ok")
        self.assertEqual(level["iterations_total"], 400000)
        self.assertGreaterEqual(level["aggregate_worker_cpu_ms"], 1)

    async def test_no_more_than_twelve_workers_allowed(self):
        with self.assertRaises(ValueError):
            await m._single_multicore_stage(14)


if __name__ == "__main__":
    unittest.main()
