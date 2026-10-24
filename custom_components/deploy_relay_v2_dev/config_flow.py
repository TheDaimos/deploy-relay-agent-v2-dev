"""Opt-in setup of a separate, read-only test integration."""
from __future__ import annotations

import probatio
from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN, NAME


class DRAV2DevConfigFlow(ConfigFlow, domain=DOMAIN):
    """Never create or migrate a V1 config entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user", data_schema=probatio.Schema({}))
