"""Regression tests for the Lovelace card auto-registration (#19, #20).

These drive ``_async_register_card`` directly against a real frontend so the
two failure modes are exercised in isolation:

  * #20 — ``_read_integration_version()`` opened manifest.json synchronously in
    the event loop. PHACC enables HA's blocking-IO protection, so the old code
    raises here; the loader-based version read does not.
  * #19 — the static path was registered before the "already registered" guard
    flag was set, so two concurrent entry setups both registered the route and
    the second raised ``RuntimeError``. Claiming the flag before the await fixes
    it.

Both tests use the ``card_frontend`` fixture, which provides ``http`` plus the
``add_extra_js_url`` data store that ``_async_register_card`` writes to (the real
``frontend`` component can't be set up under PHACC — see the fixture).
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant.loader import async_get_integration

from custom_components.wake_alarm import _async_register_card
from custom_components.wake_alarm.const import DOMAIN

_CARD_URL_BASE = "/wake_alarm/wake-alarm-card.js"


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
