"""Actual V2 public GitHub preflight through mocked HTTPS and local read-only files."""
from __future__ import annotations

import base64
import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_source_remote_test"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(ROOT)]
sys.modules[PKG] = pkg
m = importlib.import_module(f"{PKG}.remote_source")
p = importlib.import_module(f"{PKG}.source_preflight")
REPO = "TheDaimos/safe-repo"
COMMIT = "a" * 40
TREE = "b" * 40


class Content:
    def __init__(self, data): self.data = data
    async def read(self, limit): return self.data[:limit]


class Response:
    def __init__(self, data, status=200):
        self.content = Content(json.dumps(data).encode("utf-8"))
        self.headers = {"Content-Length": str(len(self.content.data))}
        self.status = status
    async def __aenter__(self): return self
    async def __aexit__(self, typ, val, tb): return False


class Session:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if not self.replies:
            raise AssertionError("unexpected GitHub request")
        result = self.replies.pop(0)
        if isinstance(result, Exception): raise result
        return Response(*result) if isinstance(result, tuple) else Response(result)


def manifest():
    return json.dumps({
        "schema": "deploy-relay.deployment.v1",
        "project": {"id": "safe_project", "name": "Safe Project"},
        "source": {"repository": REPO, "mode": "repository_contents"},
        "deployment": {"root": "/config", "groups": [
            {"id": "project", "source": "custom_components/safe_project",
             "target": "custom_components/safe_project",
             "mode": "replace_directory"},
        ]},
        "lifecycle": {"after_install": "home_assistant_restart"},
        "policy": {"allow_symlinks": False, "max_files": 100,
                   "max_uncompressed_bytes": 4096},
    }).encode()


def file(path, content):
    return {"path": path, "type": "blob", "mode": "100644", "size": len(content),
            "sha": p.git_blob_sha(content)}


def payloads(*, tree_files=None, truncated=False, content=None):
    payload = content if content is not None else manifest()
    entries = tree_files if tree_files is not None else [
        file("custom_components/safe_project/one.py", b"new")
    ]
    return [
        {"default_branch": "deploy/dev", "archived": False, "disabled": False},
        {"sha": COMMIT, "commit": {"tree": {"sha": TREE}}},
        {"encoding": "base64",
         "content": base64.b64encode(payload).decode("ascii"),
         "size": len(payload),
         "sha": p.git_blob_sha(payload)},
        {"truncated": truncated, "tree": entries},
    ]


class SourceRemoteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addAsyncCleanup(self._close)
        self.root = Path(self.temp.name)
        (self.root / "custom_components" / "safe_project").mkdir(parents=True)

    async def _close(self):
        self.temp.cleanup()

    async def test_actual_preview_identifies_changes_without_touching_files(self):
        local = self.root / "custom_components" / "safe_project"
        (local / "one.py").write_bytes(b"old")
        (local / "retired.py").write_bytes(b"retired")
        before = (local / "one.py").read_bytes()
        session = Session(payloads())
        report = await m.inspect_public_repository(session, self.root, REPO)
        self.assertEqual(report["source_commit"], COMMIT)
        self.assertEqual(report["source_ref"], "deploy/dev")
        self.assertEqual(report["change"], ["custom_components/safe_project/one.py"])
        self.assertEqual(report["remove"], ["custom_components/safe_project/retired.py"])
        self.assertEqual(report["add"], [])
        self.assertIs(report["installation_enabled"], False)
        self.assertIs(report["handover_required"], True)
        self.assertIs(report["backup_verified"], False)
        self.assertEqual((local / "one.py").read_bytes(), before)
        self.assertTrue(all(url.startswith("https://api.github.com/repos/") for url, _ in session.calls))
        self.assertTrue(all(kwargs["allow_redirects"] is False for _, kwargs in session.calls))
        self.assertTrue(all("Authorization" not in kwargs["headers"] for _, kwargs in session.calls))
        self.assertTrue(any("/contents/deploy-relay.json?ref=" + COMMIT in url for url, _ in session.calls))

    async def test_missing_project_directory_is_no_local_files(self):
        session = Session(payloads())
        report = await m.inspect_public_repository(session, self.root, REPO)
        self.assertEqual(report["add"], ["custom_components/safe_project/one.py"])

    async def test_explicit_branch_name_is_encoded_but_pinned(self):
        session = Session(payloads())
        report = await m.inspect_public_repository(session, self.root, REPO, "feature/dev")
        self.assertEqual(report["source_ref"], "feature/dev")
        self.assertIn("/commits/feature%2Fdev", session.calls[1][0])

    async def test_cannot_preview_untrusted_symlink_target(self):
        outside = self.root / "private.txt"
        outside.write_text("PRIVATE DATA")
        folder = self.root / "custom_components" / "safe_project"
        (folder / "secret.py").symlink_to(outside)
        session = Session(payloads())
        with self.assertRaises(p.PreflightError):
            await m.inspect_public_repository(session, self.root, REPO)
        self.assertEqual(outside.read_text(), "PRIVATE DATA")

    async def test_ref_validation_rejects_url_or_query_injection(self):
        for ref in ("https://elsewhere.invalid", "../../main", "main?x=a", "refs@{0}",
                    "feature\\secret", "//evil", "main "):
            with self.subTest(ref=ref), self.assertRaises(p.PreflightError):
                await m.inspect_public_repository(Session([]), self.root, REPO, ref)

    async def test_broken_source_never_claims_available(self):
        cases = [
            (payloads(truncated=True), "tree truncated"),
            (payloads(tree_files=[file("custom_components/safe_project/x", b"x"),
                                   {"path": "custom_components/safe_project/link",
                                    "type": "blob", "mode": "120000",
                                    "size": 4, "sha": p.git_blob_sha(b"evil")}]), "symlink"),
            ([{"default_branch": "deploy/dev"}, {"sha": "INVALID"}], "bad commit"),
            ([( {"default_branch": "deploy/dev"}, 404)], "not accessible"),
        ]
        for responses, label in cases:
            with self.subTest(label=label):
                with self.assertRaises(p.PreflightError):
                    await m.inspect_public_repository(Session(responses), self.root, REPO)

    async def test_oversized_file_is_never_scanned(self):
        path = self.root / "custom_components" / "safe_project" / "large.bin"
        path.write_bytes(b"a" * 5000)
        with self.assertRaises(p.PreflightError):
            await m.inspect_public_repository(Session(payloads()), self.root, REPO)


if __name__ == "__main__":
    unittest.main()
