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
    Platform.BUTTON,
]

# Config entry data keys (CONF_NAME comes from homeassistant.const)
CONF_SLUG = "slug"
CONF_LIGHT_ENTITIES = "light_entities"
CONF_MEDIA_PLAYER_ENTITIES = "media_player_entities"
CONF_PERSON_ENTITY = "person_entity"
CONF_NOTIFY_TARGET_STANDARD = "notify_target_standard"
CONF_NOTIFY_TARGET_URGENT = "notify_target_urgent"

# Days of week. Each entry is (entity_key, translation_key).
#
# entity_key is what appears in the entity_id and unique_id, prefixed
# d1..d7 so HA's alphabetical entity sort displays the toggles in
# calendar order (Mon..Sun) inside the device card.
#
# translation_key keeps the friendly label in strings.json stable as
# "Mon", "Tue", etc. — no migration needed for the displayed name.
DAY_DEFS: tuple[tuple[str, str], ...] = (
    ("d1_mon", "mon"),
    ("d2_tue", "tue"),
    ("d3_wed", "wed"),
    ("d4_thu", "thu"),
    ("d5_fri", "fri"),
    ("d6_sat", "sat"),
    ("d7_sun", "sun"),
)

# Tuple of entity_keys in calendar order (positions 0..6 match
# datetime.weekday()). Used by the coordinator to bucket day toggles.
DAYS: tuple[str, ...] = tuple(k for k, _ in DAY_DEFS)

# Defaults: Mon..Fri on, Sat/Sun off.
DEFAULT_DAYS_ON: tuple[str, ...] = tuple(k for k, _ in DAY_DEFS[:5])

# v1→v2 migration map: old-key → new-key for the day toggles.
DAY_KEY_MIGRATION: dict[str, str] = {
    tk: ek for ek, tk in DAY_DEFS
}

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

# Restart catch-up window. If Home Assistant is down at alarm_time and boots
# back up within this many minutes, the alarm fires immediately so the user is
# still woken; beyond it, the schedule simply rolls forward to the next day.
CATCHUP_GRACE_MIN = 15

# Attribute keys on sensor.<slug>_media_selection
ATTR_MEDIA_CONTENT_ID = "media_content_id"
ATTR_MEDIA_CONTENT_TYPE = "media_content_type"
ATTR_MEDIA_THUMBNAIL = "thumbnail"

# Sentinel state for sensor.<slug>_media_selection when nothing is picked.
MEDIA_STATE_NONE = "none"

# Service names
SERVICE_SET_MEDIA = "set_media"
