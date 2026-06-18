"""Full config-entry setup/teardown smoke test.

Unlike the coordinator tests (which drive the state machine directly), this
runs the real ``config_entries.async_setup`` path end-to-end. All the entity
platforms set up fine; the step that breaks setup is ``_async_register_card``,
which is exactly what #19 and #20 are about:

  * #19 — the card's static path is registered unconditionally, so a second
    entry (or a reload) raises ``RuntimeError`` registering a duplicate route;
  * #20 — ``_read_integration_version()`` does a blocking ``open()`` of
    manifest.json in the event loop.

Card registration is also tightly coupled to the frontend (it calls
``add_extra_js_url``), which isn't satisfiable in the PHACC test environment.
Hardening that path — guarding the static-path registration, reading the
manifest off-loop, and tolerating an unavailable frontend — is what #19/#20
should deliver, after which this becomes a real passing gate. So it's marked
``xfail`` (non-strict): remove the marker once that lands and it flips green.
"""
from __future__ import annotations

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wake_alarm.const import (
    CONF_LIGHT_ENTITIES,
    CONF_MEDIA_PLAYER_ENTITIES,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
    CONF_SLUG,
    DOMAIN,
)


@pytest.mark.xfail(
    reason="card registration (_async_register_card) breaks full setup: "
    "#19 duplicate static route, #20 blocking manifest open(), and "
    "frontend coupling not satisfiable under PHACC",
    strict=False,
)
async def test_full_entry_setup_and_unload(hass) -> None:
    """The entry sets up its platforms and unloads cleanly."""
    # The integration registers its Lovelace card as a static path via
    # hass.http, so the http stack must be up for a realistic run.
    assert await async_setup_component(hass, "http", {})

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="smoke",
        data={
            CONF_NAME: "Smoke",
            CONF_SLUG: "smoke",
            CONF_LIGHT_ENTITIES: ["light.bedroom"],
            CONF_MEDIA_PLAYER_ENTITIES: ["media_player.bedroom"],
            CONF_NOTIFY_TARGET_STANDARD: "notify.mobile",
            CONF_NOTIFY_TARGET_URGENT: "notify.mobile",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert coordinator is not None
    # The enable switch should have been created by the switch platform.
    assert hass.states.get("switch.smoke_enabled") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
