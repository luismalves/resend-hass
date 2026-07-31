"""Config flow for Resend."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import CannotConnect, InvalidAuth, async_validate_key
from .const import CONF_FROM, CONF_RECIPIENT, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_FROM): TextSelector(),
        vol.Required(CONF_RECIPIENT): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, multiple=True)
        ),
    }
)


class ResendConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for an API key, a verified sender and a default recipient."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_FROM].lower())
            self._abort_if_unique_id_configured()

            try:
                await async_validate_key(
                    async_get_clientsession(self.hass), user_input[CONF_API_KEY]
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_FROM], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
