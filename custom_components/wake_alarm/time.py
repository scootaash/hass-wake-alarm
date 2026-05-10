"""Wake Alarm time-of-day entity."""
from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import WakeAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WakeAlarmAlarmTime(entry)])


class WakeAlarmAlarmTime(WakeAlarmEntity, TimeEntity, RestoreEntity):
    """Alarm time-of-day. 24-hour, no seconds in UI but stored to second precision."""

    _attr_translation_key = "alarm_time"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, key="alarm_time", platform="time")
        self._attr_native_value = dt_time(7, 0)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None or last_state.state in (None, "unknown", "unavailable"):
            return
        try:
            self._attr_native_value = dt_time.fromisoformat(last_state.state)
        except ValueError:
            pass

    async def async_set_value(self, value: dt_time) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
