"""Wake Alarm switch entities (master enable + 7 day-of-week toggles)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DAY_DEFS, DEFAULT_DAYS_ON
from .entity import WakeAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities: list[SwitchEntity] = [WakeAlarmEnabledSwitch(entry)]
    for entity_key, translation_key in DAY_DEFS:
        entities.append(
            WakeAlarmDaySwitch(
                entry,
                entity_key=entity_key,
                translation_key=translation_key,
                default_on=entity_key in DEFAULT_DAYS_ON,
            )
        )
    async_add_entities(entities)


class _RestorableSwitch(WakeAlarmEntity, SwitchEntity, RestoreEntity):
    """Common restore-on-startup boolean switch."""

    def __init__(
        self, entry: ConfigEntry, key: str, default_on: bool = False
    ) -> None:
        super().__init__(entry, key=key, platform="switch")
        self._default_on = default_on
        self._attr_is_on = default_on

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ("on", "off"):
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()


class WakeAlarmEnabledSwitch(_RestorableSwitch):
    """Master enable switch (default off)."""

    _attr_translation_key = "enabled"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, key="enabled", default_on=False)


class WakeAlarmDaySwitch(_RestorableSwitch):
    """Day-of-week toggle (Mon–Fri default on, Sat/Sun default off).

    entity_key is the d1_mon..d7_sun key embedded in the entity_id and
    unique_id; translation_key is the short label ("mon"..."sun") that
    strings.json maps to the user-visible "Mon"..."Sun".
    """

    def __init__(
        self,
        entry: ConfigEntry,
        *,
        entity_key: str,
        translation_key: str,
        default_on: bool,
    ) -> None:
        super().__init__(entry, key=entity_key, default_on=default_on)
        self._attr_translation_key = translation_key
