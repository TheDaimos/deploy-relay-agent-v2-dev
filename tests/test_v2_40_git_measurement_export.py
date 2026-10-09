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
        "memory": {
            "schema": module.MEMORY_SCHEMA,
            "source": module.MEMORY_SOURCE,
            "component_memory": {
                "dra_v1_kib": None, "dra_v2_kib": None,
                "reason": module.MEMORY_REASON,
            },
            "snapshots": {
                point: {
                    "total_kib": 7340032,
                    "used_effective_kib": 3145728,
                    "free_kib": 2097152,
                    "available_kib": 4194304,
                    "ha_process_rss_kib": 524288,
                } for point in module.MEMORY_POINTS
            },
        },
    }




def combined_suite(mode="full"):
    return {
        "schema": module.SUITE_SCHEMA,
        "operation_id": "a" * 32,
        "mode": mode,
        "readonly_steps": 40 if mode == "full" else 0,
        "measurement": measurement() if mode == "full" else None,
        "multicore": {
            "schema": module.MULTICORE_SCHEMA,
            "method": "BOUNDED_CHILD_PROCESSES",
            "logical_cpus_visible": 12,
            "affinity_cpus_visible": 12,
            "levels": [
                {"workers": workers, "status": "ok", "wall_ms": 260,
                 "aggregate_worker_cpu_ms": workers * 120,
                 "iterations_total": workers * 400000}
                for workers in (1, 2, 4, 6, 8, 10, 12)
            ],
        },
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
        self.content = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def json(self):
        return self.payload

    async def read(self, maximum):
        return json.dumps(self.payload).encode("utf-8")[:maximum]


class FakeSession:
    def __init__(self, response=None):
        self.requests = []
        self.visibility_requests = []
        self.response = response or FakeResponse()
        self.repo_response = FakeResponse(200, {
            "full_name": "TheDaimos/Project-Log-And-Export",
            "private": True, "default_branch": "main",
        })

    def get(self, url, **kwargs):
        self.visibility_requests.append((url, kwargs))
        return self.repo_response

    def put(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return self.response


class GitExportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.token = "github_pat_SYNTHETIC_TEST_NEVER_REAL"
        self.store = FakeStore()
        self.session = FakeSession()
        self.writer = module.MeasurementGitExport(
            self.store, self.session, token_provider=lambda: self.token,
        )
        await self.writer.load()
        await self.writer.set_repository("TheDaimos/Project-Log-And-Export")

    def uploaded(self, n=0):
        url, request = self.session.requests[n]
        payload = base64.b64decode(request["json"]["content"])
        return url, request, json.loads(payload)

    async def test_no_default_repository_and_download_without_github(self):
        store = FakeStore()
        writer = module.MeasurementGitExport(
            store, self.session, token_provider=lambda: None,
        )
        await writer.load()
        self.assertIsNone(writer.repository)
        self.assertIsNone(writer.status()["repository"])
        self.assertFalse(writer.configured)
        with self.assertRaises(module.GitMeasurementError):
            await writer.export(measurement(), version="0.1.14")
        local = writer.local_download(measurement(), version="0.1.14")
        content = json.loads(local["content"])
        self.assertEqual(local["application_id"], "deploy-relay-agent-v2")
        self.assertEqual(content["exportSchema"], module.STANDARD_SCHEMA)
        self.assertEqual(content["snapshot"]["measurement"]["synthetic_hashes"], 46)
        self.assertTrue(local["filename"].endswith("__" + local["export_id"] + ".json"))
        self.assertEqual(store.writes, 0)
        self.assertEqual(self.session.requests, [])
        self.assertEqual(self.session.visibility_requests, [])

    async def test_admin_repository_change_clear_and_no_implicit_transfer(self):
        await self.writer.clear_repository()
        self.assertIsNone(self.writer.repository)
        self.assertFalse(self.writer.configured)
        await self.writer.set_repository("AnotherOwner/Private-Archive")
        self.session.repo_response = FakeResponse(200, {
            "full_name": "AnotherOwner/Private-Archive",
            "private": True, "default_branch": "trunk",
        })
        result = await self.writer.export(measurement(), version="0.1.14")
        self.assertEqual(result["repository"], "AnotherOwner/Private-Archive")
        self.assertEqual(result["branch"], "trunk")
        self.assertIn("/repos/AnotherOwner/Private-Archive/contents/", self.session.requests[0][0])
        self.assertEqual(self.session.requests[0][1]["json"]["branch"], "trunk")
        await self.writer.clear_repository()
        self.assertIsNone(self.writer.repository)

    async def test_cannot_switch_destination_while_export_pending(self):
        self.session.response = FakeResponse(503)
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.14")
        original = copy.deepcopy(self.store.data)
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.set_repository("Other/Archive")
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.clear_repository()
        self.assertEqual(self.store.data, original)
        self.assertEqual(self.writer.repository, "TheDaimos/Project-Log-And-Export")

    async def test_repo_names_are_validated_without_vendor_default(self):
        for repository in (
            "", "https://github.com/Owner/Private", "Owner/../../a",
            "Owner/Repo?branch=a", "Owner/Repo/extra", "owner/.storage",
            "Owner/Private\nAuthorization", True, None,
        ):
            with self.subTest(repository=repository), self.assertRaises(module.GitMeasurementError):
                await self.writer.set_repository(repository)

    async def test_download_works_with_failed_pending_upload(self):
        self.session.response = FakeResponse(403)
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.14")
        before = copy.deepcopy(self.store.data)
        payload = self.writer.local_download(measurement(), version="0.1.14")
        self.assertEqual(json.loads(payload["content"])["application"]["id"],
                         "deploy-relay-agent-v2")
        self.assertEqual(self.store.data, before)

    async def test_private_export_metadaten_and_correct_month(self):
        result = await self.writer.export(measurement(), version="0.1.14")
        self.assertEqual(len(self.session.requests), 1)
        url, request, body = self.uploaded()
        self.assertIn("/repos/TheDaimos/Project-Log-And-Export/contents/exports/", url)
        self.assertNotIn("/deploy-relay-agent-v2-dev/contents/", url)
        self.assertIn("/exports/deploy-relay-agent-v2/", url)
        self.assertTrue(url.startswith("https://api.github.com/"))
        self.assertIs(request["allow_redirects"], False)
        self.assertNotIn("sha", request["json"], "Must CREATE, never overwrite")
        self.assertEqual(request["json"]["branch"], "main")
        self.assertEqual(request["headers"]["Authorization"], "Bearer " + self.token)
        self.assertEqual(body["exportSchema"], module.STANDARD_SCHEMA)
        self.assertEqual(body["application"], {
            "id": "deploy-relay-agent-v2", "name": "Deploy Relay Agent V2",
            "version": "0.1.14",
        })
        self.assertEqual(body["export"]["type"], "diagnostics")
        self.assertRegex(body["export"]["capturedAt"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertRegex(body["export"]["exportId"], r"^[0-9a-f]{32}$")
        self.assertEqual(body["source"], {
            "repository": module.SOURCE_REPOSITORY, "commit": None,
        })
        self.assertEqual(body["test"]["id"], "V2-CPU-RAM")
        self.assertIsNone(body["test"]["capabilityUiNumber"])
        self.assertEqual(body["snapshot"]["schema"], module.EXPORT_SCHEMA)
        self.assertEqual(body["snapshot"]["measurement"]["synthetic_hashes"], 46)
        self.assertEqual(result["export_id"], body["export"]["exportId"])
        self.assertEqual(result["path"], module.archive_path(body))
        self.assertEqual(result["repository"], "TheDaimos/Project-Log-And-Export")
        self.assertIn("/" + body["export"]["capturedAt"][:7] + "/diagnostics/", result["path"])
        self.assertFalse(self.writer.pending)
        self.assertNotIn(self.token, str(body))

    async def test_two_exports_are_distinct_even_same_second(self):
        a = await self.writer.export(measurement(), version="0.1.14")
        b = await self.writer.export(measurement(), version="0.1.14")
        self.assertNotEqual(a["export_id"], b["export_id"])
        self.assertNotEqual(a["path"], b["path"])
        self.assertEqual(len(self.session.requests), 2)
        self.assertTrue(all("sha" not in x[1]["json"] for x in self.session.requests))

    def test_display_name_change_never_changes_immutable_id_or_folder(self):
        stamp = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
        first = module.archive_document(
            measurement(), version="0.1.14", now=stamp,
            export_id="a"*32, display_name="Deploy Relay Agent V2",
        )
        renamed = module.archive_document(
            measurement(), version="0.1.14", now=stamp,
            export_id="a"*32, display_name="DRA Zukunft",
        )
        self.assertEqual(first["application"]["id"], renamed["application"]["id"])
        self.assertEqual(module.archive_path(first), module.archive_path(renamed))
        self.assertEqual(renamed["application"]["name"], "DRA Zukunft")

    def test_missing_or_lying_metadata_rejected(self):
        stamp = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
        for kwargs in (
            {"export_id": ""}, {"export_id": "wrong"},
            {"display_name": ""}, {"display_name": "\nSECRET"},
            {"source_commit": "wrong"}, {"version": ""},
        ):
            params = {
                "version": "0.1.14", "now": stamp, "export_id": "a"*32,
            }
            params.update(kwargs)
            with self.subTest(params=params), self.assertRaises(module.GitMeasurementError):
                module.archive_document(measurement(), **params)
        with self.assertRaises(module.GitMeasurementError):
            module.archive_document(measurement(), version="0.1.14",
                                    now=stamp.replace(tzinfo=None), export_id="a"*32)
        valid = module.archive_document(measurement(), version="0.1.14", now=stamp, export_id="a"*32)
        valid["application"]["id"] = "other-app"
        with self.assertRaises(module.GitMeasurementError):
            module.archive_path(valid)

    async def test_strict_anonymization_rejects_added_secrets(self):
        for change in (
            {"authorization": self.token}, {"password": self.token},
            {"scope": "ghp_SECRET_PRIVATE"}, {"operation_id": "x"*64},
            {"memory": {"api_key": self.token}}, {"synthetic_hashes": -100},
        ):
            sample = measurement()
            sample.update(change)
            with self.subTest(change=change), self.assertRaises(module.GitMeasurementError):
                await self.writer.export(sample, version="0.1.14")
        self.assertEqual(self.session.requests, [])
        self.assertEqual(self.store.writes, 1)

    async def test_full_suite_snapshot_remains_compatible(self):
        result = await self.writer.export(combined_suite(), version="0.1.14")
        url, kwargs, obj = self.uploaded()
        self.assertEqual(obj["test"]["id"], "V2-READONLY-FULL")
        self.assertEqual(obj["snapshot"]["schema"], module.SUITE_EXPORT_SCHEMA)
        self.assertEqual(obj["snapshot"]["suite"]["readonly_steps"], 40)
        self.assertEqual(
            [x["workers"] for x in obj["snapshot"]["suite"]["multicore"]["levels"]],
            [1, 2, 4, 6, 8, 10, 12],
        )
        self.assertNotIn("operation_id", json.dumps(obj))
        self.assertEqual(result["repository"], "TheDaimos/Project-Log-And-Export")

    async def test_multicore_only_and_unavailable_are_kept(self):
        report = combined_suite("multicore")
        report["multicore"]["levels"][2].update({
            "status": "unavailable", "wall_ms": None,
            "aggregate_worker_cpu_ms": None, "iterations_total": None,
        })
        await self.writer.export(report, version="0.1.14")
        _, _, obj = self.uploaded()
        self.assertEqual(obj["test"]["id"], "V2-MULTICORE")
        self.assertIsNone(obj["snapshot"]["suite"]["measurement"])
        self.assertEqual(obj["snapshot"]["suite"]["multicore"]["levels"][2]["status"], "unavailable")

    async def test_untrusted_suite_is_rejected(self):
        malformed = combined_suite()
        malformed["multicore"]["password"] = self.token
        for sample in (malformed, {**combined_suite(), "mode": "root"}):
            with self.assertRaises(module.GitMeasurementError):
                await self.writer.export(sample, version="0.1.14")
        self.assertEqual(self.session.requests, [])

    async def test_public_or_unverifiable_archive_is_never_written(self):
        for status, meta in (
            (200, {"full_name":"TheDaimos/Project-Log-And-Export",
                   "private":False, "default_branch":"main"}),
            (200, {"full_name":"TheDaimos/untrusted", "private":True,
                   "default_branch":"main"}),
            (403, {"message":"forbidden"}),
            (404, {"message":"missing"}),
        ):
            with self.subTest(status=status, meta=meta):
                self.session.repo_response = FakeResponse(status, meta)
                with self.assertRaises(module.GitMeasurementError):
                    await self.writer.export(measurement(), version="0.1.14")
                self.assertEqual(self.session.requests, [])
                self.assertTrue(self.writer.pending)
                # Explicit retry of the same path after visibility becomes private.
                self.session.repo_response = FakeResponse(200, {
                    "full_name":"TheDaimos/Project-Log-And-Export",
                    "private":True, "default_branch":"main",
                })
                await self.writer.retry_pending()
                self.assertFalse(self.writer.pending)
                self.assertTrue(self.session.visibility_requests)
                self.assertTrue(all("allow_redirects" in kw and kw["allow_redirects"] is False
                                    for _, kw in self.session.visibility_requests))
                self.session.requests.clear()

    async def test_persisted_payload_with_nested_secrets_is_rejected(self):
        self.session.response = FakeResponse(503)
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.14")
        good = self.store.data
        for mutate in (
            lambda x: x["snapshot"]["measurement"].update({"authorization":"SECRET"}),
            lambda x: x["snapshot"]["measurement"].update({"synthetic_hashes":"evil"}),
            lambda x: x["snapshot"]["measurement"]["memory"]["snapshots"]["start"].update(
                {"password":"SECRET"}),
            lambda x: x["snapshot"].update({"note":"unapproved"}),
        ):
            bad = copy.deepcopy(good)
            raw = json.loads(bad["pending"]["raw"])
            mutate(raw)
            bad["pending"]["raw"] = json.dumps(raw, sort_keys=True, separators=(",", ":"))+"\n"
            pending = module.MeasurementGitExport(
                FakeStore(bad), self.session, token_provider=lambda:self.token)
            with self.assertRaises(module.GitMeasurementError):
                await pending.load()

    async def test_403_rejected_and_original_kept_locally(self):
        self.session.response = FakeResponse(403, {"raw_token": self.token})
        with self.assertRaises(module.GitMeasurementError) as caught:
            await self.writer.export(measurement(), version="0.1.14")
        self.assertNotIn(self.token, str(caught.exception))
        self.assertEqual(self.store.data["schema"], module.QUEUE_SCHEMA)
        self.assertEqual(self.store.data["pending"]["repository"], "TheDaimos/Project-Log-And-Export")
        self.assertTrue(self.writer.pending)
        self.assertNotIn(self.token, self.store.data["pending"]["raw"])
        self.assertEqual(len(self.session.requests), 1)

    async def test_network_failure_retry_same_id_then_clear(self):
        self.session.response = FakeResponse(503)
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.14")
        first = copy.deepcopy(self.store.data["pending"])
        previous_writer = module.MeasurementGitExport(
            self.store, self.session, token_provider=lambda: self.token,
        )
        await previous_writer.load()
        self.assertTrue(previous_writer.pending)
        with self.assertRaises(module.GitMeasurementError):
            await previous_writer.export(measurement(), version="0.1.14")
        self.session.response = FakeResponse(201)
        result = await previous_writer.retry_pending()
        self.assertEqual(result["export_id"], first["export_id"])
        self.assertEqual(result["path"], first["path"])
        self.assertFalse(previous_writer.pending)
        self.assertIsNone(self.store.data["pending"])
        self.assertEqual(len(self.session.requests), 2)

    async def test_collision_422_never_updates_existing_file(self):
        self.session.response = FakeResponse(422)
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.14")
        before = copy.deepcopy(self.store.data["pending"])
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.retry_pending()
        self.assertEqual(self.store.data["pending"], before)
        self.assertEqual(len(self.session.requests), 2)
        self.assertTrue(all("sha" not in args["json"] for _, args in self.session.requests))

    async def test_no_token_on_server_no_network_or_queue(self):
        writer = module.MeasurementGitExport(
            self.store, self.session, token_provider=lambda: None,
        )
        await writer.load()
        self.assertFalse(writer.configured)
        with self.assertRaises(module.GitMeasurementError):
            await writer.export(measurement(), version="0.1.14")
        self.assertEqual(self.session.requests, [])
        self.assertEqual(self.store.writes, 1)

    async def test_browser_token_configuration_is_disabled(self):
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.configure(token=self.token)
        self.assertEqual(self.store.writes, 1)

    async def test_corrupted_pending_queue_never_silently_overwritten(self):
        for bad in (
            {"schema": "unknown", "pending": None},
            {"schema": module.QUEUE_SCHEMA, "repository": "User/Repo", "pending": {"path": "public"}},
            {"schema": module.QUEUE_SCHEMA, "repository": "User/Repo", "pending": {
                "path": "exports/deploy-relay-agent-v2/evil",
                "export_id": "a"*32, "raw": '{"password":"SECRET"}',
            }},
        ):
            store = FakeStore(bad)
            writer = module.MeasurementGitExport(
                store, self.session, token_provider=lambda: self.token,
            )
            with self.assertRaises(module.GitMeasurementError):
                await writer.load()
            self.assertEqual(store.writes, 0)

    async def test_local_queue_save_failure_uploads_nothing(self):
        self.store.fail_save = True
        with self.assertRaises(module.GitMeasurementError) as caught:
            await self.writer.export(measurement(), version="0.1.14")
        self.assertNotIn("PRIVATE TOKEN", str(caught.exception))
        self.assertEqual(self.session.requests, [])

    async def test_invalid_remote_commit_confirmation_keeps_pending(self):
        self.session.response = FakeResponse(201, {"commit": {"sha": "INVALID"}})
        with self.assertRaises(module.GitMeasurementError):
            await self.writer.export(measurement(), version="0.1.14")
        self.assertTrue(self.writer.pending)

    def test_archive_path_example_and_version(self):
        now = datetime(2026, 10, 9, 11, 0, tzinfo=timezone.utc)
        doc = module.archive_document(
            measurement(), version="0.1.14", now=now,
            export_id="f"*32, source_commit="b"*40,
        )
        path = module.archive_path(doc)
        self.assertEqual(path, (
            "exports/deploy-relay-agent-v2/2026-10/diagnostics/"
            "2026-10-09T11-00-00Z__deploy-relay-agent-v2__0.1.14__diagnostics__"
            + "f"*32 + ".json"
        ))
        self.assertEqual(doc["source"]["commit"], "b"*40)


if __name__ == "__main__":
    unittest.main()
