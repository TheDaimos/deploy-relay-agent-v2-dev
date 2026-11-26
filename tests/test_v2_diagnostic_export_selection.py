"""Export gating is based on the last completed diagnostic, not last job."""
from __future__ import annotations

import ast
import types
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev" / "websocket_api.py"
root = ast.parse(FILE.read_text(encoding="utf-8"))
selected = next(node for node in root.body
                if isinstance(node, ast.AsyncFunctionDef) and node.name == "_exportable_diagnostic")
selected.decorator_list = []
env = {}
exec(compile(ast.Module(body=[selected], type_ignores=[]), str(FILE), "exec"), env)
select = env["_exportable_diagnostic"]


class Registry:
    def __init__(self, records):
        self.records = records

    async def list(self, limit=12):
        return self.records[:limit]

    async def get(self, operation_id):
        return next((x for x in self.records if x["operation_id"] == operation_id), None)


class Summary:
    def __init__(self, report):
        self.report = report

    def summary(self):
        return self.report


def runtime(records, *, suite=None, measurement=None):
    return types.SimpleNamespace(
        registry=Registry(records),
        suite=Summary(suite),
        measurement=Summary(measurement),
    )


def item(letter, status):
    return {"operation_id": letter * 32, "status": status}


class DiagnosticEligibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_recent_successful_measurement_remains_exportable_after_preview(self):
        records = [item("b", "success"), item("a", "success")]
        sample = {"operation_id": "a" * 32, "schema": "dra-v2-dev-measurement.v2"}
        self.assertEqual(await select(runtime(records, measurement=sample)), sample)

    async def test_running_unrelated_operation_does_not_hide_completed_measurement(self):
        records = [item("b", "running"), item("a", "success")]
        sample = {"operation_id": "a" * 32}
        self.assertEqual(await select(runtime(records, measurement=sample)), sample)

    async def test_only_successful_diagnostic_is_selected(self):
        records = [item("b", "failed"), item("a", "success")]
        suite = {"operation_id": "a" * 32, "mode": "full"}
        newer_failed = {"operation_id": "b" * 32, "schema": "dra-v2-dev-measurement.v2"}
        self.assertEqual(await select(runtime(records, suite=suite, measurement=newer_failed)), suite)

    async def test_no_data_or_only_unfinished_data_never_exportable(self):
        self.assertIsNone(await select(runtime([item("a", "success")])))
        for status in ("failed", "running", "interrupted", "cancelled"):
            with self.subTest(status=status):
                self.assertIsNone(await select(runtime(
                    [item("a", status)], measurement={"operation_id": "a" * 32},
                )))

    async def test_older_nonexistent_report_does_not_authorize_export(self):
        self.assertIsNone(await select(runtime(
            [item("b", "success")], measurement={"operation_id": "a" * 32},
        )))

    async def test_latest_real_measurement_preferred_to_older_suite(self):
        records = [item("c", "success"), item("b", "success")]
        suite = {"operation_id": "b" * 32, "mode": "full"}
        solo = {"operation_id": "c" * 32, "schema": "dra-v2-dev-measurement.v2"}
        self.assertEqual(await select(runtime(records, suite=suite, measurement=solo)), solo)


if __name__ == "__main__":
    unittest.main()
