"""Register the Deploy Relay admin sidebar panel."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    NAME,
    PANEL_ELEMENT,
    PANEL_ICON,
    PANEL_STATIC_URL,
    PANEL_URL_PATH,
    VERSION,
)

_FRONTEND_DIR = Path(__file__).parent / "frontend"


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register static frontend assets and the admin-only sidebar panel."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    if not domain_data.get("static_registered"):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    PANEL_STATIC_URL,
                    str(_FRONTEND_DIR),
                    cache_headers=False,
                )
            ]
        )
        domain_data["static_registered"] = True

    if frontend.async_panel_exists(hass, PANEL_URL_PATH):
        return

    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=NAME,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        config={
            "_panel_custom": {
                "name": PANEL_ELEMENT,
                "embed_iframe": False,
                "trust_external": False,
                "handle_safe_area": False,
                "module_url": (
                    f"{PANEL_STATIC_URL}/deploy-relay-panel.js?v={VERSION}"
                ),
            }
        },
        require_admin=True,
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel when the single config entry unloads."""
    if frontend.async_panel_exists(hass, PANEL_URL_PATH):
        frontend.async_remove_panel(
            hass,
            PANEL_URL_PATH,
            warn_if_unknown=False,
        )
