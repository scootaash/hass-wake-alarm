"""Music-sequence resilience tests (#45).

A player going unavailable mid-sequence (raising on a media_player service
call) must not abort the whole sequence or strand the rest. The sequence
routes its calls through ``_safe_call``, which logs and continues.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

import custom_components.wake_alarm.music_sequence as ms
from custom_components.wake_alarm.const import CONF_MEDIA_PLAYER_ENTITIES
from custom_components.wake_alarm.music_sequence import async_run_music_sequence


@pytest.fixture(autouse=True)
def _fast_timings(monkeypatch):
    """Zero the Sonos/queue settle delays so the real sequence runs instantly."""
    for const in (
        "_PLAY_QUEUE_SETTLE_SEC",
        "_RANDOM_SKIP_INTERVAL_SEC",
        "_UNJOIN_SETTLE_SEC",
        "_JOIN_SETTLE_SEC",
    ):
        monkeypatch.setattr(ms, const, 0)

MEDIA = {
    "content_id": "spotify:playlist:wake",
    "content_type": "playlist",
    "title": "Wake Up",
    "thumbnail": None,
}


class FakeCoordinator:
    """Minimal stand-in exposing what async_run_music_sequence reads."""

    def __init__(self, hass, players: list[str]) -> None:
        self.hass = hass
        self.slug = "test"
        self.entry = SimpleNamespace(data={CONF_MEDIA_PLAYER_ENTITIES: players})

    def current_media(self) -> dict:
        return MEDIA

    def read_number(self, key: str, default):
        # Instant fade keeps the test fast; everything else takes the default.
        return 0 if key == "music_fade_sec" else default


async def test_single_player_volume_failure_does_not_abort(hass) -> None:
    """A volume_set that raises is swallowed; play_media still happens."""
    bad = "media_player.bad"
    hass.states.async_set(bad, "idle")  # no GROUPING feature → single path

    volume_calls: list[str] = []

    async def volume_handler(call) -> None:
        volume_calls.append(call.data["entity_id"])
        raise HomeAssistantError("device offline")

    hass.services.async_register("media_player", "volume_set", volume_handler)
    play = async_mock_service(hass, "media_player", "play_media")

    coord = FakeCoordinator(hass, [bad])

    # Must not raise despite every volume_set failing.
    await async_run_music_sequence(coord, asyncio.Event())
    await hass.async_block_till_done()

    assert volume_calls  # it tried
    assert len(play) == 1  # and still issued play_media


async def test_one_of_two_players_failing_still_plays_the_other(hass) -> None:
    """One player raising on volume_set must not stop the other from playing."""
    good, bad = "media_player.good", "media_player.bad"
    # No GROUPING feature on either → single-player (fan-out) path.
    hass.states.async_set(good, "idle")
    hass.states.async_set(bad, "idle")

    played: list[str] = []

    async def play_handler(call) -> None:
        played.append(call.data["entity_id"])

    async def volume_handler(call) -> None:
        if call.data["entity_id"] == bad:
            raise HomeAssistantError("device offline")

    hass.services.async_register("media_player", "volume_set", volume_handler)
    hass.services.async_register("media_player", "play_media", play_handler)

    coord = FakeCoordinator(hass, [good, bad])

    await async_run_music_sequence(coord, asyncio.Event())
    await hass.async_block_till_done()

    # The bad player's volume failure didn't abort the loop before the good one.
    assert good in played
    assert bad in played


async def test_single_player_shuffles_and_random_skips(hass) -> None:
    """A single player shuffles and skips a random 1-4 tracks so it doesn't
    always start on the same track (parity with the multi-Sonos path)."""
    player = "media_player.solo"
    hass.states.async_set(player, "idle")  # no GROUPING feature → single path
    shuffle = async_mock_service(hass, "media_player", "shuffle_set")
    play = async_mock_service(hass, "media_player", "play_media")
    skips = async_mock_service(hass, "media_player", "media_next_track")
    async_mock_service(hass, "media_player", "volume_set")

    coord = FakeCoordinator(hass, [player])
    await async_run_music_sequence(coord, asyncio.Event())
    await hass.async_block_till_done()

    assert len(shuffle) == 1
    assert shuffle[0].data["shuffle"] is True
    assert len(play) == 1
    assert 1 <= len(skips) <= 4  # random 1-4 next-track calls


async def test_single_player_skip_cancels_cleanly(hass) -> None:
    """A cancel during the single-player settle/skip aborts without playing."""
    player = "media_player.solo"
    hass.states.async_set(player, "idle")
    async_mock_service(hass, "media_player", "shuffle_set")
    async_mock_service(hass, "media_player", "play_media")
    async_mock_service(hass, "media_player", "media_next_track")
    async_mock_service(hass, "media_player", "volume_set")

    cancel = asyncio.Event()
    cancel.set()  # already cancelled
    coord = FakeCoordinator(hass, [player])
    # Must return promptly without raising.
    await async_run_music_sequence(coord, cancel)
    await hass.async_block_till_done()
