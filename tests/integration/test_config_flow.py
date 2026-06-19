"""Config / options flow tests (#40).

`config_flow.py` was ~13% covered. These pin the validation surface
(`need_light_or_media`, player grouping / platform / availability checks) and
the options-flow "drop a cleared optional field" round-trip — the bit most
likely to silently break if `_validate_input` ever stops omitting falsy
optionals from its cleaned data.
"""
from __future__ import annotations

import homeassistant.config_entries as _config_entries
import pytest
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wake_alarm.config_flow import (
    _validate_input,
    _validate_players,
)
from custom_components.wake_alarm.const import (
    CONF_AFTER_SCRIPT,
    CONF_AT_ALARM_SCRIPT,
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

pytestmark = pytest.mark.skipif(
    not hasattr(_config_entries, "ConfigFlowResult"),
    reason="integration config_flow requires ConfigFlowResult (HA 2024.4+)",
)


# -------------------- _validate_input --------------------


async def test_validate_input_requires_light_or_media(hass) -> None:
    errors, _ph, _data = _validate_input(
        hass, {CONF_NAME: "Test"}, require_name=True
    )
    assert errors[CONF_LIGHT_ENTITIES] == "need_light_or_media"
    assert errors[CONF_MEDIA_PLAYER_ENTITIES] == "need_light_or_media"


async def test_validate_input_lights_only_ok(hass) -> None:
    errors, _ph, data = _validate_input(
        hass,
        {CONF_NAME: "Test", CONF_LIGHT_ENTITIES: ["light.x"]},
        require_name=True,
    )
    assert errors == {}
    assert data[CONF_SLUG] == "test"
    assert data[CONF_LIGHT_ENTITIES] == ["light.x"]
    assert data[CONF_MEDIA_PLAYER_ENTITIES] == []


async def test_validate_input_invalid_name(hass) -> None:
    # Whitespace-only name strips to "" → slug is empty → invalid_name.
    errors, _ph, _data = _validate_input(
        hass, {CONF_NAME: "   ", CONF_LIGHT_ENTITIES: ["light.x"]},
        require_name=True,
    )
    assert errors[CONF_NAME] == "invalid_name"


async def test_validate_input_drops_empty_optionals(hass) -> None:
    errors, _ph, data = _validate_input(
        hass,
        {
            CONF_NAME: "Test",
            CONF_LIGHT_ENTITIES: ["light.x"],
            CONF_PERSON_ENTITY: "",
            CONF_CONDITION_ENTITY: None,
            CONF_BEFORE_SCRIPT: "",
            CONF_NOTIFY_TARGET_STANDARD: "  ",
        },
        require_name=True,
    )
    assert errors == {}
    for k in (
        CONF_PERSON_ENTITY,
        CONF_CONDITION_ENTITY,
        CONF_BEFORE_SCRIPT,
        CONF_NOTIFY_TARGET_STANDARD,
    ):
        assert k not in data


# -------------------- _validate_players --------------------


def _add_player(
    hass,
    registry,
    object_id: str,
    platform: str,
    *,
    features: int = int(MediaPlayerEntityFeature.GROUPING),
    available: bool = True,
) -> str:
    ent = registry.async_get_or_create(
        "media_player", platform, f"uid_{object_id}", suggested_object_id=object_id
    )
    if available:
        hass.states.async_set(
            ent.entity_id, "idle", {"supported_features": features}
        )
    return ent.entity_id


async def test_validate_players_unavailable(hass) -> None:
    registry = er.async_get(hass)
    good = _add_player(hass, registry, "good", "sonos")
    bad = _add_player(hass, registry, "bad", "sonos", available=False)
    errors, ph = _validate_players(hass, [good, bad])
    assert errors[CONF_MEDIA_PLAYER_ENTITIES] == "media_player_unavailable"
    assert bad in ph["players"]


async def test_validate_players_no_grouping(hass) -> None:
    registry = er.async_get(hass)
    a = _add_player(hass, registry, "a", "sonos", features=0)
    b = _add_player(hass, registry, "b", "sonos", features=0)
    errors, _ph = _validate_players(hass, [a, b])
    assert errors[CONF_MEDIA_PLAYER_ENTITIES] == "no_grouping_support"


async def test_validate_players_mixed_platforms(hass) -> None:
    registry = er.async_get(hass)
    a = _add_player(hass, registry, "a", "sonos")
    b = _add_player(hass, registry, "b", "cast")
    errors, ph = _validate_players(hass, [a, b])
    assert errors[CONF_MEDIA_PLAYER_ENTITIES] == "mixed_platforms"
    assert "cast" in ph["platforms"] and "sonos" in ph["platforms"]


async def test_validate_players_single_player_is_fine(hass) -> None:
    registry = er.async_get(hass)
    a = _add_player(hass, registry, "a", "sonos", features=0)
    errors, _ph = _validate_players(hass, [a])
    assert errors == {}


# -------------------- create flow --------------------


async def test_create_flow_shows_error_with_no_targets(hass) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Bedroom",
            CONF_LIGHT_ENTITIES: [],
            CONF_MEDIA_PLAYER_ENTITIES: [],
        },
    )
    # Stays on the form with the validation error; no entry created.
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"][CONF_LIGHT_ENTITIES] == "need_light_or_media"


# -------------------- options flow drop round-trip --------------------


async def test_options_flow_drops_cleared_optional_fields(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Test Alarm",
            CONF_SLUG: "test",
            CONF_LIGHT_ENTITIES: ["light.bedroom"],
            CONF_MEDIA_PLAYER_ENTITIES: [],
            CONF_PERSON_ENTITY: "person.me",
            CONF_CONDITION_ENTITY: "binary_sensor.bed",
            CONF_BEFORE_SCRIPT: "script.before",
            CONF_AT_ALARM_SCRIPT: "script.at_alarm",
            CONF_AFTER_SCRIPT: "script.after",
            CONF_NOTIFY_TARGET_STANDARD: "notify.mobile",
            CONF_NOTIFY_TARGET_URGENT: "notify.mobile",
        },
        version=5,
        unique_id="test",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    # Submit keeping the light but clearing every optional field.
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_LIGHT_ENTITIES: ["light.bedroom"],
            CONF_MEDIA_PLAYER_ENTITIES: [],
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY

    data = dict(entry.data)
    for k in (
        CONF_PERSON_ENTITY,
        CONF_CONDITION_ENTITY,
        CONF_BEFORE_SCRIPT,
        CONF_AT_ALARM_SCRIPT,
        CONF_AFTER_SCRIPT,
        CONF_NOTIFY_TARGET_STANDARD,
        CONF_NOTIFY_TARGET_URGENT,
    ):
        assert k not in data
    # Immutable identity fields preserved.
    assert data[CONF_NAME] == "Test Alarm"
    assert data[CONF_SLUG] == "test"
    assert data[CONF_LIGHT_ENTITIES] == ["light.bedroom"]
