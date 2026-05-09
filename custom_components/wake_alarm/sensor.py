"""Wake Alarm sensors: next_alarm timestamp + state enum."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    STATE_IDLE,
    STATE_PLAYING,
    STATE_RAMPING,
    STATE_SNOOZING,
)
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
    async_add_entities(
        [
            WakeAlarmNextAlarmSensor(entry, coordinator),
            WakeAlarmStateSensor(entry, coordinator),
        ]
    )


class _CoordinatorSensor(WakeAlarmEntity, SensorEntity):
    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WakeAlarmCoordinator,
        *,
        key: str,
    ) -> None:
        super().__init__(entry, key=key, platform="sensor")
        self._coordinator = coordinator

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class WakeAlarmNextAlarmSensor(_CoordinatorSensor):
    _attr_translation_key = "next_alarm"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self, entry: ConfigEntry, coordinator: WakeAlarmCoordinator
    ) -> None:
        super().__init__(entry, coordinator, key="next_alarm")

    @property
    def native_value(self) -> datetime | None:
        return self._coordinator.next_fire


class WakeAlarmStateSensor(_CoordinatorSensor):
    _attr_translation_key = "state"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [STATE_IDLE, STATE_RAMPING, STATE_PLAYING, STATE_SNOOZING]

    def __init__(
        self, entry: ConfigEntry, coordinator: WakeAlarmCoordinator
    ) -> None:
        super().__init__(entry, coordinator, key="state")

    @property
    def native_value(self) -> str:
        return self._coordinator.state
