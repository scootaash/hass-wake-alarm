"""Base entity for Wake Alarm."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import CONF_SLUG, DOMAIN


class WakeAlarmEntity(Entity):
    """Base class. Sets device info, unique_id, and entity_id by slug."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, key: str, platform: str) -> None:
        self._entry = entry
        self._key = key
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self.entity_id = f"{platform}.{slug}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Wake Alarm",
            model="Alarm Instance",
            entry_type=DeviceEntryType.SERVICE,
        )
