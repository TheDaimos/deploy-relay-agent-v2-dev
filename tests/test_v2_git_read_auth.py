"""Separate V2 GitHub source read-auth persists without exposing its token."""
from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_read_auth_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
m = importlib.import_module(f"{PKG}.remote_source")

TOKEN = "github_pat_private_source_readonly"


class Store:
    def __init__(self, val=None):
        self.value = val
        self.fail = False
        self.writes = 0

    async def async_load(self):
        return self.value

    async def async_save(self, v):
        if self.fail:
            raise OSError("secret persistence failed")
        self.value = v
        self.writes += 1


class GitReadAuthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = Store()
        self.auth = m.GitReadAuth(self.store)
        await self.auth.load()

    async def test_load_empty_does_not_persist_or_share_export_credentials(self):
        self.assertIsNone(self.auth.token)
        self.assertIs(self.auth.configured, False)
        self.assertEqual(self.store.writes, 0)

    async def test_explicit_configure_and_restart_roundtrip(self):
        await self.auth.configure(TOKEN)
        self.assertEqual(self.store.value["schema"], m.READ_AUTH_SCHEMA)
        self.assertEqual(self.auth.token, TOKEN)
        again = m.GitReadAuth(self.store)
        await again.load()
        self.assertTrue(again.configured)
        self.assertEqual(again.token, TOKEN)
        await again.clear()
        self.assertFalse(again.configured)
        self.assertIsNone(self.store.value["token"])

    async def test_invalid_token_rejected_before_storage(self):
        for token in ("", "short", "malicious\nAuthorization: bad",
                      "https://github.com/anyone", "x" * 1000, None,
                      True):
            with self.subTest(token=token), self.assertRaises(m.GitReadAuthError):
                await self.auth.configure(token)
        self.assertEqual(self.store.writes, 0)
        self.assertIsNone(self.auth.token)

    async def test_corrupted_unknown_store_fails_closed(self):
        for obj in ({"token": TOKEN},
                    {"schema": "future", "token": TOKEN},
                    {"schema": m.READ_AUTH_SCHEMA, "token": TOKEN, "export_secret": "x"}):
            with self.subTest(obj=obj):
                with self.assertRaises(m.GitReadAuthError):
                    await m.GitReadAuth(Store(obj)).load()

    async def test_persistence_failure_does_not_claim_new_credentials(self):
        self.store.fail = True
        with self.assertRaises(m.GitReadAuthError):
            await self.auth.configure(TOKEN)
        self.assertFalse(self.auth.configured)
        self.assertIsNone(self.auth.token)

    async def test_failed_clear_retains_last_known_credential(self):
        await self.auth.configure(TOKEN)
        self.store.fail = True
        with self.assertRaises(m.GitReadAuthError):
            await self.auth.clear()
        self.assertTrue(self.auth.configured)
        self.assertEqual(self.auth.token, TOKEN)


if __name__ == "__main__":
    unittest.main()
