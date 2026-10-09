"""Project registry isolation, opt-in migration and retention safety."""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path

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

    async def test_import_preview_does_not_write(self):
        v1 = v1_projects(("TheDaimos/weather-router-dev", "WeatherRouter", 10))
        preview = m.v1_proposals(v1)
        self.assertEqual(v1.queries, ["deploy_relay"])
        self.assertEqual(preview[0]["repository"], "TheDaimos/weather-router-dev")
        self.assertEqual(preview[0]["origin"], "v1_import")
        self.assertEqual(preview[0]["status"], "pending_review")
        self.assertEqual(self.store.writes, 0)
        self.assertNotIn("ghp_", str(preview))

    async def test_explicit_import_is_independent_idempotent_and_reloads(self):
        v1 = v1_projects(
            ("TheDaimos/weather-router-dev", "WeatherRouter", 17),
            ("TheDaimos/gewitterradar", "Gewitterradar", 10),
        )
        result = await self.catalog.import_v1(v1)
        self.assertEqual(result, {"added": 2, "already_present": 0})
        self.assertEqual(self.store.writes, 1)
        self.assertNotIn("PRIVATE", str(self.store.value))
        self.assertNotIn("selected_source_commit", str(self.store.value))
        self.assertNotIn("backup_path", str(self.store.value))
        self.assertEqual((await self.catalog.import_v1(v1))["added"], 0)
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
            ("evil.io/a", "Bad"),
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

    async def test_failed_store_write_leaves_current_memory_unchanged(self):
        self.store.fail = True
        with self.assertRaises(m.CatalogError):
            await self.catalog.add("TheDaimos/demo", "Demo")
        self.assertEqual(self.catalog.list(), [])
        self.assertEqual(self.store.writes, 0)

    async def test_corrupt_v1_entry_blocks_complete_import(self):
        v1 = v1_projects(("TheDaimos/a", "A", 10), ("TheDaimos/b", "B", 1))
        with self.assertRaises(m.CatalogError):
            await self.catalog.import_v1(v1)
        self.assertEqual(self.catalog.list(), [])
        self.assertEqual(self.store.writes, 0)

    async def test_catalog_limit_is_hard(self):
        for n in range(32):
            await self.catalog.add(f"TheDaimos/project-{n}", f"Project {n}")
        with self.assertRaises(m.CatalogError):
            await self.catalog.add("TheDaimos/another", "Another")


if __name__ == "__main__":
    unittest.main()
