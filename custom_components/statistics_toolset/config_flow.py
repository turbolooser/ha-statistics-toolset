"""UI configuration for the write locks.

The two settings that decide whether anything can be written at all belong where they can be
seen and changed: simulation mode, and which counters are writable. Putting them in the UI
also means they survive a HACS update — unlike an edit to ``const.py`` — and that changing
them reloads the integration instead of needing a restart.

There is nothing to configure when adding the integration, so the setup step just creates the
entry; everything happens under "Configure" afterwards.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ADMIN_ONLY_MODE,
    CONF_ADMIN_ONLY,
    CONF_READ_ONLY,
    CONF_WRITE_ALLOWLIST,
    DOMAIN,
    READ_ONLY_MODE,
    WRITE_ALLOWLIST,
)

TITLE = "HA Statistics Toolset"


def options_schema(current: dict[str, Any]) -> vol.Schema:
    """Build the options form, pre-filled with what is currently in force."""
    return vol.Schema(
        {
            vol.Required(
                CONF_READ_ONLY,
                default=current.get(CONF_READ_ONLY, READ_ONLY_MODE),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_WRITE_ALLOWLIST,
                default=list(current.get(CONF_WRITE_ALLOWLIST, WRITE_ALLOWLIST) or []),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Required(
                CONF_ADMIN_ONLY,
                default=current.get(CONF_ADMIN_ONLY, ADMIN_ONLY_MODE),
            ): selector.BooleanSelector(),
        }
    )


class StatisticsToolsetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add the integration; the interesting part is the options flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the single entry — nothing needs to be asked here."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=TITLE,
            data={},
            options={
                CONF_READ_ONLY: READ_ONLY_MODE,
                CONF_WRITE_ALLOWLIST: [],
                CONF_ADMIN_ONLY: ADMIN_ONLY_MODE,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return StatisticsToolsetOptionsFlow()


class StatisticsToolsetOptionsFlow(OptionsFlow):
    """Simulation mode on/off, and which counters may be written."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            # Empty list means "no restriction", which is what an empty allowlist has always
            # meant — stored as a list so the entry stays JSON-serialisable.
            return self.async_create_entry(
                data={
                    CONF_READ_ONLY: bool(user_input[CONF_READ_ONLY]),
                    CONF_WRITE_ALLOWLIST: list(user_input.get(CONF_WRITE_ALLOWLIST) or []),
                    CONF_ADMIN_ONLY: bool(user_input[CONF_ADMIN_ONLY]),
                }
            )
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(dict(self.config_entry.options)),
        )
