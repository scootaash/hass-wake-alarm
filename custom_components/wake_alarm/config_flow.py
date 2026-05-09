"""Config and options flow for Wake Alarm."""
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
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.util import slugify

from .const import (
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


class _CommonFlow:
    """Shared step handlers for create + options flows."""

    hass: HomeAssistant
    _data: dict[str, Any]

    def _lights_schema(self, defaults: dict[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_LIGHT_ENTITIES,
                    default=defaults.get(CONF_LIGHT_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="light", multiple=True)
                ),
            }
        )

    def _media_players_schema(self, defaults: dict[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(
                    CONF_MEDIA_PLAYER_ENTITIES,
                    default=defaults.get(CONF_MEDIA_PLAYER_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player", multiple=True
                    )
                ),
            }
        )

    def _presence_schema(self, defaults: dict[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_PERSON_ENTITY,
                    description={
                        "suggested_value": defaults.get(CONF_PERSON_ENTITY, "")
                    },
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="person")
                ),
            }
        )

    def _notify_schema(self, defaults: dict[str, Any]) -> vol.Schema:
        # Build a dropdown of registered notify.* services. custom_value=True
        # so power users can paste a service that isn't loaded yet.
        notify_services = sorted(
            self.hass.services.async_services().get("notify", {}).keys()
        )
        options = [f"notify.{name}" for name in notify_services]
        select = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=options,
                custom_value=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        return vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_TARGET_STANDARD,
                    description={
                        "suggested_value": defaults.get(
                            CONF_NOTIFY_TARGET_STANDARD, ""
                        )
                    },
                ): select,
                vol.Optional(
                    CONF_NOTIFY_TARGET_URGENT,
                    description={
                        "suggested_value": defaults.get(
                            CONF_NOTIFY_TARGET_URGENT, ""
                        )
                    },
                ): select,
            }
        )


class WakeAlarmConfigFlow(ConfigFlow, _CommonFlow, domain=DOMAIN):
    """Initial config flow.

    Media content is intentionally NOT collected here — the user picks media
    after setup via the card's media browser, which calls the
    wake_alarm.set_media service.
    """

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return WakeAlarmOptionsFlow(entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            slug = slugify(name)
            if not slug:
                errors[CONF_NAME] = "invalid_name"
            else:
                await self.async_set_unique_id(slug)
                self._abort_if_unique_id_configured()
                self._data[CONF_NAME] = name
                self._data[CONF_SLUG] = slug
                return await self.async_step_lights()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME): str}),
            errors=errors,
        )

    async def async_step_lights(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_LIGHT_ENTITIES] = user_input[CONF_LIGHT_ENTITIES]
            return await self.async_step_media_players()
        return self.async_show_form(
            step_id="lights", data_schema=self._lights_schema({})
        )

    async def async_step_media_players(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, Any] = {}
        if user_input is not None:
            players = user_input[CONF_MEDIA_PLAYER_ENTITIES]
            errors, placeholders = _validate_players(self.hass, players)
            if not errors:
                self._data[CONF_MEDIA_PLAYER_ENTITIES] = players
                return await self.async_step_presence()
        return self.async_show_form(
            step_id="media_players",
            data_schema=self._media_players_schema(self._data),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_presence(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            person = user_input.get(CONF_PERSON_ENTITY)
            if person:
                self._data[CONF_PERSON_ENTITY] = person
            return await self.async_step_notifications()
        return self.async_show_form(
            step_id="presence", data_schema=self._presence_schema({})
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            for k in (CONF_NOTIFY_TARGET_STANDARD, CONF_NOTIFY_TARGET_URGENT):
                v = (user_input.get(k) or "").strip()
                if v:
                    self._data[k] = v
            return await self.async_step_confirm()
        return self.async_show_form(
            step_id="notifications", data_schema=self._notify_schema({})
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._data[CONF_NAME], data=self._data
            )
        summary = "\n".join(
            f"- {k}: {v}"
            for k, v in self._data.items()
            if k != CONF_SLUG
        )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"summary": summary},
        )


class WakeAlarmOptionsFlow(OptionsFlow, _CommonFlow):
    """Options flow re-runs the same steps (without name).

    Media selection is changed via the card, not here.
    """

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._data: dict[str, Any] = dict(entry.data)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_lights()

    async def async_step_lights(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_LIGHT_ENTITIES] = user_input[CONF_LIGHT_ENTITIES]
            return await self.async_step_media_players()
        return self.async_show_form(
            step_id="lights", data_schema=self._lights_schema(self._data)
        )

    async def async_step_media_players(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, Any] = {}
        if user_input is not None:
            players = user_input[CONF_MEDIA_PLAYER_ENTITIES]
            errors, placeholders = _validate_players(self.hass, players)
            if not errors:
                self._data[CONF_MEDIA_PLAYER_ENTITIES] = players
                return await self.async_step_presence()
        return self.async_show_form(
            step_id="media_players",
            data_schema=self._media_players_schema(self._data),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_presence(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            person = user_input.get(CONF_PERSON_ENTITY)
            if person:
                self._data[CONF_PERSON_ENTITY] = person
            else:
                self._data.pop(CONF_PERSON_ENTITY, None)
            return await self.async_step_notifications()
        return self.async_show_form(
            step_id="presence", data_schema=self._presence_schema(self._data)
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            for k in (CONF_NOTIFY_TARGET_STANDARD, CONF_NOTIFY_TARGET_URGENT):
                v = (user_input.get(k) or "").strip()
                if v:
                    self._data[k] = v
                else:
                    self._data.pop(k, None)
            self.hass.config_entries.async_update_entry(
                self._entry, data=self._data
            )
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="notifications", data_schema=self._notify_schema(self._data)
        )
