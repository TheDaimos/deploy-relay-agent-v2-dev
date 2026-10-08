"""V2 DEV-only admin panel; no V1 paths or elements are touched."""
from __future__ import annotations

from pathlib import Path
from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME, PANEL_ELEMENT, PANEL_PATH, STATIC_PATH, VERSION


async def async_register_panel(hass: HomeAssistant) -> None:
    state = hass.data.setdefault(DOMAIN, {})
    if not state.get("static_registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(
                STATIC_PATH, str(Path(__file__).parent / "frontend"),
                cache_headers=False,
            )]
        )
        state["static_registered"] = True
    if frontend.async_panel_exists(hass, PANEL_PATH):
        return
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=NAME,
        sidebar_icon="mdi:flask-outline",
        frontend_url_path=PANEL_PATH,
        config={"_panel_custom": {
            "name": PANEL_ELEMENT,
            "embed_iframe": False,
            "trust_external": False,
            "handle_safe_area": False,
            "module_url": f"{STATIC_PATH}/lab.js?v={VERSION}",
        }},
        require_admin=True,
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    if frontend.async_panel_exists(hass, PANEL_PATH):
        frontend.async_remove_panel(hass, PANEL_PATH, warn_if_unknown=False)
