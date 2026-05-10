"""Stepped light ramp.

Ports scripts.alarm_light_ramp from the legacy YAML:

* total_steps = length_min * steps_per_min (>=1)
* per_step seconds = ceil(60 / steps_per_min)
* Initial light.turn_on at 1% brightness, start_kelvin (turns on any
  lights that are off)
* Each step interpolates brightness 1% → max_brightness_pct and Kelvin
  start_kelvin → target_kelvin linearly across denom = total_steps - 1
* next_brightness = max(linear_target, current_brightness) — never dim
  a manually-brightened light
* Stop early if any configured light's brightness already meets/exceeds
  max_brightness_pct (full user override)
* User-override detection itself lives on the coordinator: every
  light.turn_on goes through coordinator.async_call_light_turn_on,
  which tags the call with a tracked Context. The coordinator's light
  state listener sets cancel_event when an untagged change arrives.
"""
from __future__ import annotations

import asyncio
import logging
import math
from typing import TYPE_CHECKING

from ._pure import clamp_kelvin, compute_step_target
from .const import (
    CONF_LIGHT_ENTITIES,
    DEFAULT_LENGTH_MIN,
    DEFAULT_MAX_BRIGHTNESS_PCT,
    DEFAULT_START_KELVIN,
    DEFAULT_STEPS_PER_MIN,
    DEFAULT_TARGET_KELVIN,
)

if TYPE_CHECKING:
    from .coordinator import WakeAlarmCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_run_light_ramp(
    coordinator: "WakeAlarmCoordinator",
    cancel_event: asyncio.Event,
) -> None:
    """Run the stepped sunrise ramp until done, cancelled, or user-overridden."""
    light_entities: list[str] = list(
        coordinator.entry.data.get(CONF_LIGHT_ENTITIES) or []
    )
    if not light_entities:
        _LOGGER.warning(
            "no lights configured for %s; skipping ramp", coordinator.slug
        )
        return

    length_min = int(coordinator.read_number("length_min", DEFAULT_LENGTH_MIN))
    max_pct = int(
        coordinator.read_number("max_brightness_pct", DEFAULT_MAX_BRIGHTNESS_PCT)
    )
    start_k = int(coordinator.read_number("start_kelvin", DEFAULT_START_KELVIN))
    target_k = int(coordinator.read_number("target_kelvin", DEFAULT_TARGET_KELVIN))
    steps_per_min = int(
        coordinator.read_number("steps_per_min", DEFAULT_STEPS_PER_MIN)
    )

    total_steps = max(1, length_min * steps_per_min)
    per_step_sec = max(1, math.ceil(60 / max(1, steps_per_min)))

    # Initial turn-on at 1% / start_kelvin (turns on any lights that are off)
    await coordinator.async_call_light_turn_on(
        light_entities, brightness_pct=1, kelvin=clamp_kelvin(start_k)
    )

    for idx in range(total_steps):
        if cancel_event.is_set():
            return

        linear_pct, linear_k = compute_step_target(
            idx, total_steps, max_pct, start_k, target_k
        )

        current_pct = _max_current_brightness_pct(coordinator, light_entities)

        # Manual override: user has already taken brightness to/above target
        if current_pct >= max_pct:
            _LOGGER.info(
                "ramp for %s stopped early: current %d%% >= max %d%%",
                coordinator.slug,
                current_pct,
                max_pct,
            )
            return

        next_pct = max(1, min(100, max(linear_pct, current_pct)))
        next_k = clamp_kelvin(linear_k)

        await coordinator.async_call_light_turn_on(
            light_entities, brightness_pct=next_pct, kelvin=next_k
        )

        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=per_step_sec)
            return  # cancelled mid-step
        except asyncio.TimeoutError:
            continue


def _max_current_brightness_pct(
    coordinator: "WakeAlarmCoordinator", entity_ids: list[str]
) -> int:
    pcts: list[int] = []
    for ent in entity_ids:
        st = coordinator.hass.states.get(ent)
        if st is None:
            continue
        bri = st.attributes.get("brightness")
        if bri is None:
            continue
        try:
            pcts.append(round(int(bri) / 2.55))
        except (TypeError, ValueError):
            continue
    return max(pcts) if pcts else 0
