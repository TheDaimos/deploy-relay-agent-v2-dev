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
