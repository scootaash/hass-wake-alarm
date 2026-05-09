"""Wake Alarm action buttons."""
from __future__ import annotations

import logging
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WakeAlarmCoordinator
from .entity import WakeAlarmEntity

_LOGGER = logging.getLogger(__name__)

# Action key → coordinator method name. Methods missing on the coordinator
# log a warning when pressed (e.g. test_music until step 5).
_ACTIONS: tuple[tuple[str, str], ...] = (
    ("test_light_ramp", "async_test_light_ramp"),
    ("cancel_ramp", "async_cancel_ramp"),
    ("test_music", "async_test_music"),
    ("dismiss", "async_dismiss"),
    ("snooze", "async_snooze"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WakeAlarmCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        WakeAlarmActionButton(entry, coordinator, key, getattr(coordinator, attr))
        for key, attr in _ACTIONS
    )


class WakeAlarmActionButton(WakeAlarmEntity, ButtonEntity):
    """Button entity that invokes a coordinator method on press."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: WakeAlarmCoordinator,
        key: str,
        action: Callable[[], Awaitable[None]],
    ) -> None:
        super().__init__(entry, key=key, platform="button")
        self._coordinator = coordinator
        self._action = action
        self._attr_translation_key = key

    async def async_press(self) -> None:
        await self._action()
