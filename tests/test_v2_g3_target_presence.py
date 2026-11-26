"""G3-10: synthetic-filesystem tests for a never-authorizing presence probe."""
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_g3_presence_tests"
module = types.ModuleType(PKG)
module.__path__ = [str(ROOT)]
sys.modules.setdefault(PKG, module)
presence = importlib.import_module(f"{PKG}.target_presence")


def target(name):
    return f"custom_components/{name}"


class G3PresenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "ha_config"
        self.components = self.root / "custom_components"
        self.components.mkdir(parents=True)

    def scan(self, *names):
        return presence.observe_target_presence(self.root, [target(n) for n in names])

    def test_present_and_absent_are_both_not_owned(self):
        (self.components / "gewitterradar").mkdir()
        result = self.scan("gewitterradar", "aurora")
        self.assertEqual(result["schema"], presence.SCHEMA)
        self.assertEqual(result["target_count"], 2)
        self.assertEqual([x["presence"] for x in result["targets"]],
                         ["present", "absent"])
        for item in result["targets"]:
            self.assertEqual(item["ownership"], "unverified")
        self.assertFalse(result["owner_identity_verified"])
        self.assertFalse(result["v1_handover_verified"])
        self.assertFalse(result["cross_process_lock_verified"])
        self.assertFalse(result["source_binding_verified"])
        self.assertFalse(result["backup_verified"])
        self.assertFalse(result["installation_enabled"])
        self.assertFalse(result["parallel_installation_enabled"])
        self.assertTrue(result["handover_required"])
        self.assertIn("+00:00", result["observed_at"])

    def test_ambiguous_case_variants_never_count_as_free(self):
        (self.components / "Radar").mkdir()
        (self.components / "radar").mkdir()
        self.assertEqual(self.scan("radar")["targets"][0]["presence"], "ambiguous")

    def test_symlink_and_regular_file_target_are_unsafe(self):
        (self.components / "normal_file").write_text("unchanged", encoding="utf-8")
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.components / "linked").symlink_to(outside, target_is_directory=True)
        result = self.scan("normal_file", "linked")
        self.assertEqual([x["presence"] for x in result["targets"]],
                         ["unsafe", "unsafe"])
        self.assertEqual((self.components / "normal_file").read_text(encoding="utf-8"),
                         "unchanged")
        self.assertTrue((self.components / "linked").is_symlink())
        self.assertFalse(result["installation_enabled"])

    def test_parent_symlink_does_not_follow(self):
        other = Path(self.temp.name) / "real_components"
        other.mkdir()
        self.components.rmdir()
        self.components.symlink_to(other, target_is_directory=True)
        with self.assertRaises(presence.TargetPresenceError):
            self.scan("gewitterradar")

    def test_root_symlink_does_not_follow(self):
        linked_root = Path(self.temp.name) / "linked_root"
        linked_root.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(presence.TargetPresenceError):
            presence.observe_target_presence(linked_root, [target("foo")])

    def test_missing_parent_or_invalid_root_fails_closed(self):
        self.components.rmdir()
        for source in (self.root, None, ""):
            with self.subTest(source=source), self.assertRaises(presence.TargetPresenceError):
                presence.observe_target_presence(source, [target("foo")])

    def test_casefold_duplicate_or_unsafe_targets_are_rejected(self):
        samples = (
            [], None, "custom_components/foo",
            [target("foo"), target("FOO")],
            [target("deploy_relay")],
            [target("deploy_relay_v2_dev")],
            ["secrets.yaml"], ["custom_components/../secret"],
            [target("foo")] * 33,
        )
        for targets in samples:
            with self.subTest(targets=targets), self.assertRaises(
                    presence.TargetPresenceError):
                presence.observe_target_presence(self.root, targets)

    def test_large_directory_fails_closed_before_target_stat(self):
        with patch.object(presence.os, "listdir",
                          return_value=["dummy"] * (presence.MAX_DIRECTORY_ENTRIES + 1)):
            with self.assertRaises(presence.TargetPresenceError):
                self.scan("target")

    def test_unavailable_target_stat_does_not_appear_absent(self):
        (self.components / "foo").mkdir()
        original = presence.os.stat
        def fail_foo(name, *, dir_fd=None, follow_symlinks=True):
            if name == "foo":
                raise OSError("race / vanished")
            return original(name, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        with patch.object(presence.os, "stat", side_effect=fail_foo):
            result = self.scan("foo")
        self.assertEqual(result["targets"][0]["presence"], "unavailable")
        self.assertFalse(result["installation_enabled"])

    def test_does_not_read_project_or_v1_private_file_contents(self):
        (self.components / "foo").mkdir()
        (self.components / "foo" / "secret.txt").write_text("private", encoding="utf-8")
        with patch("builtins.open", side_effect=AssertionError("opened file contents")):
            result = self.scan("foo")
        self.assertEqual(result["targets"][0]["presence"], "present")
        self.assertNotIn("secret", str(result))
        self.assertTrue((self.components / "foo" / "secret.txt").is_file())


if __name__ == "__main__":
    unittest.main()
