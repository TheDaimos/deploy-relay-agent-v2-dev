"""Strict V2 read-only manifest, source tree and difference plan contracts."""
from __future__ import annotations

import importlib
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PACKAGE = "_v2_source_preflight_test"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = pkg
m = importlib.import_module(f"{PACKAGE}.source_preflight")

REPO = "TheDaimos/safe-repo"
SHA = "a" * 40


def manifest(groups=None, **changes):
    obj = {
        "schema": "deploy-relay.deployment.v1",
        "project": {"id": "safe_project", "name": "Safe Project"},
        "source": {"repository": REPO, "mode": "repository_contents"},
        "deployment": {
            "root": "/config",
            "groups": groups or [{"source": "custom_components/safe_project",
                                  "target": "custom_components/safe_project",
                                  "mode": "replace_directory"}],
        },
        "policy": {
            "allow_symlinks": False, "max_files": 100, "max_uncompressed_bytes": 4096,
        },
    }
    obj.update(changes)
    return json.dumps(obj).encode("utf-8")


def tree_item(path, content=b"x", *, mode="100644", kind="blob"):
    return {
        "path": path, "type": kind, "mode": mode,
        "size": len(content), "sha": m.git_blob_sha(content),
    }


class PurePreflightTests(unittest.TestCase):
    def test_parse_real_manifest_shape(self):
        obj = m.parse_manifest(manifest(), repository=REPO)
        self.assertEqual(obj["project_id"], "safe_project")
        self.assertEqual(obj["groups"][0]["target"], "custom_components/safe_project")

    def test_rejects_untrusted_target_before_scanning(self):
        for target in ("custom_components/deploy_relay",
                       "custom_components/deploy_relay_v2_dev",
                       ".storage",
                       "secrets.yaml",
                       "www/something",
                       "custom_components/../evil",
                       "custom_components/safe_project/../evil",
                       r"custom_components\evil"):
            with self.subTest(target=target), self.assertRaises(m.PreflightError):
                m.parse_manifest(
                    manifest(groups=[{"source": "package", "target": target,
                                     "mode": "replace_directory"}]),
                    repository=REPO,
                )

    def test_wrong_owner_or_artifact_mode_never_approved(self):
        with self.assertRaises(m.PreflightError):
            m.parse_manifest(manifest(), repository="Another/safe-repo")
        obj = json.loads(manifest())
        obj["source"]["mode"] = "actions_artifact"
        with self.assertRaises(m.PreflightError):
            m.parse_manifest(json.dumps(obj).encode(), repository=REPO)

    def test_bounded_file_tree_and_diff(self):
        data = m.parse_manifest(manifest(), repository=REPO)
        prefix = "custom_components/safe_project/"
        files = m.inspect_tree(data, [
            tree_item(prefix + "old.py", b"new"),
            tree_item(prefix + "added.py", b"added"),
            {"path": "docs", "type": "tree", "mode": "040000"},
        ])
        local = {
            prefix + "old.py": m.git_blob_sha(b"old"),
            prefix + "retired.py": m.git_blob_sha(b"retired"),
        }
        report = m.compare_blobs(data, files, local, source_commit=SHA)
        self.assertEqual(report["add"], [prefix + "added.py"])
        self.assertEqual(report["change"], [prefix + "old.py"])
        self.assertEqual(report["remove"], [prefix + "retired.py"])
        self.assertEqual(report["unchanged_count"], 0)
        self.assertIs(report["installation_enabled"], False)
        self.assertIs(report["handover_required"], True)

    def test_symlinks_submodules_or_truncation_never_pass(self):
        data = m.parse_manifest(manifest(), repository=REPO)
        path = "custom_components/safe_project/p.py"
        for mode, kind in [("120000", "blob"), ("160000", "commit"),
                           ("100644", "tree")]:
            with self.subTest(mode=mode), self.assertRaises(m.PreflightError):
                m.inspect_tree(data, [tree_item(path, mode=mode, kind=kind)])
        with self.assertRaises(m.PreflightError):
            m.inspect_tree(data, [tree_item(path)] * 2)
        with self.assertRaises(m.PreflightError):
            m.inspect_tree(data, [])

    def test_no_implicit_treat_unknown_as_current(self):
        data = m.parse_manifest(manifest(), repository=REPO)
        for bad in (
            {"not/ours.py": SHA},
            {"custom_components/safe_project/one": "invalid"},
        ):
            with self.assertRaises(m.PreflightError):
                m.compare_blobs(data, [], bad, source_commit=SHA)
        with self.assertRaises(m.PreflightError):
            m.compare_blobs(data, [], {}, source_commit="main")

    def test_reject_excess_manifest_resource_policy_and_schema(self):
        for mutation in (
            lambda x: x["policy"].update({"max_files": 10000}),
            lambda x: x["policy"].update({"allow_symlinks": True}),
            lambda x: x.update({"schema": "unknown"}),
            lambda x: x["deployment"].update({"root": "/tmp"}),
        ):
            obj = json.loads(manifest())
            mutation(obj)
            with self.assertRaises(m.PreflightError):
                m.parse_manifest(json.dumps(obj).encode(), repository=REPO)

    def test_generated_git_blob_hash_has_canonical_format(self):
        self.assertEqual(m.git_blob_sha(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")


if __name__ == "__main__":
    unittest.main()
