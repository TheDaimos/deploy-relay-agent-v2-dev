"""Latest Git SHA check must never prepare or authorize an installation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"deploy_relay_v2_dev"

class SourceHeadContracts(unittest.TestCase):
    def test_is_read_only_and_uses_registered_project_auth(self):
        source=(ROOT/"remote_source.py").read_text(encoding="utf-8")
        ws=(ROOT/"websocket_api.py").read_text(encoding="utf-8")
        ui=(ROOT/"frontend"/"lab.js").read_text(encoding="utf-8")
        self.assertIn('async def inspect_source_head(',source)
        self.assertIn('"/commits/" + quote(ref, safe="")',source)
        self.assertIn('source_ref(ref)',source)
        self.assertIn('async def async_projects_source_head(',ws)
        self.assertIn('runtime.source_scan_lock',ws)
        self.assertIn('runtime.project_auth.token(repo) or runtime.source_auth.token',ws)
        start=ws.index('async def async_projects_source_head(')
        end=ws.index('async def _inspect_source_preview(',start)
        body=ws[start:end]
        self.assertNotIn('async_install_start',body)
        self.assertNotIn('async_install_prepare',body)
        self.assertIn('id="dra-source-refresh"',ui)
        self.assertIn('this._sourcePreview = null;',ui)
        self.assertIn('Neuer Git-Commit erkannt. Alte Vorschau ungültig',ui)
        self.assertIn('projects/source_head',ui)
        self.assertIn('this._installPreparation = null;',ui)
if __name__=="__main__":
    unittest.main()
