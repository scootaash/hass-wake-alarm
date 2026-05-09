"""Constants for the Wake Alarm integration."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "wake_alarm"

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.TIME,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

# Config entry data keys (CONF_NAME comes from homeassistant.const)
CONF_SLUG = "slug"
CONF_LIGHT_ENTITIES = "light_entities"
CONF_MEDIA_PLAYER_ENTITIES = "media_player_entities"
CONF_MEDIA_CONTENT_ID = "media_content_id"
CONF_MEDIA_CONTENT_TYPE = "media_content_type"
CONF_PERSON_ENTITY = "person_entity"
CONF_NOTIFY_TARGET_STANDARD = "notify_target_standard"
CONF_NOTIFY_TARGET_URGENT = "notify_target_urgent"

# Days of week, ordered Mon..Sun (matches datetime.weekday())
DAYS: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DEFAULT_DAYS_ON: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri")

# State machine values exposed via sensor.<slug>_state
STATE_IDLE = "idle"
STATE_RAMPING = "ramping"
STATE_PLAYING = "playing"
STATE_SNOOZING = "snoozing"

# Defaults for runtime-tweakable entities
DEFAULT_ALARM_TIME = "07:00:00"
DEFAULT_LENGTH_MIN = 15
DEFAULT_START_KELVIN = 1500
DEFAULT_TARGET_KELVIN = 4500
DEFAULT_MAX_BRIGHTNESS_PCT = 35
DEFAULT_VOLUME = 0.08
DEFAULT_SNOOZE_MIN = 4
DEFAULT_STEPS_PER_MIN = 20
DEFAULT_MUSIC_FADE_SEC = 60
DEFAULT_AUTO_DISMISS_MIN = 0

# Allowed media content types (config flow dropdown)
MEDIA_CONTENT_TYPES: tuple[str, ...] = (
    "favorite_item_id",
    "playlist",
    "music",
    "url",
)
