"""V2 DEV Git measurement upload: strict public allowlist, isolated credentials."""
from __future__ import annotations

import asyncio
import base64
import copy
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

PATH = (Path(__file__).resolve().parents[1] /
        "custom_components" / "deploy_relay_v2_dev" / "git_measurement_export.py")
spec = importlib.util.spec_from_file_location("_v2_git_measurement_isolated", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def measurement():
    return {
        "schema": module.MEASUREMENT_SCHEMA,
        "scope": module.SCOPE,
        "operation_id": "a" * 32,
        "base_seconds": 10,
        "work_seconds": 20,
        "after_seconds": 10,
        "base_process_cpu_ms": 100,
        "work_process_cpu_ms": 200,
        "after_process_cpu_ms": 90,
        "max_wakeup_delay_ms": 8,
        "elapsed_ms": 40016,
        "synthetic_hashes": 46,
    }


class FakeStore:
    def __init__(self, data=None):
        self.data = copy.deepcopy(data)
        self.writes = 0
        self.fail_save = False

    async def async_load(self):
        return copy.deepcopy(self.data)

    async def async_save(self, data):
        if self.fail_save:
            raise RuntimeError("PRIVATE TOKEN MUST NOT LEAK")
        self.data = copy.deepcopy(data)
        self.writes += 1


class FakeResponse:
    def __init__(self, status=201, payload=None):
        self.status = status
        self.payload = payload if payload is not None else {"commit": {"sha": "b" * 40}}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response=None):
        self.requests = []
        self.response = response or FakeResponse()

    def put(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return self.response


class GitExportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.token = "github_pat_A_TEST_TOKEN_FOR_TEST_ONLY"
        self.store = FakeStore()
        self.session = FakeSession()
        self.writer = module.MeasurementGitExport(self.store, self.session)
        await self.writer.load()

    async def test_explicit_upload_is_public_minimal_and_isolated(self):
        self.assertFalse(self.writer.configured)
        await self.writer.configure(token=self.token)
        self.assertTrue(self.writer.configured)
        result = await self.writer.export(measurement(), version="0.1.4")
        self.assertEqual(self.store.writes, 1)
        self.assertEqual(len(self.session.requests), 1)
        url, request = self.session.requests[0]
        self.assertTrue(url.startswith(
            "https://api.github.com/repos/TheDaimos/deploy-relay-agent-v2-dev/"
            "contents/.deploy-relay/diagnostics/v2-dev/"
        ))
        self.assertEqual(request["json"]["branch"], "main")
        self.assertIn("[skip ci]", request["json"]["message"])
        self.assertNotIn("sha", request["json"])
        self.assertEqual(request["headers"]["Authorization"], f"Bearer {self.token}")
        payload = base64.b64decode(request["json"]["content"]).decode("utf-8")
        self.assertLessEqual(len(payload), module.MAX_EXPORT_BYTES)
        for forbidden in (self.token, "operation_id", "aaaaaaaaaa",
                          "subentry", "username", "/config/", "github_pat_"):
            self.assertNotIn(forbidden, payload)
        blob = json.loads(payload)
        self.assertEqual(blob["repository"], module.REPOSITORY)
        self.assertEqual(blob["branch"], "main")
        self.assertEqual(blob["snapshot"]["measurement"]["synthetic_hashes"], 46)
        self.assertEqual(blob["snapshot"]["measurement"]["scope"], module.SCOPE)
        self.assertNotIn("operation_id", blob["snapshot"]["measurement"])
        self.assertTrue(result["file_url"].startswith(
            "https://github.com/TheDaimos/deploy-relay-agent-v2-dev/blob/main/"
            ".deploy-relay/diagnostics/v2-dev/"
        ))
        self.assertEqual(result["commit_sha"], "b" * 40)

    async def test_no_upload_before_explicit_configuration(self):
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.4")
        self.assertEqual(self.session.requests, [])

    async def test_secret_store_kept_separate_and_reloaded(self):
        await self.writer.configure(token=self.token)
        another = module.MeasurementGitExport(self.store, self.session)
        await another.load()
        self.assertTrue(another.configured)
        await another.configure(clear=True)
        self.assertFalse(another.configured)
        self.assertIsNone(self.store.data["token"])
        with self.assertRaises(module.GitMeasurementError):
            await another.export(measurement(), version="0.1.4")

    async def test_corrupt_store_refused_without_overwriting(self):
        for invalid in (
            {"schema": "other", "token": self.token},
            {"schema": module.AUTH_SCHEMA, "token": self.token, "private": "SECRET"},
            {"schema": module.AUTH_SCHEMA, "token": 55},
        ):
            store = FakeStore(invalid)
            writer = module.MeasurementGitExport(store, self.session)
            with self.assertRaises(module.GitMeasurementError):
                await writer.load()
            self.assertFalse(writer.available)
            self.assertEqual(store.writes, 0)

    async def test_write_failure_keeps_old_token_and_hides_exception(self):
        await self.writer.configure(token=self.token)
        self.store.fail_save = True
        with self.assertRaises(module.GitMeasurementError) as error:
            await self.writer.configure(token="github_pat_ANOTHER_TEST_TOKEN")
        self.assertNotIn("PRIVATE TOKEN", str(error.exception))
        self.assertEqual(self.store.data["token"], self.token)
        self.assertTrue(self.writer.configured)

    async def test_reject_unknown_secret_fields_and_invalid_metrics(self):
        await self.writer.configure(token=self.token)
        for update in (
            {"password": "SECRET"},
            {"synthetic_hashes": -1},
            {"base_seconds": 11},
            {"base_process_cpu_ms": True},
            {"scope": "HA_DEV_PRIVATE_PATH"},
            {"operation_id": "not valid"},
        ):
            sample = measurement()
            sample.update(update)
            with self.subTest(update=update):
                with self.assertRaises(module.GitMeasurementError):
                    await self.writer.export(sample, version="0.1.4")
        self.assertEqual(self.session.requests, [])

    async def test_git_error_does_not_leak_token_or_response(self):
        await self.writer.configure(token=self.token)
        self.session.response = FakeResponse(status=403,
            payload={"raw_secret": self.token})
        with self.assertRaises(module.GitMeasurementError) as error:
            await self.writer.export(measurement(), version="0.1.4")
        self.assertNotIn(self.token, str(error.exception))
        self.assertNotIn("raw_secret", str(error.exception))

    async def test_invalid_confirmation_is_not_success(self):
        await self.writer.configure(token=self.token)
        self.session.response = FakeResponse(payload={"commit": {"sha": "wrong"}})
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.4")

    def test_fixed_public_target_and_utc_document(self):
        self.assertEqual(module.REPOSITORY, "TheDaimos/deploy-relay-agent-v2-dev")
        self.assertEqual(module.ROOT, ".deploy-relay/diagnostics/v2-dev")
        now = datetime(2026, 10, 8, 18, 30, tzinfo=timezone.utc)
        doc = module.public_export_document(measurement(), version="0.1.4", now=now)
        self.assertEqual(doc["created_at"], "2026-10-08T18:30:00Z")
        self.assertEqual(doc["schema"], module.EXPORT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
