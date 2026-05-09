"""Wake Alarm coordinator: state machine + scheduling.

Owns the next-fire computation and the async_track_point_in_time callback.
Recomputes whenever any dependency entity (master enable, time, day toggles,
length) changes state. No minute-pattern polling.
"""
from __future__ import annotations

import logging
from datetime import datetime, time as dt_time, timedelta
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_SLUG,
    DAYS,
    DEFAULT_LENGTH_MIN,
    STATE_IDLE,
    STATE_PLAYING,
    STATE_RAMPING,
    STATE_SNOOZING,
)

_LOGGER = logging.getLogger(__name__)


class WakeAlarmCoordinator:
    """Per-config-entry state machine and scheduler."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.slug: str = entry.data[CONF_SLUG]

        self._state: str = STATE_IDLE
        self._next_fire: datetime | None = None
        self._next_ramp_start: datetime | None = None

        self._cancel_schedule: CALLBACK_TYPE | None = None
        self._cancel_listeners: list[CALLBACK_TYPE] = []
        self._update_callbacks: list[Callable[[], None]] = []

    # -------------------- public state --------------------

    @property
    def state(self) -> str:
        return self._state

    @property
    def next_fire(self) -> datetime | None:
        return self._next_fire

    @property
    def is_active(self) -> bool:
        return self._state != STATE_IDLE

    def async_add_listener(
        self, update_callback: Callable[[], None]
    ) -> Callable[[], None]:
        """Register a no-arg listener notified on state/schedule changes."""
        self._update_callbacks.append(update_callback)

        def _remove() -> None:
            if update_callback in self._update_callbacks:
                self._update_callbacks.remove(update_callback)

        return _remove

    @callback
    def _notify_listeners(self) -> None:
        for cb in list(self._update_callbacks):
            try:
                cb()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("listener for %s raised", self.slug)

    # -------------------- lifecycle --------------------

    async def async_setup(self) -> None:
        """Subscribe to dependency state changes and compute the initial schedule."""
        watched: list[str] = [
            f"switch.{self.slug}_enabled",
            f"time.{self.slug}_alarm_time",
            f"number.{self.slug}_length_min",
            *(f"switch.{self.slug}_{day}" for day in DAYS),
        ]
        self._cancel_listeners.append(
            async_track_state_change_event(
                self.hass, watched, self._async_on_dependency_change
            )
        )
        self.async_recompute_schedule()

    async def async_unload(self) -> None:
        for cancel in self._cancel_listeners:
            cancel()
        self._cancel_listeners.clear()
        if self._cancel_schedule is not None:
            self._cancel_schedule()
            self._cancel_schedule = None

    # -------------------- scheduling --------------------

    @callback
    def _async_on_dependency_change(self, event: Event) -> None:
        self.async_recompute_schedule()

    @callback
    def async_recompute_schedule(self) -> None:
        """(Re)compute next fire time and (re)arm the timer."""
        if self._cancel_schedule is not None:
            self._cancel_schedule()
            self._cancel_schedule = None

        next_fire = self._compute_next_fire()
        self._next_fire = next_fire
        self._next_ramp_start = None

        if next_fire is not None:
            length_min = int(self._read_number("length_min", DEFAULT_LENGTH_MIN))
            ramp_start = next_fire - timedelta(minutes=length_min)
            self._next_ramp_start = ramp_start
            # Aim at ramp_start; async_track_point_in_time fires immediately
            # if it has passed (e.g. mid-cycle restart), which is acceptable
            # given the brief's clean-slate restart policy.
            self._cancel_schedule = async_track_point_in_time(
                self.hass, self._async_on_fire, ramp_start
            )

        self._notify_listeners()

    def _compute_next_fire(self) -> datetime | None:
        if not self._read_enabled():
            return None
        alarm_time = self._read_alarm_time()
        if alarm_time is None:
            return None
        enabled_days = self._read_enabled_days()
        if not enabled_days:
            return None

        now = dt_util.now()
        today_at = now.replace(
            hour=alarm_time.hour,
            minute=alarm_time.minute,
            second=alarm_time.second,
            microsecond=0,
        )
        for offset in range(0, 8):
            candidate = today_at + timedelta(days=offset)
            if candidate.weekday() in enabled_days and candidate > now:
                return candidate
        return None

    # -------------------- fire callback (stub for now) --------------------

    async def _async_on_fire(self, _now: datetime) -> None:
        """Fire callback. Real ramp/music wiring lands in steps 4 and 5."""
        self._cancel_schedule = None
        if not self._read_enabled():
            self.async_recompute_schedule()
            return
        # TODO step 4-5: presence check, light ramp, music sequence, etc.
        # For step 3 we just bounce through ramping → idle and reschedule
        # so sensor.next_alarm rolls over to the following day.
        self._set_state(STATE_RAMPING)
        self._set_state(STATE_IDLE)
        self.async_recompute_schedule()

    # -------------------- state machine --------------------

    @callback
    def _set_state(self, new_state: str) -> None:
        if new_state not in (
            STATE_IDLE,
            STATE_RAMPING,
            STATE_PLAYING,
            STATE_SNOOZING,
        ):
            raise ValueError(f"unknown coordinator state: {new_state}")
        if self._state == new_state:
            return
        self._state = new_state
        self._notify_listeners()

    # -------------------- state readers --------------------

    def _read_enabled(self) -> bool:
        st = self.hass.states.get(f"switch.{self.slug}_enabled")
        return st is not None and st.state == "on"

    def _read_alarm_time(self) -> dt_time | None:
        st = self.hass.states.get(f"time.{self.slug}_alarm_time")
        if st is None or st.state in (None, "unknown", "unavailable", ""):
            return None
        try:
            return dt_time.fromisoformat(st.state)
        except ValueError:
            return None

    def _read_enabled_days(self) -> set[int]:
        result: set[int] = set()
        for idx, day in enumerate(DAYS):
            st = self.hass.states.get(f"switch.{self.slug}_{day}")
            if st is not None and st.state == "on":
                result.add(idx)
        return result

    def _read_number(self, key: str, default: float) -> float:
        st = self.hass.states.get(f"number.{self.slug}_{key}")
        if st is None or st.state in (None, "unknown", "unavailable", ""):
            return default
        try:
            return float(st.state)
        except ValueError:
            return default
