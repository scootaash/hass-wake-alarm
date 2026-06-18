"""Wake Alarm sensors: next_alarm timestamp, state enum, media selection."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_THUMBNAIL,
    CONF_LIGHT_ENTITIES,
    CONF_MEDIA_PLAYER_ENTITIES,
    CONF_PERSON_ENTITY,
    DOMAIN,
    MEDIA_STATE_NONE,
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
            WakeAlarmMediaSelectionSensor(entry, coordinator),
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Surface config-entry data the card needs (lights / players / person /
        the user-friendly instance name).

        config_entry.data isn't readable from the frontend, so we mirror the
        target entity IDs as attributes on this sensor. The card uses these
        for the targets section in the settings view, to scope the media
        browser to the first selected media player, and to render the
        instance name in its header (locale-safe — no friendly_name regex).
        """
        data = self._entry.data
        return {
            "instance_name": data.get(CONF_NAME, ""),
            "light_entities": list(data.get(CONF_LIGHT_ENTITIES, []) or []),
            "media_player_entities": list(
                data.get(CONF_MEDIA_PLAYER_ENTITIES, []) or []
            ),
            "person_entity": data.get(CONF_PERSON_ENTITY),
        }


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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snooze_until = self._coordinator.snooze_finishes_at
        return {
            "snooze_until": snooze_until.isoformat() if snooze_until else None,
        }


class WakeAlarmMediaSelectionSensor(WakeAlarmEntity, SensorEntity, RestoreEntity):
    """Read-only sensor reflecting the user's last media selection.

    Written via the wake_alarm.set_media service. Persistence is via
    RestoreEntity — selection survives HA restarts without requiring a
    config-entry reload cycle on every pick.

    State is the friendly title (e.g. "Morning Wake Up Mix") or the literal
    "none" when nothing is picked. The actual media_content_id /
    media_content_type / thumbnail are exposed as attributes.
    """

    _attr_translation_key = "media_selection"

    def __init__(
        self, entry: ConfigEntry, coordinator: WakeAlarmCoordinator
    ) -> None:
        super().__init__(entry, key="media_selection", platform="sensor")
        self._coordinator = coordinator
        self._title: str | None = None
        self._content_id: str | None = None
        self._content_type: str | None = None
        self._thumbnail: str | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in (
            None,
            "",
            "unknown",
            "unavailable",
            MEDIA_STATE_NONE,
        ):
            attrs = last.attributes or {}
            content_id = attrs.get(ATTR_MEDIA_CONTENT_ID)
            content_type = attrs.get(ATTR_MEDIA_CONTENT_TYPE)
            if content_id and content_type:
                self._title = last.state
                self._content_id = content_id
                self._content_type = content_type
                self._thumbnail = attrs.get(ATTR_MEDIA_THUMBNAIL)
        self._coordinator.register_media_sensor(self)

    @property
    def native_value(self) -> str:
        return self._title if self._title else MEDIA_STATE_NONE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_MEDIA_CONTENT_ID: self._content_id,
            ATTR_MEDIA_CONTENT_TYPE: self._content_type,
            ATTR_MEDIA_THUMBNAIL: self._thumbnail,
        }

    @callback
    def selection_data(self) -> dict[str, Any] | None:
        """Returns the current selection or None if nothing usable is picked."""
        if not self._content_id or not self._content_type:
            return None
        return {
            "content_id": self._content_id,
            "content_type": self._content_type,
            "title": self._title or self._content_id,
            "thumbnail": self._thumbnail,
        }

    @callback
    def update_selection(
        self,
        *,
        content_id: str,
        content_type: str,
        title: str,
        thumbnail: str | None,
    ) -> None:
        self._content_id = content_id
        self._content_type = content_type
        self._title = title
        self._thumbnail = thumbnail
        self.async_write_ha_state()
