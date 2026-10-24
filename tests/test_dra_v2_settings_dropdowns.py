"""Static regression guards for mobile-safe DRA V2 DEV task settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "custom_components/deploy_relay_v2_dev/frontend/lab.js"


def test_two_numeric_fields_replaced_with_selects():
    src = LAB.read_text(encoding="utf-8")
    assert '<select id="settings-readonly" class="project-text">' in src
    assert '<select id="settings-workers" class="project-text">' in src
    assert '<input id="settings-readonly"' not in src
    assert '<input id="settings-workers"' not in src
    assert '[1,2,3,4].map(' in src
    assert 'Array.from({length:12}, (_, i) => i + 1)' in src


def test_background_refresh_cannot_close_focused_selector():
    src = LAB.read_text(encoding="utf-8")
    assert 'const editing = s?.activeElement;' in src
    assert 'this._settingsRenderPending = true;' in src
    assert 'No immediate rerender on blur' in src
    assert 'this._settingsDraft = {' in src
    assert 'this._settingsDraft = null;' in src


def test_existing_safety_limits_unchanged():
    src = LAB.read_text(encoding="utf-8")
    assert 'readonly < 1 || readonly > 4' in src
    assert 'workers < 1 || workers > 12' in src
    assert '"controlled"].includes(mode)' in src
