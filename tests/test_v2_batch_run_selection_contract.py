"""Batch run isolation and independent recommended-source discovery contracts."""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1] / "custom_components" / "deploy_relay_v2_dev"

class BatchRunContract(unittest.TestCase):
    def test_select_once_per_run_without_persisting_catalog(self):
        js=(ROOT/"frontend"/"lab.js").read_text(encoding="utf-8")
        self.assertIn("this._batchRunSelected = new Set",js)
        self.assertIn('this._batchRunSelected.has(p.repository)',js)
        self.assertIn('id="dra-main-batch-selection"',js)
        self.assertIn('this._mainBatchSelectionOpen ? "open" : ""',js)
        self.assertIn('class="dra-batch-run-choice"',js)
        self.assertIn('this._toggleBatchRunProject(',js)
        self.assertIn('this._batchStatus?.status',js)
        self.assertIn('this._isBatchSelfUpdate(p)',js)
        self.assertIn('this._isOwnBatchUpdate(p)',js)
        self.assertIn('Eigenaktualisierung · zuletzt',js)

    def test_explicit_weather_router_ref_never_lost_to_automatic_main(self):
        js=(ROOT/"frontend"/"lab.js").read_text(encoding="utf-8")
        self.assertIn("this._manualSourceRef = true;",js)
        self.assertIn('this._mainSourceRef.trim() === result.default_ref',js)
        self.assertIn('result.recommended.explicit && selectedIsDefault',js)
        self.assertIn('this._mainSourceRef = result.recommended.ref;',js)
        self.assertIn('this._automaticSourceCheckFor = null;',js)
        self.assertIn('if (oldDefaultPrepared) this._installPreparation = null;',js)

    def test_branch_discovery_not_blocked_by_inventory_lock(self):
        ws=(ROOT/"websocket_api.py").read_text(encoding="utf-8")
        init=(ROOT/"__init__.py").read_text(encoding="utf-8")
        ast.parse(ws);ast.parse(init)
        fragment=ws.split("async def async_projects_source_choices(",1)[1].split(
            "async def async_projects_source_head(",1)[0]
        self.assertIn("async with runtime.source_choices_lock:",fragment)
        self.assertNotIn("runtime.source_scan_lock.locked()",fragment)
        self.assertNotIn("async with runtime.source_scan_lock:",fragment)
        self.assertIn("source_choices_lock=asyncio.Lock()",init)

if __name__=="__main__":
    unittest.main()
