"""Wake Alarm services."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DOMAIN, SERVICE_SET_MEDIA

_LOGGER = logging.getLogger(__name__)

_SET_MEDIA_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): vol.All(cv.ensure_list, [cv.entity_id]),
        vol.Required("media_content_id"): cv.string,
        vol.Required("media_content_type"): cv.string,
        vol.Required("title"): cv.string,
        vol.Optional("thumbnail"): cv.string,
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register wake_alarm.* services. Idempotent across reloads."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_MEDIA):
        return

    async def _async_set_media(call: ServiceCall) -> None:
        entity_ids: list[str] = call.data[ATTR_ENTITY_ID]
        registry = er.async_get(hass)
        domain_data = hass.data.get(DOMAIN, {})

        # Resolve target entities to unique config entries (multi-target call
        # could legitimately set the same media on several alarms at once).
        target_entry_ids: set[str] = set()
        for entity_id in entity_ids:
            entry = registry.async_get(entity_id)
            if entry is None or entry.config_entry_id is None:
                raise HomeAssistantError(
                    f"unknown wake_alarm entity: {entity_id}"
                )
            if entry.config_entry_id not in domain_data:
                raise HomeAssistantError(
                    f"no wake_alarm coordinator for {entity_id}"
                )
            target_entry_ids.add(entry.config_entry_id)

        for entry_id in target_entry_ids:
            coordinator = domain_data[entry_id]["coordinator"]
            coordinator.async_set_media(
                content_id=call.data["media_content_id"],
                content_type=call.data["media_content_type"],
                title=call.data["title"],
                thumbnail=call.data.get("thumbnail"),
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MEDIA,
        _async_set_media,
        schema=_SET_MEDIA_SCHEMA,
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Remove wake_alarm.* services. Called once the last entry is unloaded."""
    for service in (SERVICE_SET_MEDIA,):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
