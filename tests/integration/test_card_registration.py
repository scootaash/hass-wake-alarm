"""Regression tests for the Lovelace card auto-registration.

These drive ``_async_register_card`` directly against a real frontend so the
failure modes are exercised in isolation:

  * #20 — ``_read_integration_version()`` opened manifest.json synchronously in
    the event loop. PHACC enables HA's blocking-IO protection, so the old code
    raises here; the loader-based version read does not.
  * #19 — the static path was registered before the "already registered" guard
    flag was set, so two concurrent entry setups both registered the route and
    the second raised ``RuntimeError``. Claiming the flag before the await fixes
    it.
  * "Custom element doesn't exist: wake-alarm-card" — ``add_extra_js_url``
    puts the bundle in the page HTML, where it races HA's app script. The app
    swaps in a polyfilled ``window.customElements`` as it starts, and elements
    defined before that are invisible to HA. Pages rendered before the
    integration set up (HA still starting) never got the bundle at all. The card
    is now a stored Lovelace resource instead, loaded by the dashboard after the
    app is up, and ``add_extra_js_url`` is only a fallback.

All tests use the ``card_frontend`` fixture, which provides ``http`` plus the
``add_extra_js_url`` data store that ``_async_register_card`` writes to (the real
``frontend`` component can't be set up under PHACC — see the fixture). The
resource tests add the real ``lovelace`` component via ``lovelace_resources``.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wake_alarm import _async_register_card
from custom_components.wake_alarm.const import DOMAIN

_CARD_URL_BASE = "/wake_alarm/wake-alarm-card.js"
_OTHER_CARD = {"id": "other", "type": "module", "url": "/hacsfiles/other/other.js"}


def _seed_resources(hass_storage, *items: dict) -> None:
    """Pre-populate stored Lovelace resources, as a real install would have."""
    hass_storage["lovelace_resources"] = {
        "version": 1,
        "minor_version": 1,
        "key": "lovelace_resources",
        "data": {"items": [dict(item) for item in items]},
    }


async def _expected_versioned_url(hass) -> str:
    integration = await async_get_integration(hass, DOMAIN)
    version = str(integration.version) if integration.version else "dev"
    return f"{_CARD_URL_BASE}?v={version}"


async def test_register_card_reads_version_via_loader(
    hass, card_frontend
) -> None:
    """#20: the cache-bust version comes from the async loader, not a blocking
    ``open()`` of manifest.json.

    Patch the loader to report a sentinel version and assert the registered URL
    uses it. The old synchronous code read the version straight off disk and
    would serve the real manifest version instead, so this fails pre-fix.
    """
    fake = SimpleNamespace(version="9.9.9-test")
    with patch(
        "custom_components.wake_alarm.async_get_integration",
        new=AsyncMock(return_value=fake),
    ):
        await _async_register_card(hass)

    assert f"{_CARD_URL_BASE}?v=9.9.9-test" in card_frontend.urls


async def test_concurrent_registration_no_duplicate_route(
    hass, card_frontend
) -> None:
    """Concurrent entry setups register the card exactly once (#19)."""
    # HA sets up multiple entries of a domain concurrently. Pre-fix both calls
    # passed the guard and the second raised "method GET is already registered".
    await asyncio.gather(
        _async_register_card(hass),
        _async_register_card(hass),
    )

    expected = await _expected_versioned_url(hass)
    urls = card_frontend.urls
    assert expected in urls
    # The card URL is registered exactly once, not duplicated.
    assert sum(1 for url in urls if url == expected) == 1


async def test_register_card_persists_lovelace_resource(
    hass, card_frontend, lovelace_resources
) -> None:
    """The card is stored as a Lovelace resource and not injected into the page.

    An injected copy evaluates before HA's app swaps in its registry polyfill,
    which hides the card from HA; with the same URL it would also pre-empt the
    resource load (the browser evaluates a module URL once).
    """
    await _async_register_card(hass)

    expected = await _expected_versioned_url(hass)
    assert [
        (item["type"], item["url"]) for item in lovelace_resources.async_items()
    ] == [("module", expected)]
    assert card_frontend.urls == frozenset()


async def test_register_card_keeps_user_resources(
    hass, hass_storage, lovelace_resources
) -> None:
    """Registering into a not-yet-loaded collection keeps stored resources.

    On the 2024.6 floor the collection's create doesn't load storage first, so
    creating into it cold saved over every resource the user already had.
    """
    _seed_resources(hass_storage, _OTHER_CARD)

    await _async_register_card(hass)

    expected = await _expected_versioned_url(hass)
    items = {item["url"]: item["type"] for item in lovelace_resources.async_items()}
    assert items == {_OTHER_CARD["url"]: "module", expected: "module"}


async def test_register_card_updates_stale_resource_in_place(
    hass, hass_storage, lovelace_resources
) -> None:
    """An older-version or hand-added copy of our resource is updated, not
    duplicated, and extra copies are dropped (two URLs would evaluate the bundle
    twice and the second define() throws)."""
    _seed_resources(
        hass_storage,
        _OTHER_CARD,
        {"id": "ours", "type": "js", "url": f"{_CARD_URL_BASE}?v=0.0.1"},
        {"id": "dupe", "type": "module", "url": _CARD_URL_BASE},
    )

    await _async_register_card(hass)

    expected = await _expected_versioned_url(hass)
    items = {item["id"]: item for item in lovelace_resources.async_items()}
    assert items == {
        "other": _OTHER_CARD,
        "ours": {"id": "ours", "type": "module", "url": expected},
    }


async def _setup_yaml_resources(hass, *urls: str) -> None:
    # resource_mode only exists on newer cores; it defaults to mode.
    assert await async_setup_component(
        hass,
        "lovelace",
        {
            "lovelace": {
                "mode": "yaml",
                "resources": [{"type": "module", "url": url} for url in urls],
            }
        },
    )


async def test_register_card_yaml_mode_falls_back_to_extra_module(
    hass, card_frontend
) -> None:
    """YAML-mode resources are read-only: without our bundle listed there, the
    page-injected extra module is the only way to load the card."""
    await _setup_yaml_resources(hass, _OTHER_CARD["url"])

    await _async_register_card(hass)

    assert await _expected_versioned_url(hass) in card_frontend.urls


async def test_register_card_yaml_mode_with_card_listed(hass, card_frontend) -> None:
    """If the user lists our bundle in YAML resources, don't also inject it into
    the page: that copy would run first, before HA's registry polyfill."""
    await _setup_yaml_resources(hass, _OTHER_CARD["url"], _CARD_URL_BASE)

    await _async_register_card(hass)

    assert card_frontend.urls == frozenset()


async def test_removing_last_alarm_drops_resource(
    hass, hass_storage, lovelace_resources
) -> None:
    """The resource goes with the last alarm, so an uninstall leaves no
    dashboard resource that 404s; other resources are untouched."""
    _seed_resources(hass_storage, _OTHER_CARD)
    first = MockConfigEntry(domain=DOMAIN, version=6, data={})
    second = MockConfigEntry(domain=DOMAIN, version=6, data={})
    first.add_to_hass(hass)
    second.add_to_hass(hass)
    await _async_register_card(hass)

    def card_resources() -> list[str]:
        return [
            item["url"]
            for item in lovelace_resources.async_items()
            if item["url"].startswith(_CARD_URL_BASE)
        ]

    assert await hass.config_entries.async_remove(first.entry_id)
    assert card_resources() == [await _expected_versioned_url(hass)]

    assert await hass.config_entries.async_remove(second.entry_id)
    assert card_resources() == []
    assert [item["id"] for item in lovelace_resources.async_items()] == ["other"]
