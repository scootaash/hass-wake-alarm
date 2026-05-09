"""Wake Alarm number entities (runtime-tweakable settings)."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_AUTO_DISMISS_MIN,
    DEFAULT_LENGTH_MIN,
    DEFAULT_MAX_BRIGHTNESS_PCT,
    DEFAULT_MUSIC_FADE_SEC,
    DEFAULT_SNOOZE_MIN,
    DEFAULT_START_KELVIN,
    DEFAULT_STEPS_PER_MIN,
    DEFAULT_TARGET_KELVIN,
    DEFAULT_VOLUME,
)
from .entity import WakeAlarmEntity


@dataclass(frozen=True)
class _Spec:
    key: str
    min_value: float
    max_value: float
    step: float
    default: float
    unit: str | None = None
    mode: NumberMode = NumberMode.AUTO


_SPECS: tuple[_Spec, ...] = (
    _Spec("length_min", 1, 120, 1, DEFAULT_LENGTH_MIN, UnitOfTime.MINUTES),
    _Spec("start_kelvin", 1500, 6500, 50, DEFAULT_START_KELVIN, "K"),
    _Spec("target_kelvin", 1500, 6500, 50, DEFAULT_TARGET_KELVIN, "K"),
    _Spec(
        "max_brightness_pct",
        1,
        100,
        1,
        DEFAULT_MAX_BRIGHTNESS_PCT,
        PERCENTAGE,
        NumberMode.SLIDER,
    ),
    _Spec("volume", 0.0, 1.0, 0.01, DEFAULT_VOLUME, mode=NumberMode.SLIDER),
    _Spec("snooze_min", 1, 30, 1, DEFAULT_SNOOZE_MIN, UnitOfTime.MINUTES),
    _Spec("steps_per_min", 5, 60, 1, DEFAULT_STEPS_PER_MIN),
    _Spec(
        "music_fade_sec", 0, 300, 5, DEFAULT_MUSIC_FADE_SEC, UnitOfTime.SECONDS
    ),
    _Spec(
        "auto_dismiss_min",
        0,
        120,
        1,
        DEFAULT_AUTO_DISMISS_MIN,
        UnitOfTime.MINUTES,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(WakeAlarmNumber(entry, spec) for spec in _SPECS)


class WakeAlarmNumber(WakeAlarmEntity, RestoreNumber):
    """Generic number entity restoring its last value across restarts."""

    def __init__(self, entry: ConfigEntry, spec: _Spec) -> None:
        super().__init__(entry, key=spec.key, platform="number")
        self._spec = spec
        self._attr_translation_key = spec.key
        self._attr_native_min_value = spec.min_value
        self._attr_native_max_value = spec.max_value
        self._attr_native_step = spec.step
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_mode = spec.mode
        self._attr_native_value = spec.default

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self._attr_native_value = last.native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
