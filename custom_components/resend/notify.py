"""Notify entity so Resend works with `notify.send_message` and HA alerts."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .api import ResendError, async_send
from .const import CONF_FROM, CONF_RECIPIENT, DOMAIN
from .payload import build_payload


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the notify entity for a Resend account."""
    async_add_entities([ResendNotifyEntity(entry)])


class ResendNotifyEntity(NotifyEntity):
    """Sends plain-text mail to the entry's default recipients.

    ponytail: `notify.send_message` only carries message + title, so templates,
    CC and attachments live on the `resend.send_email` action instead.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialise the entity."""
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Resend",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a message."""
        payload = build_payload(
            {
                "to": self._entry.data[CONF_RECIPIENT],
                "subject": title or "Home Assistant",
                "text": message,
            },
            self._entry.data[CONF_FROM],
        )
        try:
            await async_send(
                async_get_clientsession(self.hass),
                self._entry.data[CONF_API_KEY],
                payload,
            )
        except ResendError as err:
            raise HomeAssistantError(str(err)) from err
