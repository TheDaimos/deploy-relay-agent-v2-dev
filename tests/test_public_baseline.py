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
            self.assertIn(payload["schema"], {
                "dra-v2-dev-git-measurement.v1",
                "dra-v2-dev-git-measurement.v2",
                "dra-v2-dev-git-suite.v1",
                "dra-v2-dev-git-suite.v2",
            })
            snapshot = payload["snapshot"]
            suite_file = payload["schema"] in {"dra-v2-dev-git-suite.v1", "dra-v2-dev-git-suite.v2"}
            self.assertEqual(
                set(snapshot),
                {"component", "created_at", "suite" if suite_file else "measurement", "mode",
                 "note", "schema", "version"},
            )
            self.assertEqual(snapshot["component"], "deploy_relay_v2_dev")
            self.assertEqual(snapshot["mode"], "READ_ONLY_TEST")
            self.assertEqual(snapshot["schema"], payload["schema"])
            self.assertRegex(snapshot["version"], r"\A0\.1\.\d{1,3}\Z")
            self.assertEqual(
                snapshot["note"],
                ("Synthetic subprocess comparison, not individual DRA CPU attribution."
                 if suite_file else
                 "Synthetic workload. CPU measured across the whole HA process, not DRA alone."),
            )
            self.assertRegex(
                snapshot["created_at"], r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z"
            )
            self.assertEqual(snapshot["created_at"].replace(":", "").replace("-", ""), match[2])
            self.assertEqual(snapshot["created_at"][:10], match[1])
            if suite_file:
                self._verify_public_suite(snapshot["suite"], payload["schema"])
                continue
            measurement = snapshot["measurement"]
            caps = {
                "base_process_cpu_ms": 3600000,
                "work_process_cpu_ms": 3600000,
                "after_process_cpu_ms": 3600000,
                "max_wakeup_delay_ms": 60000,
                "elapsed_ms": 3600000,
                "synthetic_hashes": 640,
            }
            new_schema = payload["schema"].endswith(".v2")
            self.assertEqual(
                set(measurement),
                {"scope", "base_seconds", "work_seconds", "after_seconds",
                 *caps, *({"memory"} if new_schema else set())},
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
            if new_schema:
                self._verify_anonymous_memory(measurement["memory"])
        self.assertTrue(records, "Unrecognized or empty .deploy-relay folder")
        self.assertLessEqual(len(records), 128, "Unbounded public Git diagnostics")



    def _verify_public_suite(self, data: object, public_schema: str) -> None:
        self.assertIs(type(data), dict)
        self.assertEqual(set(data), {
            "schema", "mode", "readonly_steps", "measurement", "multicore",
        })
        suite_version = "v2" if public_schema.endswith(".v2") else "v1"
        self.assertEqual(data["schema"], f"dra-v2-dev-suite.{suite_version}")
        self.assertIn(data["mode"], ("full", "multicore"))
        is_full = data["mode"] == "full"
        self.assertIs(type(data["readonly_steps"]), int)
        self.assertEqual(data["readonly_steps"], 40 if is_full else 0)
        measurement = data["measurement"]
        if is_full:
            self.assertIs(type(measurement), dict)
            self.assertEqual(set(measurement), {
                "scope", "base_seconds", "work_seconds", "after_seconds",
                "base_process_cpu_ms", "work_process_cpu_ms",
                "after_process_cpu_ms", "max_wakeup_delay_ms",
                "elapsed_ms", "synthetic_hashes", "memory",
            })
            self.assertEqual(measurement["scope"], "HA_PROCESS_WIDE_CPU_NOT_DRA_ONLY")
            for k, n in (("base_seconds", 10), ("work_seconds", 20),
                         ("after_seconds", 10)):
                self.assertIs(type(measurement[k]), int)
                self.assertEqual(measurement[k], n)
            for k, limit in {
                "base_process_cpu_ms": 3600000, "work_process_cpu_ms": 3600000,
                "after_process_cpu_ms": 3600000, "max_wakeup_delay_ms": 60000,
                "elapsed_ms": 3600000, "synthetic_hashes": 640,
            }.items():
                self.assertIs(type(measurement[k]), int)
                self.assertGreaterEqual(measurement[k], 0)
                self.assertLessEqual(measurement[k], limit)
            self._verify_anonymous_memory(measurement["memory"])
        else:
            self.assertIsNone(measurement)
        multicore = data["multicore"]
        self.assertEqual(set(multicore), {
            "schema", "method", "logical_cpus_visible",
            "affinity_cpus_visible", "levels",
        })
        self.assertEqual(multicore["schema"], f"dra-v2-dev-multicore.{suite_version}")
        self.assertEqual(multicore["method"], "BOUNDED_CHILD_PROCESSES")
        for k in ("logical_cpus_visible", "affinity_cpus_visible"):
            v = multicore[k]
            if v is not None:
                self.assertIs(type(v), int)
                self.assertGreaterEqual(v, 1)
                self.assertLessEqual(v, 1024)
        levels = multicore["levels"]
        self.assertIs(type(levels), list)
        self.assertEqual(len(levels), 7 if suite_version == "v2" else 3)
        for workers, level in zip((1, 2, 4, 6, 8, 10, 12) if suite_version == "v2" else (1, 2, 4), levels):
            self.assertEqual(set(level), {
                "workers", "status", "wall_ms",
                "aggregate_worker_cpu_ms", "iterations_total",
            })
            self.assertIs(type(level["workers"]), int)
            self.assertEqual(level["workers"], workers)
            self.assertIn(level["status"], ("ok", "unavailable"))
            if level["status"] == "unavailable":
                self.assertIsNone(level["wall_ms"])
                self.assertIsNone(level["aggregate_worker_cpu_ms"])
                self.assertIsNone(level["iterations_total"])
            else:
                for key, maxvalue in (
                    ("wall_ms", 30000),
                    ("aggregate_worker_cpu_ms", 30000),
                    ("iterations_total", workers * 400000),
                ):
                    self.assertIs(type(level[key]), int)
                    self.assertGreaterEqual(level[key], 0)
                    self.assertLessEqual(level[key], maxvalue)
                self.assertEqual(level["iterations_total"], workers * 400000)

    def _verify_anonymous_memory(self, memory: object) -> None:
        """Historical v1 exports stay valid; v2 contains only fixed counters."""
        self.assertIs(type(memory), dict)
        self.assertEqual(set(memory), {
            "schema", "source", "snapshots", "component_memory",
        })
        self.assertEqual(memory["schema"], "dra-v2-dev-memory.v1")
        self.assertEqual(memory["source"], "LINUX_PROCFS_VISIBLE_TO_HA")
        attr = memory["component_memory"]
        self.assertIs(type(attr), dict)
        self.assertEqual(set(attr), {"dra_v1_kib", "dra_v2_kib", "reason"})
        self.assertIsNone(attr["dra_v1_kib"])
        self.assertIsNone(attr["dra_v2_kib"])
        self.assertEqual(attr["reason"], "SHARED_HA_PROCESS_CANNOT_ATTRIBUTE")
        snapshots = memory["snapshots"]
        self.assertEqual(set(snapshots), {"start", "base_end", "work_end", "end"})
        keys = {
            "total_kib", "used_effective_kib", "free_kib", "available_kib",
            "ha_process_rss_kib",
        }
        for sample in snapshots.values():
            self.assertEqual(set(sample), keys)
            for number in sample.values():
                if number is not None:
                    self.assertIs(type(number), int)
                    self.assertGreaterEqual(number, 0)
                    self.assertLessEqual(number, 1 << 44)
            total, used, free, available = (
                sample["total_kib"], sample["used_effective_kib"],
                sample["free_kib"], sample["available_kib"],
            )
            if total is None:
                self.assertIsNone(used)
                self.assertIsNone(free)
                self.assertIsNone(available)
            else:
                self.assertGreater(total, 0)
                self.assertLessEqual(free, total)
                self.assertLessEqual(available, total)
                self.assertEqual(used, total - available)


if __name__ == "__main__":
    unittest.main()
