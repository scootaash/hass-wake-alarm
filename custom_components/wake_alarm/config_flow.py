"""Config and options flow for Wake Alarm.

Single-screen wizard. Both the create flow and the options flow render
every field at once with per-field help text (translated via the
``data_description`` key in strings.json).
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_AFTER_SCRIPT,
    CONF_BEFORE_SCRIPT,
    CONF_CONDITION_ENTITY,
    CONF_LIGHT_ENTITIES,
    CONF_MEDIA_PLAYER_ENTITIES,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
    CONF_PERSON_ENTITY,
    CONF_SLUG,
    DOMAIN,
)


def _validate_players(
    hass: HomeAssistant, players: list[str]
) -> tuple[dict[str, str], dict[str, Any]]:
    """Verify all selected players share an integration AND advertise GROUPING.

    Returns (errors, description_placeholders).
    """
    errors: dict[str, str] = {}
    placeholders: dict[str, Any] = {}

    if len(players) <= 1:
        return errors, placeholders

    registry = er.async_get(hass)
    platforms: set[str] = set()
    no_grouping: list[str] = []
    unavailable: list[str] = []

    for entity_id in players:
        state = hass.states.get(entity_id)
        if state is None:
            unavailable.append(entity_id)
            continue
        features = int(state.attributes.get("supported_features", 0) or 0)
        if not (features & MediaPlayerEntityFeature.GROUPING):
            no_grouping.append(entity_id)
        ent = registry.async_get(entity_id)
        if ent is not None:
            platforms.add(ent.platform)

    if unavailable:
        errors[CONF_MEDIA_PLAYER_ENTITIES] = "media_player_unavailable"
        placeholders["players"] = ", ".join(unavailable)
    elif no_grouping:
        errors[CONF_MEDIA_PLAYER_ENTITIES] = "no_grouping_support"
        placeholders["players"] = ", ".join(no_grouping)
    elif len(platforms) > 1:
        errors[CONF_MEDIA_PLAYER_ENTITIES] = "mixed_platforms"
        placeholders["platforms"] = ", ".join(sorted(platforms))

    return errors, placeholders


def _notify_select(hass: HomeAssistant) -> selector.Selector:
    """Dropdown of registered notify.* services. custom_value lets users
    paste a service that isn't loaded yet."""
    services = sorted(hass.services.async_services().get("notify", {}).keys())
    options = [f"notify.{s}" for s in services]
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            custom_value=True,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _build_schema(
    hass: HomeAssistant,
    defaults: dict[str, Any],
    *,
    include_name: bool,
) -> vol.Schema:
    """Single-screen schema. ``include_name`` is False on the options flow
    (slug is derived from name and used in entity IDs, so renaming the
    instance after creation is not supported)."""
    fields: dict[Any, Any] = {}

    if include_name:
        fields[
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, ""))
        ] = str

    fields[
        vol.Optional(
            CONF_LIGHT_ENTITIES,
            default=defaults.get(CONF_LIGHT_ENTITIES, []),
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="light", multiple=True)
    )

    fields[
        vol.Optional(
            CONF_MEDIA_PLAYER_ENTITIES,
            default=defaults.get(CONF_MEDIA_PLAYER_ENTITIES, []),
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="media_player", multiple=True)
    )

    fields[
        vol.Optional(
            CONF_PERSON_ENTITY,
            description={
                "suggested_value": defaults.get(CONF_PERSON_ENTITY, "")
            },
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="person")
    )

    fields[
        vol.Optional(
            CONF_CONDITION_ENTITY,
            description={
                "suggested_value": defaults.get(CONF_CONDITION_ENTITY, "")
            },
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="binary_sensor")
    )

    notify = _notify_select(hass)
    fields[
        vol.Optional(
            CONF_NOTIFY_TARGET_STANDARD,
            description={
                "suggested_value": defaults.get(
                    CONF_NOTIFY_TARGET_STANDARD, ""
                )
            },
        )
    ] = notify

    fields[
        vol.Optional(
            CONF_NOTIFY_TARGET_URGENT,
            description={
                "suggested_value": defaults.get(CONF_NOTIFY_TARGET_URGENT, "")
            },
        )
    ] = notify

    for key in (CONF_BEFORE_SCRIPT, CONF_AFTER_SCRIPT):
        fields[
            vol.Optional(
                key,
                description={"suggested_value": defaults.get(key, "")},
            )
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="script")
        )

    return vol.Schema(fields)


def _validate_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
    *,
    require_name: bool,
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    """Validate the single-screen form. Returns (errors, placeholders, data).

    ``data`` is the cleaned dict ready for entry.data; only meaningful when
    ``errors`` is empty.
    """
    errors: dict[str, str] = {}
    placeholders: dict[str, Any] = {}
    data: dict[str, Any] = {}

    if require_name:
        name = (user_input.get(CONF_NAME) or "").strip()
        slug = slugify(name)
        if not slug:
            errors[CONF_NAME] = "invalid_name"
        else:
            data[CONF_NAME] = name
            data[CONF_SLUG] = slug

    # Lights and media players are both individually optional, but an alarm
    # that does nothing makes no sense, so require at least one of the two
    # (#22 — lights-only or music-only are both valid).
    lights = list(user_input.get(CONF_LIGHT_ENTITIES) or [])
    players = list(user_input.get(CONF_MEDIA_PLAYER_ENTITIES) or [])

    if not lights and not players:
        errors[CONF_LIGHT_ENTITIES] = "need_light_or_media"
        errors[CONF_MEDIA_PLAYER_ENTITIES] = "need_light_or_media"
    else:
        data[CONF_LIGHT_ENTITIES] = lights
        data[CONF_MEDIA_PLAYER_ENTITIES] = players
        if players:
            player_errors, ph = _validate_players(hass, players)
            if player_errors:
                errors.update(player_errors)
                placeholders.update(ph)

    person = user_input.get(CONF_PERSON_ENTITY)
    if person:
        data[CONF_PERSON_ENTITY] = person

    condition = user_input.get(CONF_CONDITION_ENTITY)
    if condition:
        data[CONF_CONDITION_ENTITY] = condition

    for key in (CONF_BEFORE_SCRIPT, CONF_AFTER_SCRIPT):
        script = user_input.get(key)
        if script:
            data[key] = script

    for k in (CONF_NOTIFY_TARGET_STANDARD, CONF_NOTIFY_TARGET_URGENT):
        v = (user_input.get(k) or "").strip()
        if v:
            data[k] = v

    return errors, placeholders, data


class WakeAlarmConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-screen create flow."""

    VERSION = 4

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return WakeAlarmOptionsFlow(entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, Any] = {}

        if user_input is not None:
            errors, placeholders, data = _validate_input(
                self.hass, user_input, require_name=True
            )
            if not errors:
                await self.async_set_unique_id(data[CONF_SLUG])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=data[CONF_NAME], data=data
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(
                self.hass, user_input or {}, include_name=True
            ),
            errors=errors,
            description_placeholders=placeholders,
        )


class WakeAlarmOptionsFlow(OptionsFlow):
    """Single-screen options flow. Name/slug are intentionally locked."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, Any] = {}
        defaults = dict(self._entry.data)

        if user_input is not None:
            errors, placeholders, new_data = _validate_input(
                self.hass, user_input, require_name=False
            )
            if not errors:
                # Preserve immutable fields (name, slug) from the existing entry.
                merged = dict(self._entry.data)
                merged.update(new_data)
                # Drop optional fields that were cleared in this submit.
                for k in (
                    CONF_PERSON_ENTITY,
                    CONF_CONDITION_ENTITY,
                    CONF_BEFORE_SCRIPT,
                    CONF_AFTER_SCRIPT,
                    CONF_NOTIFY_TARGET_STANDARD,
                    CONF_NOTIFY_TARGET_URGENT,
                ):
                    if k not in new_data:
                        merged.pop(k, None)
                self.hass.config_entries.async_update_entry(
                    self._entry, data=merged
                )
                return self.async_create_entry(title="", data={})
            defaults = {**defaults, **user_input}

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(
                self.hass, defaults, include_name=False
            ),
            errors=errors,
            description_placeholders=placeholders,
        )
