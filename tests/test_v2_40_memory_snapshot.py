"""Linux-visible memory counters: small fixed /proc read, no HA/files/secrets."""
from __future__ import annotations

import importlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"
PKG = "_v2_memory_snapshot_test"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package
m = importlib.import_module(f"{PKG}.readonly_benchmark")


class MemorySnapshotTests(unittest.TestCase):
    def _sample(self, *, mem: str, status: str) -> dict:
        files = {
            "/proc/meminfo": mem,
            "/proc/self/status": status,
        }
        seen = []

        def fake_open(path, mode, encoding):
            seen.append((path, mode, encoding))
            if path not in files:
                raise AssertionError("unexpected file accessed")
            return io.StringIO(files[path])

        with patch("builtins.open", side_effect=fake_open):
            sample = m.snapshot_memory()
        self.assertEqual([item[0] for item in seen], [
            "/proc/meminfo", "/proc/self/status"
        ])
        return sample

    def test_usable_total_effective_used_free_available_and_rss(self):
        sample = self._sample(
            mem="MemTotal: 7340032 kB\nMemFree: 2097152 kB\n"
                "MemAvailable: 4194304 kB\nSwapTotal: 0 kB\n",
            status="Name:\tpython3\nVmRSS:\t524288 kB\n",
        )
        self.assertEqual(sample, {
            "total_kib": 7340032,
            "used_effective_kib": 3145728,
            "free_kib": 2097152,
            "available_kib": 4194304,
            "ha_process_rss_kib": 524288,
        })

    def test_missing_or_unreliable_proc_data_must_not_be_zero(self):
        sample = self._sample(
            mem="MemTotal: 1024 kB\nMemFree: 1800 kB\n"
                "MemAvailable: 999999 kB\n",
            status="Name:\tpython3\n",
        )
        self.assertEqual(sample, dict.fromkeys(m.SNAPSHOT_FIELDS))

    def test_process_rss_optional_without_discarding_system_memory(self):
        sample = self._sample(
            mem="MemTotal: 1000 kB\nMemFree: 80 kB\nMemAvailable: 360 kB\n",
            status="VmSize:\t2048 kB\n",
        )
        self.assertEqual(sample["used_effective_kib"], 640)
        self.assertIsNone(sample["ha_process_rss_kib"])

    def test_unavailable_proc_files_return_nulls(self):
        with patch("builtins.open", side_effect=OSError("do not disclose")):
            self.assertEqual(m.snapshot_memory(), dict.fromkeys(m.SNAPSHOT_FIELDS))

    def test_read_only_fixed_paths_and_bounded_input(self):
        import inspect
        src = inspect.getsource(m._read_fields)
        self.assertIn("source.read(16384)", src)
        self.assertNotIn("os.environ", src)
        self.assertEqual(m._MEMINFO, "/proc/meminfo")
        self.assertEqual(m._STATUS, "/proc/self/status")


if __name__ == "__main__":
    unittest.main()
