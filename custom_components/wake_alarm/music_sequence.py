"""Music sequence.

Two paths, ported from scripts.alarm_post_action_music in the legacy YAML.

Single player (or multi-player without GROUPING — the config flow blocks
the latter, but defensive):

    1. volume_set 0 on all configured players
    2. media_player.play_media on each
    3. linear fade 0 → target_volume across `music_fade_sec` seconds in
       `_FADE_STEPS` steps

Multi-player Sonos / GROUPING-capable:

    1.  media_player.unjoin on the first selected player (group coordinator)
    2.  3-second wait — UPnP Error 800 mitigation; skipping this in the
        legacy YAML caused intermittent failures
    3.  volume_set 0 on the coordinator (BEFORE play_media)
    4.  media_player.join with group_members = the rest
    5.  1-second settle for the group to form
    6.  volume_set 0 on each member (join does not propagate volume)
    7.  shuffle_set true on the coordinator
    8.  media_player.play_media on the coordinator with enqueue=replace
    9.  volume_set 0 on all members AGAIN — Sonos favourites can restore
        their own volume on play; this defends against a sudden blast
    10. 5-second wait for the queue to actually start
    11. synchronous linear fade across all members
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from homeassistant.components.media_player import MediaPlayerEntityFeature

from .const import (
    CONF_MEDIA_PLAYER_ENTITIES,
    DEFAULT_MUSIC_FADE_SEC,
    DEFAULT_VOLUME,
)

if TYPE_CHECKING:
    from .coordinator import WakeAlarmCoordinator

_LOGGER = logging.getLogger(__name__)

# Fixed fade granularity, mirrors the legacy YAML's `steps: 20`.
_FADE_STEPS = 20

# Sonos quirk timings.
_UNJOIN_SETTLE_SEC = 3
_JOIN_SETTLE_SEC = 1
_PLAY_QUEUE_SETTLE_SEC = 5


async def async_run_music_sequence(
    coordinator: "WakeAlarmCoordinator",
    cancel_event: asyncio.Event,
) -> None:
    """Run the appropriate path. Returns when sequence is done or cancelled."""
    players: list[str] = list(
        coordinator.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []
    )
    if not players:
        _LOGGER.warning(
            "no media players configured for %s; skipping music",
            coordinator.slug,
        )
        return

    selection = coordinator.current_media()
    if selection is None:
        # The coordinator gates on this in _async_start_music; this is just
        # a defensive guard if the sequence is invoked another way.
        _LOGGER.warning(
            "no media selected for %s; skipping music sequence",
            coordinator.slug,
        )
        return
    media_content_id: str = selection["content_id"]
    media_content_type: str = selection["content_type"]

    target_volume = float(coordinator.read_number("volume", DEFAULT_VOLUME))
    fade_sec = int(coordinator.read_number("music_fade_sec", DEFAULT_MUSIC_FADE_SEC))

    if len(players) > 1 and _all_support_grouping(coordinator, players):
        await _run_multi_player_sonos(
            coordinator,
            players,
            media_content_id,
            media_content_type,
            target_volume,
            fade_sec,
            cancel_event,
        )
    else:
        await _run_single_player(
            coordinator,
            players,
            media_content_id,
            media_content_type,
            target_volume,
            fade_sec,
            cancel_event,
        )


# -------------------- single-player path --------------------


async def _run_single_player(
    coordinator: "WakeAlarmCoordinator",
    players: list[str],
    media_content_id: str,
    media_content_type: str,
    target_volume: float,
    fade_sec: int,
    cancel_event: asyncio.Event,
) -> None:
    await asyncio.gather(*(_volume_set(coordinator, p, 0.0) for p in players))
    if cancel_event.is_set():
        return

    for player in players:
        await coordinator.hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": player,
                "media_content_id": media_content_id,
                "media_content_type": media_content_type,
            },
            blocking=False,
        )
    if cancel_event.is_set():
        return

    await _fade(coordinator, players, 0.0, target_volume, fade_sec, cancel_event)


# -------------------- multi-Sonos path --------------------


async def _run_multi_player_sonos(
    coordinator: "WakeAlarmCoordinator",
    players: list[str],
    media_content_id: str,
    media_content_type: str,
    target_volume: float,
    fade_sec: int,
    cancel_event: asyncio.Event,
) -> None:
    group_coord = players[0]
    members = players[1:]

    # 1. unjoin coordinator (clears any pre-existing group state)
    await coordinator.hass.services.async_call(
        "media_player",
        "unjoin",
        {"entity_id": group_coord},
        blocking=True,
    )
    # 2. UPnP 800 mitigation
    if await _interruptible_sleep(_UNJOIN_SETTLE_SEC, cancel_event):
        return

    # 3. volume 0 on coordinator (BEFORE)
    await _volume_set(coordinator, group_coord, 0.0)

    # 4. join the rest
    if members:
        await coordinator.hass.services.async_call(
            "media_player",
            "join",
            {"entity_id": group_coord, "group_members": members},
            blocking=True,
        )
    # 5. let the group form
    if await _interruptible_sleep(_JOIN_SETTLE_SEC, cancel_event):
        return

    # 6. volume 0 on each member individually (join does not propagate volume)
    await asyncio.gather(*(_volume_set(coordinator, p, 0.0) for p in players))

    # 7. shuffle on (mirrors legacy YAML)
    await coordinator.hass.services.async_call(
        "media_player",
        "shuffle_set",
        {"entity_id": group_coord, "shuffle": True},
        blocking=True,
    )

    # 8. play_media on coordinator
    await coordinator.hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": group_coord,
            "media_content_id": media_content_id,
            "media_content_type": media_content_type,
            "enqueue": "replace",
        },
        blocking=False,
    )

    # 9. clamp volume to 0 AGAIN on all — favourites can restore their own
    await asyncio.gather(*(_volume_set(coordinator, p, 0.0) for p in players))

    # 10. let the queue actually start
    if await _interruptible_sleep(_PLAY_QUEUE_SETTLE_SEC, cancel_event):
        return

    # 11. synchronous fade across all members
    await _fade(coordinator, players, 0.0, target_volume, fade_sec, cancel_event)


# -------------------- shared helpers --------------------


async def _fade(
    coordinator: "WakeAlarmCoordinator",
    players: list[str],
    vol_start: float,
    vol_target: float,
    fade_sec: int,
    cancel_event: asyncio.Event,
) -> None:
    if fade_sec <= 0:
        await asyncio.gather(
            *(_volume_set(coordinator, p, vol_target) for p in players)
        )
        return

    step_delay = fade_sec / _FADE_STEPS
    delta = vol_target - vol_start
    for idx in range(1, _FADE_STEPS + 1):
        if cancel_event.is_set():
            return
        raw = vol_start + delta * (idx / _FADE_STEPS)
        v = round(max(0.0, min(1.0, raw)), 2)
        await asyncio.gather(*(_volume_set(coordinator, p, v) for p in players))
        if await _interruptible_sleep(step_delay, cancel_event):
            return


async def _volume_set(
    coordinator: "WakeAlarmCoordinator", entity_id: str, volume: float
) -> None:
    await coordinator.hass.services.async_call(
        "media_player",
        "volume_set",
        {"entity_id": entity_id, "volume_level": volume},
        blocking=True,
    )


async def _interruptible_sleep(
    seconds: float, cancel_event: asyncio.Event
) -> bool:
    """Sleep for ``seconds``. Returns True if cancelled before timeout."""
    if seconds <= 0:
        return cancel_event.is_set()
    try:
        await asyncio.wait_for(cancel_event.wait(), timeout=seconds)
        return True
    except asyncio.TimeoutError:
        return False


def _all_support_grouping(
    coordinator: "WakeAlarmCoordinator", entity_ids: list[str]
) -> bool:
    for ent in entity_ids:
        st = coordinator.hass.states.get(ent)
        if st is None:
            return False
        features = int(st.attributes.get("supported_features", 0) or 0)
        if not (features & MediaPlayerEntityFeature.GROUPING):
            return False
    return True
