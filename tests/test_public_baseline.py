"""Public DRA V2 baseline smoke and release-boundary contracts.

Only stdlib; no Home Assistant runtime or live credentials required.
"""

import ast
import hashlib
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "deploy_relay"


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class PublicBaselineContracts(unittest.TestCase):
    def test_integration_manifest_is_valid(self) -> None:
        manifest = json.loads((INTEGRATION / "manifest.json").read_text("utf-8"))
        self.assertEqual(manifest["domain"], "deploy_relay")
        self.assertEqual(manifest["name"], "Deploy Relay Agent")
        self.assertTrue(manifest["config_flow"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertTrue(manifest["version"])

    def test_translation_files_and_manifest_are_valid_json(self) -> None:
        paths = [INTEGRATION / "manifest.json", INTEGRATION / "strings.json"]
        paths.extend((INTEGRATION / "translations").glob("*.json"))
        self.assertGreaterEqual(len(paths), 4)
        for path in paths:
            with self.subTest(path=path):
                self.assertIsInstance(json.loads(path.read_text("utf-8")), dict)

    def test_python_sources_parse(self) -> None:
        files = sorted(INTEGRATION.glob("*.py"))
        self.assertGreaterEqual(len(files), 20)
        for path in files:
            with self.subTest(path=path):
                ast.parse(path.read_text("utf-8"), filename=str(path))

    def test_original_official_icons_are_present(self) -> None:
        expected = {
            "icon.png": ((256, 256), "eca8b2a1261b4f60f26d9ba6d31c96c6e3c9f437"),
            "icon@2x.png": ((512, 512), "f1b2ae67b73d7bd408779e4e553f5c4452dc47b9"),
        }
        for name, (dimensions, git_sha) in expected.items():
            with self.subTest(name=name):
                data = (INTEGRATION / "brand" / name).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(data[12:16], b"IHDR")
                self.assertEqual(struct.unpack(">II", data[16:24]), dimensions)
                self.assertEqual(git_blob_sha(data), git_sha)

    def test_legal_materials_are_complete(self) -> None:
        for name in ("LICENSE", "COPYRIGHT.md", "BRANDING.md", "AUTHORS.md", "THIRD_PARTY.md"):
            self.assertTrue((ROOT / name).is_file(), name)
        self.assertIn("GNU GENERAL PUBLIC LICENSE", (ROOT / "LICENSE").read_text("utf-8"))

    def test_no_instance_specific_payloads(self) -> None:
        forbidden = (
            ".storage", ".deploy-relay", ".weather-router", "backups",
            "config", "logs", "secrets.yaml", ".env", "hacs.json",
        )
        for name in forbidden:
            self.assertFalse((ROOT / name).exists(), name)
        # A public development source is not an installable HACS release.
        self.assertTrue((ROOT / "docs" / "PUBLIC_DEVELOPMENT_POLICY.md").is_file())
        self.assertTrue((ROOT / "docs" / "SOURCE_PROVENANCE.md").is_file())


if __name__ == "__main__":
    unittest.main()
