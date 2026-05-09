"""Wake Alarm binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WakeAlarmCoordinator
from .entity import WakeAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WakeAlarmCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities([WakeAlarmActiveBinarySensor(entry, coordinator)])


class WakeAlarmActiveBinarySensor(WakeAlarmEntity, BinarySensorEntity):
    """True whenever the coordinator is in any non-idle state."""

    _attr_translation_key = "active"

    def __init__(
        self, entry: ConfigEntry, coordinator: WakeAlarmCoordinator
    ) -> None:
        super().__init__(entry, key="active", platform="binary_sensor")
        self._coordinator = coordinator

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._coordinator.is_active
