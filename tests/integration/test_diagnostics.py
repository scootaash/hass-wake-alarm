"""Config-entry diagnostics tests.

Pins the redaction of person / notify targets and the shape of the coordinator
snapshot, so a bug report carries useful scheduler/state data and never leaks a
notify target or person entity.
"""
from __future__ import annotations

from homeassistant.components.diagnostics import REDACTED

from custom_components.wake_alarm.const import (
    CONF_LIGHT_ENTITIES,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
    CONF_PERSON_ENTITY,
    DOMAIN,
)
from custom_components.wake_alarm.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .test_coordinator import SAT, at


async def test_diagnostics_redacts_and_snapshots(env, freezer) -> None:
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("person.me", "home")
    entry = env.make_entry(person_entity="person.me")
    coord = await env.build(entry, days=SAT)
    # The diagnostics handler resolves the coordinator from hass.data, exactly
    # as the real setup path registers it.
    env.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coord}

    diag = await async_get_config_entry_diagnostics(env.hass, entry)

    # Person + notify targets are redacted; useful entity lists are preserved.
    data = diag["entry"]["data"]
    assert data[CONF_PERSON_ENTITY] == REDACTED
    assert data[CONF_NOTIFY_TARGET_STANDARD] == REDACTED
    assert data[CONF_NOTIFY_TARGET_URGENT] == REDACTED
    assert data[CONF_LIGHT_ENTITIES] == ["light.bedroom"]

    # Coordinator snapshot reflects the armed-but-idle state.
    snap = diag["coordinator"]
    assert snap["state"] == "idle"
    assert snap["is_active"] is False
    assert snap["next_fire"] == at(7, 0).isoformat()
    assert snap["timers_armed"]["alarm"] is True
    assert snap["config_readback"]["enabled"] is True
    assert snap["config_readback"]["enabled_days"] == [5]
    assert snap["media_selected"] is True


async def test_diagnostics_without_coordinator(env, freezer) -> None:
    """Handler is robust if the entry has no live coordinator (mid-teardown)."""
    freezer.move_to(at(5, 0))
    entry = env.make_entry()
    # Intentionally do not register a coordinator in hass.data.
    diag = await async_get_config_entry_diagnostics(env.hass, entry)
    assert diag["coordinator"] is None
    assert diag["entry"]["data"][CONF_NOTIFY_TARGET_STANDARD] == REDACTED
