"""The Resend integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import ResendError, async_send
from .const import CONF_FROM, DOMAIN, SERVICE_SEND_EMAIL
from .payload import build_payload

PLATFORMS = [Platform.NOTIFY]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_EMAIL_LIST = vol.All(cv.ensure_list, [cv.string])

ATTACHMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("filename"): cv.string,
        # Base64 content, or a public URL for Resend to fetch.
        vol.Exclusive("content", "source"): cv.string,
        vol.Exclusive("path", "source"): cv.string,
        vol.Optional("content_type"): cv.string,
        vol.Optional("content_id"): cv.string,
    }
)

SEND_EMAIL_SCHEMA = vol.Schema(
    {
        vol.Optional("config_entry_id"): cv.string,
        vol.Required("to"): _EMAIL_LIST,
        vol.Optional("from_address"): cv.string,
        vol.Optional("subject"): cv.string,
        vol.Optional("template_id"): cv.string,
        vol.Optional("template_variables"): {cv.string: cv.string},
        vol.Optional("html"): cv.string,
        vol.Optional("text"): cv.string,
        vol.Optional("cc"): _EMAIL_LIST,
        vol.Optional("bcc"): _EMAIL_LIST,
        vol.Optional("reply_to"): _EMAIL_LIST,
        vol.Optional("headers"): {cv.string: cv.string},
        vol.Optional("tags"): [
            vol.Schema({vol.Required("name"): cv.string, vol.Required("value"): cv.string})
        ],
        vol.Optional("attachments"): [ATTACHMENT_SCHEMA],
        vol.Optional("scheduled_at"): cv.string,
    }
)


def _resolve_entry(hass: HomeAssistant, entry_id: str | None) -> ConfigEntry:
    """Pick the account to send from, defaulting to the only one set up."""
    loaded = hass.config_entries.async_loaded_entries(DOMAIN)

    if entry_id is None:
        if not loaded:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="no_account"
            )
        return loaded[0]

    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_account",
            translation_placeholders={"entry_id": entry_id},
        )
    return entry


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the send_email action."""

    async def _async_send_email(call: ServiceCall) -> ServiceResponse:
        entry = _resolve_entry(hass, call.data.get("config_entry_id"))
        payload = build_payload(dict(call.data), entry.data[CONF_FROM])
        try:
            result = await async_send(
                async_get_clientsession(hass), entry.data[CONF_API_KEY], payload
            )
        except ResendError as err:
            raise HomeAssistantError(str(err)) from err
        return {"id": result.get("id")}

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_EMAIL,
        _async_send_email,
        schema=SEND_EMAIL_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Resend account."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Resend account."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
