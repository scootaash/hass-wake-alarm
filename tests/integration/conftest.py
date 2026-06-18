"""Home-Assistant-backed fixtures for driving the coordinator directly.

These tests construct a real ``WakeAlarmCoordinator`` against the PHACC ``hass``
fixture, set the dependency-entity states the coordinator reads, and exercise
the full scheduling state machine with controllable time
(``freezer`` + ``async_fire_time_changed``) and mocked side-effects.

Driving the coordinator directly — rather than ``config_entries.async_setup`` —
keeps the suite focused on the state machine; the full entry-setup path (and the
card registration that #19/#20 were about) is covered by ``test_setup.py`` and
``test_card_registration.py`` via the ``card_frontend`` fixture below.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_NAME
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.wake_alarm.const import (
    CONF_LIGHT_ENTITIES,
    CONF_MEDIA_PLAYER_ENTITIES,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
    CONF_SLUG,
    DAYS,
    DOMAIN,
)
from custom_components.wake_alarm.coordinator import WakeAlarmCoordinator

DEFAULT_SLUG = "test"

# A non-empty media selection so current_media() returns something by default.
DEFAULT_MEDIA = {
    "media_content_id": "spotify:playlist:wake",
    "media_content_type": "playlist",
    "title": "Wake Up",
    "thumbnail": None,
}

_UNSET = object()


async def _force_utc(hass) -> None:
    """Pin the test hass to UTC so alarm_time date math is deterministic.

    PHACC defaults to US/Pacific to flush out tz bugs; DST handling is already
    covered by the pure scheduling tests, so here we want a stable wall clock.
    """
    if hasattr(hass.config, "async_set_time_zone"):
        await hass.config.async_set_time_zone("UTC")
    else:  # HA < 2024.6
        hass.config.set_time_zone("UTC")


class StubMediaSensor:
    """Stand-in for the media-selection sensor the coordinator queries."""

    def __init__(self, data: dict | None) -> None:
        self._data = data

    def selection_data(self) -> dict | None:
        return self._data


class GatedRunner:
    """Controllable fake for async_run_light_ramp / async_run_music_sequence.

    Defaults to completing immediately. Call ``block()`` before firing a timer
    to hold the runner in its running state (so the coordinator stays in
    RAMPING/PLAYING and the transition can be observed), then ``release()`` to
    let it finish. Set ``exc`` to make it raise — used to prove the light path
    failing never stops the music path.
    """

    def __init__(self, label: str) -> None:
        self.label = label
        self.calls = 0
        self.kwargs_log: list[dict] = []
        self.started = asyncio.Event()
        self.exc: Exception | None = None
        self._release = asyncio.Event()
        self._release.set()

    def block(self) -> None:
        self.started.clear()
        self._release.clear()

    def release(self) -> None:
        self._release.set()

    async def __call__(self, coordinator, cancel_event, **kwargs) -> None:
        self.calls += 1
        self.kwargs_log.append(kwargs)
        self.started.set()
        if self.exc is not None:
            raise self.exc
        # Finish on explicit release OR when the coordinator cancels us
        # (snooze/dismiss/unload set the cancel_event).
        rel = asyncio.ensure_future(self._release.wait())
        can = asyncio.ensure_future(cancel_event.wait())
        try:
            await asyncio.wait(
                {rel, can}, return_when=asyncio.FIRST_COMPLETED
            )
        finally:
            rel.cancel()
            can.cancel()


class Env:
    """Bundle of hass + mocks + builders handed to each test."""

    def __init__(
        self, hass, ramp, music, std, unavail, no_media, media_calls
    ) -> None:
        self.hass = hass
        self.ramp = ramp
        self.music = music
        self.send_standard = std
        self.send_player_unavailable = unavail
        self.send_no_media = no_media
        self.media_calls = media_calls
        self._coordinators: list[WakeAlarmCoordinator] = []

    def make_entry(self, **overrides) -> MockConfigEntry:
        data = {
            CONF_NAME: "Test Alarm",
            CONF_SLUG: DEFAULT_SLUG,
            CONF_LIGHT_ENTITIES: ["light.bedroom"],
            CONF_MEDIA_PLAYER_ENTITIES: ["media_player.bedroom"],
            CONF_NOTIFY_TARGET_STANDARD: "notify.mobile",
            CONF_NOTIFY_TARGET_URGENT: "notify.mobile",
        }
        data.update(overrides)
        # Drop keys explicitly set to None (e.g. no person configured).
        data = {k: v for k, v in data.items() if v is not None}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            version=2,
            unique_id=data[CONF_SLUG],
        )
        entry.add_to_hass(self.hass)
        return entry

    def set_states(
        self,
        slug: str = DEFAULT_SLUG,
        *,
        enabled: bool = True,
        alarm_time: str = "07:00:00",
        days: set[int] | None = None,
        length_min: int = 15,
        **numbers,
    ) -> None:
        """Set the entity states the coordinator reads on every recompute."""
        hass = self.hass
        hass.states.async_set(
            f"switch.{slug}_enabled", "on" if enabled else "off"
        )
        hass.states.async_set(f"time.{slug}_alarm_time", alarm_time)
        hass.states.async_set(f"number.{slug}_length_min", str(length_min))
        enabled_days = days if days is not None else set(range(5))  # Mon-Fri
        for idx, day in enumerate(DAYS):
            hass.states.async_set(
                f"switch.{slug}_{day}", "on" if idx in enabled_days else "off"
            )
        for key, val in numbers.items():
            hass.states.async_set(f"number.{slug}_{key}", str(val))

    async def build(
        self,
        entry: MockConfigEntry,
        *,
        media: object = _UNSET,
        **state_kwargs,
    ) -> WakeAlarmCoordinator:
        """Set states, construct the coordinator, run async_setup.

        Call this while the clock is frozen at the desired "now" so the initial
        schedule (and any restart catch-up) is computed against it.
        """
        self.set_states(entry.data[CONF_SLUG], **state_kwargs)
        # Configured players default to a playable (available) state; tests
        # that exercise the unavailable path override this after build().
        for player in entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []:
            self.hass.states.async_set(player, "idle")
        coord = WakeAlarmCoordinator(self.hass, entry)
        selection = DEFAULT_MEDIA if media is _UNSET else media
        coord.register_media_sensor(StubMediaSensor(selection))
        self._coordinators.append(coord)
        await coord.async_setup()
        await self.hass.async_block_till_done()
        return coord

    async def teardown(self) -> None:
        for coord in self._coordinators:
            await coord.async_unload()
        await self.hass.async_block_till_done()


@pytest.fixture
async def card_frontend(hass):
    """Minimal frontend stack for exercising ``_async_register_card``.

    PHACC can't set up the real ``frontend`` component (the compiled
    ``hass_frontend`` package isn't installed), so we bring up ``http`` — needed
    for static-path registration — and initialise the ``add_extra_js_url`` data
    store exactly as ``frontend.async_setup`` does. Returns the ``UrlManager``
    whose ``.urls`` the card URL is added to.
    """
    from homeassistant.components.frontend import (
        DATA_EXTRA_MODULE_URL,
        UrlManager,
    )
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, "http", {})
    try:
        manager = UrlManager(lambda *args: None, [])  # HA 2024.6+
    except TypeError:
        manager = UrlManager([])  # HA < 2024.6 (no on_change arg)
    hass.data[DATA_EXTRA_MODULE_URL] = manager
    return manager


@pytest.fixture
async def env(hass):
    """Coordinator test harness: patched runners/notifications + builders."""
    await _force_utc(hass)
    ramp = GatedRunner("ramp")
    music = GatedRunner("music")
    cov = "custom_components.wake_alarm.coordinator"
    with (
        patch(f"{cov}.async_run_light_ramp", ramp),
        patch(f"{cov}.async_run_music_sequence", music),
        patch(f"{cov}.async_send_standard", new=AsyncMock()) as std,
        patch(
            f"{cov}.async_send_player_unavailable", new=AsyncMock()
        ) as unavail,
        patch(f"{cov}.async_send_no_media", new=AsyncMock()) as no_media,
    ):
        media_calls = {
            name: async_mock_service(hass, "media_player", name)
            for name in ("media_pause", "media_stop", "unjoin")
        }
        environment = Env(
            hass, ramp, music, std, unavail, no_media, media_calls
        )
        try:
            yield environment
        finally:
            await environment.teardown()
