"""Complete V2 backup metadata and byte-level integrity require exact coverage."""
from __future__ import annotations

import copy
import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_backup_integrity_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
m = importlib.import_module(f"{PKG}.backup_integrity")

PROJECT = "weather_router"
ROOT_NAME = "custom_components/weather_router"
FILES = {
    ROOT_NAME + "/__init__.py": b"component",
    ROOT_NAME + "/manifest.json": b'{"name":"WeatherRouter"}',
}


class BackupIntegrityContractTests(unittest.TestCase):
    def test_complete_independently_verified_backup_never_grants_restore(self):
        descriptor = m.create_complete_manifest(PROJECT, [ROOT_NAME], FILES)
        self.assertEqual(descriptor["schema"], m.SCHEMA)
        result = m.verify_complete_manifest(descriptor, FILES)
        self.assertEqual(result["file_count"], 2)
        self.assertTrue(result["verified"])
        self.assertFalse(result["restoration_enabled"])
        self.assertFalse(result["mutation_enabled"])

    def test_missing_and_extra_files_both_fail(self):
        descriptor = m.create_complete_manifest(PROJECT, [ROOT_NAME], FILES)
        changes = [
            {ROOT_NAME + "/__init__.py": FILES[ROOT_NAME + "/__init__.py"]},
            {**FILES, ROOT_NAME + "/extra": b"outside snapshot"},
            {**FILES, ROOT_NAME + "/manifest.json": b"corrupted"},
        ]
        for changed in changes:
            with self.subTest(data=changed), self.assertRaises(m.BackupIntegrityError):
                m.verify_complete_manifest(descriptor, changed)

    def test_never_allows_v1_or_v2_management_dir_or_sensitive_path(self):
        for bad in (
            "custom_components/deploy_relay",
            "custom_components/deploy_relay_v2_dev",
            ".storage",
            "secrets.yaml",
            "custom_components/../secrets",
        ):
            with self.subTest(path=bad), self.assertRaises(m.BackupIntegrityError):
                m.create_complete_manifest(PROJECT, [bad], {})

    def test_never_allows_unmanaged_or_duplicate_paths(self):
        with self.assertRaises(m.BackupIntegrityError):
            m.create_complete_manifest(PROJECT, [ROOT_NAME],
                                       {"custom_components/other/x": b"bad"})
        with self.assertRaises(m.BackupIntegrityError):
            m.create_complete_manifest(
                PROJECT, [ROOT_NAME],
                {ROOT_NAME + "/Camel.py": b"one", ROOT_NAME + "/camel.py": b"two"})
        with self.assertRaises(m.BackupIntegrityError):
            m.create_complete_manifest(PROJECT, [ROOT_NAME, ROOT_NAME], {})

    def test_metadata_cannot_self_certify_verification(self):
        descriptor = m.create_complete_manifest(PROJECT, [ROOT_NAME], FILES)
        for change in (
            ("complete_inventory_required", False),
            ("schema", "unknown"),
            ("total_bytes", 0),
        ):
            mutated = copy.deepcopy(descriptor)
            mutated[change[0]] = change[1]
            with self.subTest(change=change), self.assertRaises(m.BackupIntegrityError):
                m.verify_complete_manifest(mutated, FILES)
        mutated = copy.deepcopy(descriptor)
        mutated["files"][0]["sha256"] = "0" * 64
        with self.assertRaises(m.BackupIntegrityError):
            m.verify_complete_manifest(mutated, FILES)

    def test_empty_backup_must_still_verify_to_no_files(self):
        descriptor = m.create_complete_manifest(PROJECT, [ROOT_NAME], {})
        self.assertEqual(m.verify_complete_manifest(descriptor, {})["file_count"], 0)
        with self.assertRaises(m.BackupIntegrityError):
            m.verify_complete_manifest(descriptor, FILES)


if __name__ == "__main__":
    unittest.main()
