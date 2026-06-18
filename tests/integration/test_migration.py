"""Config-entry migration tests (#39).

`async_migrate_entry` had zero coverage. These pin the v1→v4 cascade (day-key
registry rename + version bumps), the additive v2/v3 no-ops, and the
downgrade guard — exactly the logic a future regression (e.g. flipping the
cascade ``if``s to ``elif``) would silently break.
"""
from __future__ import annotations

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wake_alarm import async_migrate_entry
from custom_components.wake_alarm.const import CONF_SLUG, DOMAIN

# old day-key (v1) → new day-key (v2+), in calendar order.
DAY_OLD_NEW = [
    ("mon", "d1_mon"),
    ("tue", "d2_tue"),
    ("wed", "d3_wed"),
    ("thu", "d4_thu"),
    ("fri", "d5_fri"),
    ("sat", "d6_sat"),
    ("sun", "d7_sun"),
]


async def test_v1_migrates_to_v4_and_renames_day_switches(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SLUG: "test", CONF_NAME: "Test Alarm"},
        version=1,
        unique_id="test",
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    for old, _new in DAY_OLD_NEW:
        registry.async_get_or_create(
            "switch",
            DOMAIN,
            f"{entry.entry_id}_{old}",
            config_entry=entry,
            suggested_object_id=f"test_{old}",
        )

    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 4

    for old, new in DAY_OLD_NEW:
        # Old unique_id is gone; new one resolves to the renamed entity_id.
        assert (
            registry.async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_{old}")
            is None
        )
        assert (
            registry.async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_{new}")
            == f"switch.test_{new}"
        )


@pytest.mark.parametrize("version", [2, 3])
async def test_v2_and_v3_bump_to_v4(hass, version: int) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SLUG: f"x{version}", CONF_NAME: "X"},
        version=version,
        unique_id=f"x{version}",
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 4
    # Additive steps don't touch stored data.
    assert entry.data[CONF_SLUG] == f"x{version}"


async def test_v4_is_a_noop(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SLUG: "y", CONF_NAME: "Y"},
        version=4,
        unique_id="y",
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 4


async def test_future_version_downgrade_guard_returns_false(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SLUG: "z", CONF_NAME: "Z"},
        version=5,
        unique_id="z",
    )
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 5
