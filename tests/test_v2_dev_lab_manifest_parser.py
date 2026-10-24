"""Validate the isolated lab deployment manifest with the actual DRA V1 parser.

Load only the pure-stdlib parser; never import or start the HA integration.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "custom_components" / "deploy_relay"


class ManifestParserContract(unittest.TestCase):
    def test_v2_sidecar_manifest_accepted_by_existing_v1_parser(self):
        package_name = "_dra_v1_manifest_validation"
        package = types.ModuleType(package_name)
        package.__path__ = [str(V1)]
        sys.modules[package_name] = package

        def load(name):
            full = f"{package_name}.{name}"
            spec = importlib.util.spec_from_file_location(full, V1 / f"{name}.py")
            self.assertIsNotNone(spec)
            module = importlib.util.module_from_spec(spec)
            sys.modules[full] = module
            spec.loader.exec_module(module)
            return module

        try:
            load("const")
            parser = load("manifest")
            paths = load("path_policy")
            raw = json.loads((ROOT / "deploy-relay.json").read_text(encoding="utf-8"))
            parsed = parser.parse_manifest(
                raw,
                expected_repository="TheDaimos/deploy-relay-agent-v2-dev",
                expected_project_id="deploy_relay_agent_v2_dev",
            )
            self.assertEqual(len(parsed.groups), 1)
            self.assertEqual(parsed.root, "/config")
            self.assertEqual(parsed.groups[0].target, "custom_components/deploy_relay_v2_dev")
            self.assertEqual(
                paths.validate_target_path(parsed.groups[0].target).as_posix(),
                "custom_components/deploy_relay_v2_dev",
            )
        finally:
            for name in ("const", "manifest", "path_policy"):
                sys.modules.pop(f"{package_name}.{name}", None)
            sys.modules.pop(package_name, None)


if __name__ == "__main__":
    unittest.main()
