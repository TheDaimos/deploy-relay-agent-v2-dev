"""Project registry isolation, opt-in migration and retention safety."""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_project_test"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package
m = importlib.import_module(f"{PKG}.project_catalog")


class Store:
    def __init__(self, initial=None):
        self.value = initial
        self.writes = 0
        self.fail = False

    async def async_load(self):
        return self.value

    async def async_save(self, value):
        if self.fail:
            raise OSError("private location")
        self.value = value
        self.writes += 1


def v1_projects(*projects):
    entries = [
        types.SimpleNamespace(
            subentries={
                str(i): types.SimpleNamespace(
                    subentry_type="project",
                    title=name,
                    data={
                        "repository": repo,
                        "backup_retention": retention,
                        "github_token": "ghp_PRIVATE_DO_NOT_COPY",
                        "selected_source_commit": "f"*40,
                        "backup_path": "/config/deploy_relay/backups",
                    },
                ) for i, (repo, name, retention) in enumerate(projects)
            },
        )
    ]
    class Entries:
        def __init__(self): self.queries = []
        def async_entries(self, domain):
            self.queries.append(domain)
            return entries
    return Entries()


class V2ProjectCatalogTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store = Store()
        self.catalog = m.ProjectCatalog(self.store)
        await self.catalog.load()

    async def test_sammelupdate_picker_position_is_persisted_independently(self):
        for name in ("alpha", "beta", "gamma"):
            await self.catalog.add(f"TheDaimos/{name}", name)
        original = self.catalog.list()
        self.assertEqual(self.catalog.picker_batch_position, 3)
        self.assertEqual(self.store.value["picker_batch_position"], 3)
        for i in (2, 1, 0):
            self.assertEqual(await self.catalog.move_picker_batch(-1), i)
            self.assertEqual(self.catalog.list(), original)
            self.assertEqual(self.store.value["picker_batch_position"], i)
        with self.assertRaises(m.CatalogError):
            await self.catalog.move_picker_batch(-1)
        await self.catalog.move("TheDaimos/alpha", 1)
        self.assertEqual(self.catalog.picker_batch_position, 0)
        self.assertEqual([p["repository"] for p in self.catalog.list()],
                         ["TheDaimos/beta", "TheDaimos/alpha", "TheDaimos/gamma"])
        reloaded = m.ProjectCatalog(self.store)
        await reloaded.load()
        self.assertEqual(reloaded.picker_batch_position, 0)
        self.assertEqual(reloaded.list(), self.catalog.list())
        await reloaded.add("TheDaimos/delta", "delta")
        self.assertEqual(reloaded.picker_batch_position, 0)
        with self.assertRaises(m.CatalogError):
            await reloaded.move_picker_batch(True)
        with self.assertRaises(m.CatalogError):
            await reloaded.move_picker_batch(2)

    async def test_sammelupdate_legacy_catalog_and_storage_failure_are_safe(self):
        record = m.proposal("TheDaimos/alpha", "Alpha", origin="manual")
        legacy = Store({"schema":m.SCHEMA,"projects":[record]})
        catalog = m.ProjectCatalog(legacy)
        await catalog.load()
        self.assertEqual(catalog.picker_batch_position, 1)
        legacy.fail = True
        with self.assertRaises(m.CatalogError):
            await catalog.move_picker_batch(-1)
        self.assertEqual(catalog.picker_batch_position, 1)
        self.assertEqual(legacy.writes, 0)
        for value in (-1, 2, True, "0"):
            storage = Store({"schema":m.SCHEMA,"projects":[record],
                             "picker_batch_position":value})
            with self.assertRaises(m.CatalogError):
                await m.ProjectCatalog(storage).load()

    async def test_import_preview_does_not_write(self):
        v1 = v1_projects(("TheDaimos/weather-router-dev", "WeatherRouter", 10))
        preview = m.v1_proposals(v1)
        self.assertEqual(v1.queries, ["deploy_relay"])
        self.assertEqual(preview[0]["repository"], "TheDaimos/weather-router-dev")
        self.assertEqual(preview[0]["origin"], "v1_import")
        self.assertEqual(preview[0]["status"], "pending_review")
        self.assertEqual(self.store.writes, 0)
        self.assertNotIn("ghp_", str(preview))

    async def test_v1_readonly_mapping_views_are_accepted(self):
        from types import MappingProxyType
        v1 = v1_projects(("TheDaimos/aurora", "Aurora", 10))
        class FrozenEntries:
            def async_entries(self, domain):
                entries = v1.async_entries(domain)
                for entry in entries:
                    entry.subentries = MappingProxyType(entry.subentries)
                    for sub in entry.subentries.values():
                        sub.data = MappingProxyType(sub.data)
                return entries
        rows = m.v1_proposals(FrozenEntries())
        self.assertEqual(len(rows), 1)
        self.assertNotIn("PRIVATE", str(rows))

    async def test_explicit_import_is_independent_idempotent_and_reloads(self):
        v1 = v1_projects(
            ("TheDaimos/weather-router-dev", "WeatherRouter", 17),
            ("TheDaimos/gewitterradar", "Gewitterradar", 10),
        )
        result = await self.catalog.import_v1(v1, [p["repository"] for p in m.v1_proposals(v1)])
        self.assertEqual(result, {"added": 2, "already_present": 0})
        self.assertEqual(self.store.writes, 1)
        self.assertNotIn("PRIVATE", str(self.store.value))
        self.assertNotIn("selected_source_commit", str(self.store.value))
        self.assertNotIn("backup_path", str(self.store.value))
        self.assertEqual((await self.catalog.import_v1(v1, [p["repository"] for p in m.v1_proposals(v1)]))["added"], 0)
        self.assertEqual(self.store.writes, 1)
        new = m.ProjectCatalog(self.store)
        await new.load()
        self.assertEqual(len(new.list()), 2)
        self.assertEqual(next(x for x in new.list() if x["name"] == "WeatherRouter")["backup_retention"], 17)

    async def test_add_valid_project_and_retention(self):
        row = await self.catalog.add("https://github.com/TheDaimos/aurora-borealis-dev",
                                     "Aurora Borealis")
        self.assertEqual(row["project_id"], "aurora_borealis_dev")
        self.assertEqual(row["backup_retention"], 10)
        row = await self.catalog.set_retention(row["repository"], 30)
        self.assertEqual(row["backup_retention"], 30)
        self.assertEqual(self.catalog.list()[0]["status"], "pending_review")

    async def test_duplicate_case_insensitive(self):
        await self.catalog.add("TheDaimos/project-dev", "")
        with self.assertRaises(m.CatalogError):
            await self.catalog.add("thedaimos/PROJECT-dev", "Duplicate")

    async def test_invalid_projects_cannot_persist(self):
        bad = [
            ("https://evil.io/a", "Bad"),
            ("http://github.com/a/b", "Bad"),
            ("TheDaimos/../../bad", "Bad"),
            ("TheDaimos/evil", "<script>"),
            ("TheDaimos/even", "control\nname"),
        ]
        for repo, name in bad:
            with self.subTest(repo=repo):
                with self.assertRaises(m.CatalogError):
                    await self.catalog.add(repo, name)
        self.assertEqual(self.store.writes, 0)

    async def test_different_owners_cannot_share_backup_identity(self):
        await self.catalog.add("TheDaimos/weather-router", "WeatherRouter")
        with self.assertRaises(m.CatalogError):
            await self.catalog.add("OtherOwner/weather-router", "Other")
        self.assertEqual(len(self.catalog.list()), 1)

    async def test_retention_range_min_max_and_bool(self):
        await self.catalog.add("TheDaimos/test", "Test")
        for value in (-1, 0, 2, 101, True, "10"):
            with self.subTest(value=value):
                with self.assertRaises(m.CatalogError):
                    await self.catalog.set_retention("TheDaimos/test", value)
        await self.catalog.set_retention("TheDaimos/test", 3)
        await self.catalog.set_retention("TheDaimos/test", 100)

    async def test_fail_closed_on_unknown_schema_and_duplicate(self):
        s = Store({"schema": "unexpected", "projects": []})
        with self.assertRaises(m.CatalogError):
            await m.ProjectCatalog(s).load()
        sample = m.proposal("TheDaimos/a", "A", origin="manual")
        s = Store({"schema": m.SCHEMA, "projects": [sample, dict(sample)]})
        with self.assertRaises(m.CatalogError):
            await m.ProjectCatalog(s).load()

    async def test_import_selection_only_imports_selected_and_rejects_unknown(self):
        v1 = v1_projects(("TheDaimos/weather-router-dev", "WeatherRouter", 10),
                         ("TheDaimos/gewitterradar", "Gewitterradar", 10))
        self.assertEqual((await self.catalog.import_v1(v1, ["TheDaimos/gewitterradar"]))["added"], 1)
        self.assertEqual([x["repository"] for x in self.catalog.list()], ["TheDaimos/gewitterradar"])
        with self.assertRaises(m.CatalogError):
            await self.catalog.import_v1(v1, ["TheDaimos/unlisted"])
        with self.assertRaises(m.CatalogError):
            await self.catalog.import_v1(v1, ["TheDaimos/gewitterradar", "TheDaimos/gewitterradar"])

    async def test_failed_store_write_leaves_current_memory_unchanged(self):
        self.store.fail = True
        with self.assertRaises(m.CatalogError):
            await self.catalog.add("TheDaimos/demo", "Demo")
        self.assertEqual(self.catalog.list(), [])
        self.assertEqual(self.store.writes, 0)

    async def test_corrupt_v1_entry_blocks_complete_import(self):
        v1 = v1_projects(("TheDaimos/a", "A", 10), ("TheDaimos/b", "B", 1))
        with self.assertRaises(m.CatalogError):
            await self.catalog.import_v1(v1, [p["repository"] for p in m.v1_proposals(v1)])
        self.assertEqual(self.catalog.list(), [])
        self.assertEqual(self.store.writes, 0)

    async def test_batch_preselection_roundtrip_and_legacy_default(self):
        original = await self.catalog.add("TheDaimos/gewitterradar", "Gewitterradar")
        self.assertIs(original["batch_preselect"], True)
        changed = await self.catalog.set_batch_preselect(original["repository"], False)
        self.assertIs(changed["batch_preselect"], False)
        reread = m.ProjectCatalog(self.store)
        await reread.load()
        self.assertIs(reread.list()[0]["batch_preselect"], False)
        legacy = dict(m.proposal("TheDaimos/legacy", "Legacy", origin="manual"))
        legacy.pop("batch_preselect")
        old = m.ProjectCatalog(Store({"schema": m.SCHEMA, "projects": [legacy]}))
        await old.load()
        self.assertIs(old.list()[0]["batch_preselect"], True)

    async def test_batch_only_accepts_exact_registered_repositories(self):
        await self.catalog.add("TheDaimos/one", "One")
        await self.catalog.add("TheDaimos/two", "Two")
        self.assertIs((await self.catalog.set_batch_preselect("TheDaimos/two", False))["batch_preselect"], False)
        prev = self.catalog.batch_preview(["TheDaimos/one", "TheDaimos/two"])
        self.assertEqual([r["repository"] for r in prev["selected"]],
                         ["TheDaimos/one", "TheDaimos/two"])
        self.assertEqual([r["status"] for r in prev["selected"]],
                         ["not_checked", "not_checked"])
        self.assertIs(prev["installation_enabled"], False)
        self.assertIs(prev["sources_verified"], False)
        for bad in (["TheDaimos/unknown"], ["TheDaimos/one", "thedaimos/ONE"],
                    ["TheDaimos/one", None], "TheDaimos/one", [True]):
            with self.subTest(bad=bad), self.assertRaises(m.CatalogError):
                self.catalog.batch_preview(bad)
        self.assertEqual(len(self.catalog.list()), 2)

    async def test_preselection_invalid_value_does_not_change_state(self):
        await self.catalog.add("TheDaimos/a", "A")
        for value in (1, 0, "false", None):
            with self.assertRaises(m.CatalogError):
                await self.catalog.set_batch_preselect("TheDaimos/a", value)
        self.assertIs(self.catalog.list()[0]["batch_preselect"], True)

    async def test_project_order_activation_notes_and_removal_are_persistent(self):
        await self.catalog.add("TheDaimos/one", "One", "Read-Only", True)
        await self.catalog.add("TheDaimos/two", "Two", "", True)
        await self.catalog.move("TheDaimos/two", -1)
        self.assertEqual([p["repository"] for p in self.catalog.list()],
                         ["TheDaimos/two", "TheDaimos/one"])
        await self.catalog.configure("TheDaimos/two", "TheDaimos/two", "Two",
                                     "Temporarily disabled", False)
        self.assertEqual(self.catalog.list()[0]["note"], "Temporarily disabled")
        self.assertIs(self.catalog.list()[0]["active"], False)
        with self.assertRaises(m.CatalogError):
            self.catalog.batch_preview(["TheDaimos/two"])
        saved = m.ProjectCatalog(self.store)
        await saved.load()
        self.assertEqual(saved.list()[0]["repository"], "TheDaimos/two")
        self.assertIs(saved.list()[0]["active"], False)
        await saved.remove("TheDaimos/two")
        self.assertEqual(len(saved.list()), 1)
        self.assertEqual(saved.list()[0]["repository"], "TheDaimos/one")

    async def test_project_update_rejects_duplicate_repositories_and_invalid_notes(self):
        await self.catalog.add("TheDaimos/one", "One")
        await self.catalog.add("TheDaimos/two", "Two")
        with self.assertRaises(m.CatalogError):
            await self.catalog.configure("TheDaimos/one", "TheDaimos/two", "One", "", True)
        with self.assertRaises(m.CatalogError):
            await self.catalog.configure("TheDaimos/one", "TheDaimos/one", "One", chr(0), True)
        self.assertEqual(len(self.catalog.list()), 2)

    async def test_access_mode_is_operator_metadata_and_roundtrips(self):
        await self.catalog.add("TheDaimos/access", "Access", access_mode="read_write")
        self.assertEqual(self.catalog.list()[0]["access_mode"], "read_write")
        await self.catalog.configure("TheDaimos/access", "TheDaimos/access",
                                     "Access", "Notes", True, "read_only")
        self.assertEqual(self.catalog.list()[0]["access_mode"], "read_only")
        restored = m.ProjectCatalog(self.store)
        await restored.load()
        self.assertEqual(restored.list()[0]["access_mode"], "read_only")
        with self.assertRaises(m.CatalogError):
            await self.catalog.configure("TheDaimos/access", "TheDaimos/access",
                                         "Access", "", True, "admin_all")
        self.assertEqual(self.catalog.list()[0]["access_mode"], "read_only")

    async def test_catalog_limit_is_hard(self):
        for n in range(32):
            await self.catalog.add(f"TheDaimos/project-{n}", f"Project {n}")
        with self.assertRaises(m.CatalogError):
            await self.catalog.add("TheDaimos/another", "Another")


class V2ProjectCredentialsTests(unittest.IsolatedAsyncioTestCase):
    async def test_token_is_separate_and_only_suffix_is_exposed(self):
        remote = importlib.import_module(f"{PKG}.remote_source")
        store = Store()
        credentials = remote.ProjectReadAuth(store)
        await credentials.load()
        secret = "github_pat_ABCdef1234567890"
        await credentials.save("TheDaimos/one", secret)
        self.assertEqual(credentials.status("TheDaimos/one"),
                         {"configured":True, "suffix":"67890"})
        self.assertNotIn(secret, str(credentials.status("TheDaimos/one")))
        self.assertIsNone(credentials.token("TheDaimos/two"))
        reloaded = remote.ProjectReadAuth(store)
        await reloaded.load()
        self.assertEqual(reloaded.token("TheDaimos/one"), secret)
        await reloaded.rename("TheDaimos/one", "TheDaimos/renamed")
        self.assertIsNone(reloaded.token("TheDaimos/one"))
        self.assertEqual(reloaded.token("TheDaimos/renamed"), secret)
        await reloaded.delete("TheDaimos/renamed")
        self.assertEqual(reloaded.status("TheDaimos/renamed")["configured"], False)

class V2GitConnectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_is_manifest_independent_and_never_writes(self):
        remote = importlib.import_module(f"{PKG}.remote_source")
        get = AsyncMock(return_value={
            "full_name":"TheDaimos/private-example", "private":True,
            "permissions":{"pull":True,"push":False}
        })
        with patch.object(remote, "_get", get):
            result = await remote.inspect_repository_connection(object(),
                "TheDaimos/private-example", token="github_pat_1234567890123456")
        self.assertIs(result["connected"], True)
        self.assertIs(result["private"], True)
        self.assertIs(result["advertised_push"], False)
        self.assertIs(result["write_tested"], False)
        self.assertEqual(get.await_count, 1)
        self.assertIn("/repos/TheDaimos/private-example", get.await_args.args[1])
        self.assertNotIn("deploy-relay.json", str(get.await_args))

    async def test_connection_rejects_mismatched_repository(self):
        remote = importlib.import_module(f"{PKG}.remote_source")
        get = AsyncMock(return_value={"full_name":"Other/repo", "private":False})
        with patch.object(remote, "_get", get):
            with self.assertRaises(remote.PreflightError):
                await remote.inspect_repository_connection(object(), "TheDaimos/repo")


if __name__ == "__main__":
    unittest.main()
