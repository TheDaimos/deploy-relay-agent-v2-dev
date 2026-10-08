"""Public DRA V2 baseline smoke and release-boundary contracts.

Only stdlib; no Home Assistant runtime or live credentials required.
"""

import ast
import hashlib
import json
import re
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
            ".storage", ".weather-router", "backups",
            "config", "logs", "secrets.yaml", ".env", "hacs.json",
        )
        for name in forbidden:
            self.assertFalse((ROOT / name).exists(), name)
        # A public development source is not an installable HACS release.
        self.assertTrue((ROOT / "docs" / "PUBLIC_DEVELOPMENT_POLICY.md").is_file())
        self.assertTrue((ROOT / "docs" / "SOURCE_PROVENANCE.md").is_file())


    def test_public_git_diagnostics_only_contain_strict_measurement_data(self) -> None:
        """Do not reject safe Git exports, but fail closed on other runtime payloads."""
        root = ROOT / ".deploy-relay"
        if not root.exists():
            return
        self.assertTrue(root.is_dir())
        self.assertFalse(root.is_symlink())
        allowed_dirs = re.compile(
            r"diagnostics(?:/v2-dev(?:/\d{4}-\d{2}-\d{2})?)?\Z"
        )
        allowed_file = re.compile(
            r"diagnostics/v2-dev/(\d{4}-\d{2}-\d{2})/"
            r"(\d{8}T\d{6}Z)-[0-9a-f]{8}\.json\Z"
        )
        records = []
        for node in root.rglob("*"):
            self.assertFalse(node.is_symlink(), str(node))
            rel = node.relative_to(root).as_posix()
            if node.is_dir():
                self.assertRegex(rel, allowed_dirs)
                continue
            self.assertTrue(node.is_file(), rel)
            match = allowed_file.fullmatch(rel)
            self.assertIsNotNone(match, rel)
            self.assertLessEqual(node.stat().st_size, 4096)
            records.append(node)
            payload = json.loads(node.read_text("utf-8"))
            self.assertEqual(
                set(payload),
                {"branch", "path", "repository", "schema", "snapshot"},
            )
            self.assertEqual(payload["branch"], "main")
            self.assertEqual(payload["repository"], "TheDaimos/deploy-relay-agent-v2-dev")
            self.assertEqual(payload["path"], ".deploy-relay/" + rel)
            self.assertEqual(payload["schema"], "dra-v2-dev-git-measurement.v1")
            snapshot = payload["snapshot"]
            self.assertEqual(
                set(snapshot),
                {"component", "created_at", "measurement", "mode",
                 "note", "schema", "version"},
            )
            self.assertEqual(snapshot["component"], "deploy_relay_v2_dev")
            self.assertEqual(snapshot["mode"], "READ_ONLY_TEST")
            self.assertEqual(snapshot["schema"], "dra-v2-dev-git-measurement.v1")
            self.assertRegex(snapshot["version"], r"\A0\.1\.\d{1,3}\Z")
            self.assertEqual(
                snapshot["note"],
                "Synthetic workload. CPU measured across the whole HA process, not DRA alone.",
            )
            self.assertRegex(
                snapshot["created_at"], r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z"
            )
            self.assertEqual(snapshot["created_at"].replace(":", "").replace("-", ""), match[2])
            self.assertEqual(snapshot["created_at"][:10], match[1])
            measurement = snapshot["measurement"]
            caps = {
                "base_process_cpu_ms": 3600000,
                "work_process_cpu_ms": 3600000,
                "after_process_cpu_ms": 3600000,
                "max_wakeup_delay_ms": 60000,
                "elapsed_ms": 3600000,
                "synthetic_hashes": 640,
            }
            self.assertEqual(
                set(measurement),
                {"scope", "base_seconds", "work_seconds", "after_seconds", *caps},
            )
            self.assertEqual(
                measurement["scope"], "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY"
            )
            for field, expected in (
                ("base_seconds", 10), ("work_seconds", 20),
                ("after_seconds", 10),
            ):
                self.assertIs(type(measurement[field]), int)
                self.assertEqual(measurement[field], expected)
            for field, maximum in caps.items():
                value = measurement[field]
                self.assertIs(type(value), int)
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, maximum)
        self.assertTrue(records, "Unrecognized or empty .deploy-relay folder")
        self.assertLessEqual(len(records), 128, "Unbounded public Git diagnostics")


if __name__ == "__main__":
    unittest.main()
