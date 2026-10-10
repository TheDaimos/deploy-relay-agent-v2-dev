"""Saved V2 tuning options are not an accidental scheduler or write unlock."""
from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_settings_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
m = importlib.import_module(f"{PKG}.settings")


class Store:
    def __init__(self, value=None):
        self.value = value
        self.writes = 0
        self.fail = False

    async def async_load(self): return self.value
    async def async_save(self, value):
        if self.fail: raise OSError("no")
        self.value = value
        self.writes += 1


class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = Store()
        self.settings = m.V2Settings(self.store)
        await self.settings.load()

    async def test_defaults_are_nonmutating(self):
        self.assertEqual(self.settings.snapshot(), {
            "mode": "sequential", "max_readonly_jobs": 2,
            "max_worker_processes": 4,
        })
        self.assertEqual(self.settings.effective()["active_readonly_limit"], 1)
        self.assertEqual(self.settings.effective()["mutation_limit"], 0)
        self.assertIs(self.settings.effective()["worker_budget_enforced"], False)
        self.assertEqual(self.store.writes, 0)

    async def test_roundtrip_and_defensive_copy(self):
        desired = {"mode": "controlled", "max_readonly_jobs": 3,
                   "max_worker_processes": 12}
        result = await self.settings.save(desired)
        result["max_worker_processes"] = 99
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 12)
        self.assertEqual(self.store.writes, 1)
        await self.settings.save(desired)
        self.assertEqual(self.store.writes, 1)
        other = m.V2Settings(self.store)
        await other.load()
        self.assertEqual(other.snapshot(), desired)
        self.assertEqual(other.effective()["active_readonly_limit"], 1)

    async def test_reject_auto_and_both_out_of_range(self):
        good = self.settings.snapshot()
        bad = [{**good, "mode": "automatic"}, {**good, "mode": "write"},
               {**good, "max_readonly_jobs": 5},
               {**good, "max_worker_processes": 13},
               {**good, "max_worker_processes": 0},
               {**good, "max_worker_processes": True},
               {**good, "unexpected": "token"}]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(m.SettingsError):
                await self.settings.save(item)
        self.assertEqual(self.store.writes, 0)

    async def test_startup_reduction_persists_and_warns_after_restart(self):
        await self.settings.startup_check(12, probe=False)
        await self.settings.save({
            "mode": "controlled", "max_readonly_jobs": 3,
            "max_worker_processes": 10
        })
        restarted = m.V2Settings(self.store)
        await restarted.load()
        await restarted.startup_check(2, probe=False)
        self.assertEqual(restarted.snapshot()["max_worker_processes"], 2)
        self.assertEqual(restarted.core_status()["available_cores"], 2)
        warning = restarted.core_status()["warning"]
        self.assertEqual(warning, {
            "code": "cpu_limit_reduced", "previous_available": 12,
            "available_cores": 2, "reduced_from": 10,
        })
        self.assertEqual(restarted.effective()["active_readonly_limit"], 1)
        self.assertEqual(restarted.effective()["mutation_limit"], 0)
        persisted = m.V2Settings(self.store)
        await persisted.load()
        self.assertEqual(persisted.core_status()["warning"], warning)
        self.assertEqual(persisted.snapshot()["max_worker_processes"], 2)
        after = self.store.writes
        await persisted.startup_check(2, probe=False)
        self.assertEqual(self.store.writes, after)

    async def test_increase_is_silent_and_never_restores_earlier_preference(self):
        await self.settings.startup_check(4, probe=False)
        await self.settings.save({**m.DEFAULT, "max_worker_processes": 3})
        await self.settings.startup_check(12, probe=False)
        self.assertEqual(self.settings.core_status()["available_cores"], 12)
        self.assertIsNone(self.settings.core_status()["warning"])
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 3)

    async def test_first_observation_clamps_without_false_previous_hardware(self):
        await self.settings.startup_check(2, probe=False)
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 2)
        self.assertEqual(self.settings.core_status()["warning"]["previous_available"], None)
        self.assertEqual(self.settings.core_status()["warning"]["reduced_from"], 4)

    async def test_warning_can_be_acknowledged_without_new_reduction(self):
        await self.settings.startup_check(2, probe=False)
        await self.settings.acknowledge_warning()
        self.assertIsNone(self.settings.core_status()["warning"])
        await self.settings.startup_check(2, probe=False)
        self.assertIsNone(self.settings.core_status()["warning"])
        await self.settings.startup_check(12, probe=False)
        self.assertIsNone(self.settings.core_status()["warning"])
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 2)

    async def test_warning_survives_cpu_growth_until_user_ack(self):
        await self.settings.startup_check(2, probe=False)
        before = self.settings.core_status()["warning"]
        await self.settings.startup_check(12, probe=False)
        self.assertEqual(self.settings.core_status()["warning"], before)
        await self.settings.acknowledge_warning()
        self.assertIsNone(self.settings.core_status()["warning"])

    async def test_manual_save_cannot_exceed_available_cpu_count(self):
        await self.settings.startup_check(3, probe=False)
        before = self.store.writes
        with self.assertRaises(m.SettingsError):
            await self.settings.save({**self.settings.snapshot(), "max_worker_processes": 4})
        self.assertEqual(self.store.writes, before)
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 3)
        await self.settings.save({**self.settings.snapshot(), "max_worker_processes": 1})
        self.assertIsNone(self.settings.core_status()["warning"])

    async def test_legacy_schema_migrates_without_loss_on_startup(self):
        legacy = {"mode": "controlled", "max_readonly_jobs": 4, "max_worker_processes": 8}
        old_store = Store({"schema": m.LEGACY_SCHEMA, "settings": legacy})
        upgraded = m.V2Settings(old_store)
        await upgraded.load()
        self.assertEqual(upgraded.snapshot(), legacy)
        self.assertEqual(old_store.writes, 0)
        await upgraded.startup_check(12, probe=False)
        self.assertEqual(old_store.value["schema"], m.SCHEMA)
        self.assertEqual(old_store.value["settings"], legacy)
        self.assertEqual(old_store.value["available_cores"], 12)

    async def test_invalid_or_missing_detection_never_overwrites(self):
        await self.settings.save({**m.DEFAULT, "max_worker_processes": 11})
        before = self.store.writes
        await self.settings.startup_check(None, probe=False)
        self.assertEqual(self.store.writes, before)
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 11)
        for value in (0, -1, 4097, True, 2.5):
            with self.assertRaises(m.SettingsError):
                await self.settings.startup_check(value, probe=False)
        self.assertEqual(self.store.writes, before)

    async def test_failed_startup_persistence_is_fail_closed(self):
        self.store.fail = True
        with self.assertRaises(m.SettingsError):
            await self.settings.startup_check(2, probe=False)
        self.assertIsNone(self.settings.core_status()["available_cores"])
        self.assertEqual(self.settings.snapshot()["max_worker_processes"], 4)

    async def test_detect_affinity_is_narrower_than_host_count(self):
        from unittest.mock import patch
        with patch.object(m.os, "cpu_count", return_value=12):
            with patch.object(m.os, "sched_getaffinity", create=True, return_value={0, 1}):
                self.assertEqual(m.detect_available_cores(), 2)
            with patch.object(m.os, "sched_getaffinity", create=True, side_effect=OSError):
                self.assertEqual(m.detect_available_cores(), 12)
        with patch.object(m.os, "cpu_count", return_value=None):
            with patch.object(m.os, "sched_getaffinity", create=True, side_effect=OSError):
                self.assertIsNone(m.detect_available_cores())

    async def test_bad_store_never_autoresets(self):
        for value in ({"schema": "old", "settings": dict(m.DEFAULT)},
                      {"schema": m.SCHEMA, "settings": {"mode": "controlled"}},
                      {"schema": m.SCHEMA, "settings": {**m.DEFAULT, "token": "secret"}}):
            with self.subTest(value=value), self.assertRaises(m.SettingsError):
                await m.V2Settings(Store(value)).load()

    async def test_failed_save_does_not_mutate_live_settings(self):
        before = self.settings.snapshot()
        self.store.fail = True
        with self.assertRaises(m.SettingsError):
            await self.settings.save({**before, "max_worker_processes": 9})
        self.assertEqual(self.settings.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
