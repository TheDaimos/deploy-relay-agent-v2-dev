"""Bounded measurement profile, without HA or real 40-second sleep."""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_measure_contract"
pack = types.ModuleType(PKG)
pack.__path__ = [str(ROOT)]
sys.modules[PKG] = pack
m = importlib.import_module(f"{PKG}.readonly_benchmark")


class MeasurementTests(unittest.IsolatedAsyncioTestCase):
    async def test_measurement_is_bounded_and_sequential(self):
        report = m.ReadOnlyMeasurement()
        report.claim("a" * 32)
        steps = []
        work_calls = 0

        async def instant_sleep(seconds):
            self.assertEqual(seconds, 1)
            await asyncio.sleep(0)

        async def fake_thread(fn):
            nonlocal work_calls
            self.assertIs(fn, m._bounded_synthetic_hash)
            work_calls += 1
            await asyncio.sleep(0)
            return 2

        async def progress(phase, index, total):
            self.assertEqual(phase.value, "inventory")
            steps.append((index, total))

        with patch.object(m, "sleep", instant_sleep), patch.object(m, "to_thread", fake_thread):
            await report.run(progress)
        s = report.summary()
        self.assertEqual(len(steps), 40)
        self.assertEqual(steps[0], (1, 40))
        self.assertEqual(steps[-1], (40, 40))
        self.assertEqual(work_calls, 20)
        self.assertEqual(s["synthetic_hashes"], 40)
        self.assertEqual([s["base_seconds"], s["work_seconds"], s["after_seconds"]], [10, 20, 10])
        self.assertEqual(s["operation_id"], "a" * 32)
        self.assertEqual(s["scope"], "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY")
        self.assertNotIn("path", s)
        self.assertNotIn("token", s)

    async def test_measurement_is_volatile_and_not_exported_until_finished(self):
        report = m.ReadOnlyMeasurement()
        self.assertIsNone(report.summary())
        report.claim("a" * 32)
        self.assertIsNone(report.summary())
        async def cancel(_phase, index, _total):
            if index == 3:
                raise asyncio.CancelledError()
        async def noop(_seconds):
            await asyncio.sleep(0)
        with patch.object(m, "sleep", noop):
            with self.assertRaises(asyncio.CancelledError):
                await report.run(cancel)
        self.assertIsNone(report.summary())

    def test_hash_work_hard_caps(self):
        import inspect
        src = inspect.getsource(m._bounded_synthetic_hash)
        self.assertIn("processed < 32", src)
        self.assertIn("+ 0.040", src)
        self.assertLessEqual(m._bounded_synthetic_hash(), 32)

    def test_measurement_reset_and_defensive_copy(self):
        report = m.ReadOnlyMeasurement()
        with self.assertRaises(ValueError):
            report.claim("not-a-uuid")
        report.claim("a" * 32)
        self.assertIsNone(report.summary())
        report._summary = {"elapsed_ms": 20}
        a = report.summary()
        a["elapsed_ms"] = 999
        self.assertEqual(report.summary()["elapsed_ms"], 20)
        report.claim("b" * 32)
        self.assertIsNone(report.summary())


if __name__ == "__main__":
    unittest.main()
