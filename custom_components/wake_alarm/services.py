"""Wake Alarm services + mobile-action event routing.

Two surfaces:

1. wake_alarm.set_media — the card calls this after the user picks media
   in the in-card browser. Resolves target → config entry → coordinator
   and writes through to the media_selection sensor.

2. wake_alarm.{snooze, dismiss, cancel_ramp, test_light_ramp, test_music}
   — target-only services that map straight to coordinator methods. These
   give automations and the mobile notification actions a stable handle.

The mobile_app_notification_action event is decoded once globally; the
notification payloads encode the entry_id in the action string, so we
can resolve back to the right coordinator without scanning.
"""
from __future__ import annotations

import logging
from typing import Callable

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DOMAIN, SERVICE_SET_MEDIA
from .notifications import ACTION_DISMISS, ACTION_SNOOZE, parse_action_id

_LOGGER = logging.getLogger(__name__)

# Internal hass.data[DOMAIN] key for the global event listener removal
# callable. Underscore-prefixed so the per-entry data lookup ignores it.
_LISTENER_KEY = "_global_action_listener"

# Companion app event for action button taps. Same name on both iOS and
# Android in modern HA Companion versions.
_NOTIFICATION_ACTION_EVENT = "mobile_app_notification_action"

# Target-only services: each maps service-name → coordinator method-name.
_TARGET_SERVICES: tuple[tuple[str, str], ...] = (
    ("snooze", "async_snooze"),
    ("dismiss", "async_dismiss"),
    ("cancel_ramp", "async_cancel_ramp"),
    ("test_light_ramp", "async_test_light_ramp"),
    ("test_music", "async_test_music"),
    ("test_standard_notification", "async_test_standard_notification"),
    ("test_urgent_notification", "async_test_urgent_notification"),
)

_TARGET_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): vol.All(cv.ensure_list, [cv.entity_id])}
)

_SET_MEDIA_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): vol.All(cv.ensure_list, [cv.entity_id]),
        vol.Required("media_content_id"): cv.string,
        vol.Required("media_content_type"): cv.string,
        vol.Required("title"): cv.string,
        vol.Optional("thumbnail"): cv.string,
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register every wake_alarm.* service + the action listener.

    Idempotent across reloads: the has_service guard ensures the whole
    block (services + listener) is registered exactly once.
    """
    if hass.services.has_service(DOMAIN, SERVICE_SET_MEDIA):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MEDIA,
        _build_set_media_handler(hass),
        schema=_SET_MEDIA_SCHEMA,
    )
    for service_name, method_name in _TARGET_SERVICES:
        hass.services.async_register(
            DOMAIN,
            service_name,
            _build_target_handler(hass, method_name),
            schema=_TARGET_SCHEMA,
        )

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[_LISTENER_KEY] = hass.bus.async_listen(
        _NOTIFICATION_ACTION_EVENT, _build_action_handler(hass)
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Remove every wake_alarm.* service + the action listener."""
    domain_data = hass.data.get(DOMAIN, {})
    remove: CALLBACK_TYPE | None = domain_data.pop(_LISTENER_KEY, None)
    if remove is not None:
        remove()
    for service in (SERVICE_SET_MEDIA, *(name for name, _ in _TARGET_SERVICES)):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)


# -------------------- handler builders --------------------


def _build_set_media_handler(hass: HomeAssistant) -> Callable:
    async def _handler(call: ServiceCall) -> None:
        target_entry_ids = _resolve_target_entries(hass, call.data[ATTR_ENTITY_ID])
        domain_data = hass.data[DOMAIN]
        for entry_id in target_entry_ids:
            coordinator = domain_data[entry_id]["coordinator"]
            coordinator.async_set_media(
                content_id=call.data["media_content_id"],
                content_type=call.data["media_content_type"],
                title=call.data["title"],
                thumbnail=call.data.get("thumbnail"),
            )

    return _handler


def _build_target_handler(hass: HomeAssistant, method_name: str) -> Callable:
    async def _handler(call: ServiceCall) -> None:
        target_entry_ids = _resolve_target_entries(hass, call.data[ATTR_ENTITY_ID])
        domain_data = hass.data[DOMAIN]
        for entry_id in target_entry_ids:
            coordinator = domain_data[entry_id]["coordinator"]
            await getattr(coordinator, method_name)()

    return _handler


def _build_action_handler(hass: HomeAssistant) -> Callable:
    @callback
    def _handler(event: Event) -> None:
        action = event.data.get("action")
        if not isinstance(action, str):
            return
        parsed = parse_action_id(action)
        if parsed is None:
            return
        action_name, entry_id = parsed
        domain_data = hass.data.get(DOMAIN, {})
        entry_data = domain_data.get(entry_id)
        if entry_data is None:
            _LOGGER.debug(
                "ignoring action %s: no coordinator for %s", action, entry_id
            )
            return
        coordinator = entry_data["coordinator"]
        if action_name == ACTION_SNOOZE:
            hass.async_create_task(coordinator.async_snooze())
        elif action_name == ACTION_DISMISS:
            hass.async_create_task(coordinator.async_dismiss())
        else:
            _LOGGER.debug("unknown wake_alarm action: %s", action_name)

    return _handler


# -------------------- shared resolution --------------------


def _resolve_target_entries(
    hass: HomeAssistant, entity_ids: list[str]
) -> set[str]:
    """Map a list of target entity IDs to the unique config-entry IDs they own."""
    registry = er.async_get(hass)
    domain_data = hass.data.get(DOMAIN, {})
    target_entry_ids: set[str] = set()
    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        if entry is None or entry.config_entry_id is None:
            raise HomeAssistantError(f"unknown wake_alarm entity: {entity_id}")
        if entry.config_entry_id not in domain_data:
            raise HomeAssistantError(
                f"no wake_alarm coordinator for {entity_id}"
            )
        target_entry_ids.add(entry.config_entry_id)
    return target_entry_ids
