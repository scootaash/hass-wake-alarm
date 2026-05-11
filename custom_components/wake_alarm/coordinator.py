"""Wake Alarm coordinator: state machine + scheduling + light ramp.

Owns the next-fire computation and the async_track_point_in_time callback.
Recomputes whenever any dependency entity (master enable, time, day toggles,
length) changes state. No minute-pattern polling.

Also owns context tracking for user-override detection: every light service
call this coordinator emits goes through async_call_light_turn_on, which tags
the call with a tracked Context. State changes for configured lights that
arrive with an unknown context.id while ramping are treated as user overrides
and end the ramp.
"""
from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime, time as dt_time, timedelta
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import (
    CALLBACK_TYPE,
    Context,
    Event,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LIGHT_ENTITIES,
    CONF_MEDIA_PLAYER_ENTITIES,
    CONF_PERSON_ENTITY,
    CONF_SLUG,
    DAYS,
    DEFAULT_AUTO_DISMISS_MIN,
    DEFAULT_LENGTH_MIN,
    DEFAULT_SNOOZE_MIN,
    STATE_IDLE,
    STATE_PLAYING,
    STATE_RAMPING,
    STATE_SNOOZING,
)
from ._pure import compute_next_fire
from .light_ramp import async_run_light_ramp
from .music_sequence import async_run_music_sequence
from .notifications import (
    async_send_no_media,
    async_send_player_unavailable,
    async_send_standard,
)

_LOGGER = logging.getLogger(__name__)

# Context tracking window for user-override detection
_CTX_MAX_AGE_SEC = 60
_CTX_MAX_ENTRIES = 50


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

        # User-override detection
        self._issued_contexts: OrderedDict[str, datetime] = OrderedDict()

        # Ramp task and cancel signal
        self._ramp_task: asyncio.Task | None = None
        self._ramp_cancel_event: asyncio.Event | None = None

        # Music task and cancel signal
        self._music_task: asyncio.Task | None = None
        self._music_cancel_event: asyncio.Event | None = None

        # Media selection sensor (registered when sensor entity adds itself)
        self._media_sensor = None  # type: ignore[var-annotated]

        # Snooze + auto-dismiss timers
        self._snooze_cancel: CALLBACK_TYPE | None = None
        self._auto_dismiss_cancel: CALLBACK_TYPE | None = None
        # Wall-clock target for the snooze finish; surfaced as a sensor
        # attribute so the card can show a countdown.
        self._snooze_finishes_at: datetime | None = None
        # Wall-clock target for auto-dismiss. Captured at first PLAYING
        # transition and preserved across snooze cycles, so the timer
        # always elapses N minutes after the alarm originally fired —
        # never extended by repeat snoozes.
        self._auto_dismiss_deadline: datetime | None = None

        # Music-start callback scheduled from _async_on_fire
        self._cancel_music_start: CALLBACK_TYPE | None = None

    # -------------------- public state --------------------

    @property
    def name(self) -> str:
        """User-friendly name for this alarm instance."""
        return self.entry.data.get(CONF_NAME, self.slug)

    @property
    def state(self) -> str:
        return self._state

    @property
    def next_fire(self) -> datetime | None:
        return self._next_fire

    @property
    def is_active(self) -> bool:
        return self._state != STATE_IDLE

    @property
    def snooze_finishes_at(self) -> datetime | None:
        """Wall-clock time the snooze timer will fire (None unless snoozing)."""
        return self._snooze_finishes_at

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

        light_entities = list(self.entry.data.get(CONF_LIGHT_ENTITIES) or [])
        if light_entities:
            self._cancel_listeners.append(
                async_track_state_change_event(
                    self.hass,
                    light_entities,
                    self._async_on_light_state_change,
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
        # Cancel any in-flight ramp / music / snooze / auto-dismiss
        if self._ramp_cancel_event is not None:
            self._ramp_cancel_event.set()
        if self._ramp_task is not None and not self._ramp_task.done():
            self._ramp_task.cancel()
        if self._music_cancel_event is not None:
            self._music_cancel_event.set()
        if self._music_task is not None and not self._music_task.done():
            self._music_task.cancel()
        self._cancel_snooze()
        self._cancel_auto_dismiss()
        self._cancel_pending_music_start()

    # -------------------- scheduling --------------------

    @callback
    def _async_on_dependency_change(self, event: Event) -> None:
        # Mid-cycle disable: master enable flips off while a sequence is
        # running → trigger a full dismiss (which itself reschedules).
        if event.data.get("entity_id") == f"switch.{self.slug}_enabled":
            new_state = event.data.get("new_state")
            if (
                new_state is not None
                and new_state.state == "off"
                and self.is_active
            ):
                self.hass.async_create_task(self.async_dismiss())
                return
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
            length_min = int(self.read_number("length_min", DEFAULT_LENGTH_MIN))
            ramp_start = next_fire - timedelta(minutes=length_min)
            self._next_ramp_start = ramp_start
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
        return compute_next_fire(dt_util.now(), alarm_time, enabled_days)

    # -------------------- fire callback --------------------

    async def _async_on_fire(self, _now: datetime) -> None:
        """Fire at ramp_start. Per BRIEF.md "On fire":

        1. Master enable check
        2. Person presence check (if configured)
        3. Start the light ramp
        4. Schedule music start at alarm_time
        """
        self._cancel_schedule = None
        if not self._read_enabled():
            self.async_recompute_schedule()
            return

        # Person presence check applies to the whole sequence (not just the
        # pre-phase, unlike the legacy YAML).
        person = self.entry.data.get(CONF_PERSON_ENTITY)
        if person:
            person_state = self.hass.states.get(person)
            if person_state is None or person_state.state != "home":
                _LOGGER.info(
                    "alarm for %s skipped: %s not home",
                    self.slug,
                    person,
                )
                self.async_recompute_schedule()
                return

        # Capture alarm_time (== self._next_fire). The schedule won't be
        # recomputed mid-cycle; it only recomputes after dismiss / completion.
        alarm_time = self._next_fire
        await self._async_start_ramp(end_state=STATE_IDLE)

        if alarm_time is None:
            return
        if alarm_time > dt_util.now():
            self._cancel_music_start = async_track_point_in_time(
                self.hass, self._async_on_music_start, alarm_time
            )
        else:
            # ramp_start was already in the past at fire time (mid-cycle
            # restart) → fire music immediately.
            self.hass.async_create_task(
                self._async_on_music_start(dt_util.now())
            )

    async def _async_on_music_start(self, _now: datetime) -> None:
        """Fired at alarm_time. Decide between music, urgent, or no-media."""
        self._cancel_music_start = None

        players = list(
            self.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []
        )
        unavailable = [
            ent_id
            for ent_id in players
            if (st := self.hass.states.get(ent_id)) is None
            or st.state in ("unavailable", "unknown")
        ]
        if unavailable:
            _LOGGER.warning(
                "alarm at %s: players unavailable %s; skipping music",
                self.slug,
                unavailable,
            )
            await async_send_player_unavailable(self, unavailable)
            # Lights continue ramping; ramp_runner finally returns to IDLE.
            return

        if self.current_media() is None:
            _LOGGER.warning(
                "alarm at %s: no media set; skipping music",
                self.slug,
            )
            await async_send_no_media(self)
            return

        await self._async_start_music(end_state=STATE_IDLE)
        await async_send_standard(self)

    # -------------------- light ramp --------------------

    async def async_test_light_ramp(self) -> None:
        """User-pressed test-ramp button: run the ramp standalone."""
        if self._state != STATE_IDLE:
            _LOGGER.warning(
                "test_light_ramp ignored for %s: state=%s",
                self.slug,
                self._state,
            )
            return
        await self._async_start_ramp(end_state=STATE_IDLE)

    async def async_cancel_ramp(self) -> None:
        """Stop the ramp without touching music."""
        if self._ramp_cancel_event is not None:
            self._ramp_cancel_event.set()

    async def _async_start_ramp(self, *, end_state: str) -> None:
        """Kick off the ramp loop as a background task."""
        if self._ramp_task is not None and not self._ramp_task.done():
            _LOGGER.debug(
                "ramp already running for %s; skipping start", self.slug
            )
            return
        self._set_state(STATE_RAMPING)
        self._ramp_cancel_event = asyncio.Event()
        self._ramp_task = self.hass.async_create_task(
            self._ramp_runner(end_state)
        )

    async def _ramp_runner(self, end_state: str) -> None:
        try:
            await async_run_light_ramp(self, self._ramp_cancel_event)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            _LOGGER.exception("ramp for %s failed", self.slug)
        finally:
            self._ramp_task = None
            self._ramp_cancel_event = None
            # Only revert to IDLE here; later steps will decide whether to
            # transition to PLAYING based on whether music is starting.
            if self._state == STATE_RAMPING:
                self._set_state(end_state)

    # -------------------- music sequence --------------------

    async def async_test_music(self) -> None:
        """User-pressed test-music button: run the sequence standalone."""
        if self._state != STATE_IDLE:
            _LOGGER.warning(
                "test_music ignored for %s: state=%s",
                self.slug,
                self._state,
            )
            return
        await self._async_start_music(end_state=STATE_IDLE)

    async def _async_start_music(
        self, *, end_state: str, from_snooze: bool = False
    ) -> None:
        if self._music_task is not None and not self._music_task.done():
            _LOGGER.debug(
                "music already running for %s; skipping start", self.slug
            )
            return
        # Precondition: no media picked → skip music entirely. The on-fire
        # path handles the urgent notification on its own; here (test button
        # or snooze-resume) we just log and bail.
        if self.current_media() is None:
            _LOGGER.warning(
                "music skipped for %s: no media selected (use the card to pick)",
                self.slug,
            )
            return
        self._set_state(STATE_PLAYING)
        self._music_cancel_event = asyncio.Event()
        self._music_task = self.hass.async_create_task(
            self._music_runner(end_state, from_snooze=from_snooze)
        )
        self._start_auto_dismiss_if_configured()

    async def _music_runner(
        self, end_state: str, *, from_snooze: bool = False
    ) -> None:
        try:
            await async_run_music_sequence(
                self, self._music_cancel_event, from_snooze=from_snooze
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            _LOGGER.exception("music for %s failed", self.slug)
        finally:
            self._music_task = None
            self._music_cancel_event = None
            if self._state == STATE_PLAYING:
                self._set_state(end_state)

    # -------------------- snooze + dismiss --------------------

    async def async_snooze(self) -> None:
        """Snooze flow per the brief.

        Pauses music (if any), cancels ramp/music tasks, transitions to
        SNOOZING, starts a timer for snooze_min minutes. On fire, the music
        sequence re-runs with from_snooze=True (skipping group join setup).
        Lights are intentionally left untouched.
        """
        if self._state not in (STATE_RAMPING, STATE_PLAYING):
            _LOGGER.info(
                "snooze ignored for %s: state=%s",
                self.slug,
                self._state,
            )
            return

        # End ramp if it's running (ramp_runner finally will not flip state
        # back to IDLE because we set SNOOZING below before it runs).
        if self._ramp_cancel_event is not None:
            self._ramp_cancel_event.set()

        # Pause music if it's running and stop the loop
        if self._state == STATE_PLAYING:
            players = list(
                self.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []
            )
            if players:
                await self.hass.services.async_call(
                    "media_player",
                    "media_pause",
                    {"entity_id": players[0]},
                    blocking=False,
                )
            if self._music_cancel_event is not None:
                self._music_cancel_event.set()

        self._cancel_auto_dismiss()
        self._cancel_pending_music_start()
        self._set_state(STATE_SNOOZING)

        snooze_min = int(self.read_number("snooze_min", DEFAULT_SNOOZE_MIN))
        self._snooze_finishes_at = dt_util.now() + timedelta(minutes=snooze_min)
        self._snooze_cancel = async_call_later(
            self.hass,
            snooze_min * 60,
            self._async_snooze_finished,
        )
        # Re-notify so listeners pick up the new snooze_finishes_at.
        self._notify_listeners()

    async def _async_snooze_finished(self, _now: datetime) -> None:
        self._snooze_cancel = None
        self._snooze_finishes_at = None
        if self._state != STATE_SNOOZING:
            return
        # Re-run music skipping the group join (group is already formed).
        await self._async_start_music(end_state=STATE_IDLE, from_snooze=True)

    async def async_dismiss(self) -> None:
        """Full dismiss per the brief.

        Stops music on all configured players, unjoins any formed group,
        cancels every pending task/timer, leaves lights as the user has
        them, returns to IDLE, and recomputes the next fire time.
        """
        if self._state == STATE_IDLE:
            _LOGGER.debug("dismiss for %s: already idle", self.slug)
            return

        players = list(
            self.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []
        )
        if players:
            await self.hass.services.async_call(
                "media_player",
                "media_stop",
                {"entity_id": players},
                blocking=False,
            )
            if len(players) > 1:
                await self.hass.services.async_call(
                    "media_player",
                    "unjoin",
                    {"entity_id": players[0]},
                    blocking=False,
                )

        if self._ramp_cancel_event is not None:
            self._ramp_cancel_event.set()
        if self._music_cancel_event is not None:
            self._music_cancel_event.set()
        self._cancel_snooze()
        self._cancel_auto_dismiss()
        self._cancel_pending_music_start()

        # _set_state(STATE_IDLE) now handles the schedule recompute and
        # auto-dismiss deadline clear, so we don't need explicit calls.
        self._set_state(STATE_IDLE)

    @callback
    def _cancel_pending_music_start(self) -> None:
        if self._cancel_music_start is not None:
            self._cancel_music_start()
            self._cancel_music_start = None

    @callback
    def _cancel_snooze(self) -> None:
        if self._snooze_cancel is not None:
            self._snooze_cancel()
            self._snooze_cancel = None
        self._snooze_finishes_at = None

    @callback
    def _cancel_auto_dismiss(self) -> None:
        if self._auto_dismiss_cancel is not None:
            self._auto_dismiss_cancel()
            self._auto_dismiss_cancel = None

    @callback
    def _clear_auto_dismiss_deadline(self) -> None:
        """Drop the captured deadline so the next alarm fire starts fresh."""
        self._auto_dismiss_deadline = None

    @callback
    def _start_auto_dismiss_if_configured(self) -> None:
        """Arm the auto-dismiss timer if auto_dismiss_min > 0.

        Captures the deadline at the first PLAYING transition and
        preserves it across snooze cycles so the timer never gets
        extended by repeat snoozes — N minutes always means N minutes
        from when the alarm first fired.
        """
        self._cancel_auto_dismiss()
        minutes = int(
            self.read_number("auto_dismiss_min", DEFAULT_AUTO_DISMISS_MIN)
        )
        if minutes <= 0:
            return
        if self._auto_dismiss_deadline is None:
            self._auto_dismiss_deadline = dt_util.now() + timedelta(minutes=minutes)
        remaining = (self._auto_dismiss_deadline - dt_util.now()).total_seconds()
        if remaining <= 0:
            # Already past the deadline (e.g. a long snooze pushed us
            # past it) — fire immediately.
            self.hass.async_create_task(self.async_dismiss())
            return
        self._auto_dismiss_cancel = async_call_later(
            self.hass,
            remaining,
            self._async_auto_dismiss_fire,
        )

    async def _async_auto_dismiss_fire(self, _now: datetime) -> None:
        self._auto_dismiss_cancel = None
        if self._state != STATE_PLAYING:
            return
        _LOGGER.info("auto-dismiss firing for %s", self.slug)
        await self.async_dismiss()

    # -------------------- test notifications --------------------

    async def async_test_standard_notification(self) -> None:
        """Fire the standard alarm notification with current settings.

        Lets the user verify their notify target + sound + interruption
        level on the actual device without scheduling an alarm.
        """
        await async_send_standard(self)

    async def async_test_urgent_notification(self) -> None:
        """Fire the urgent (critical) notification with current settings.

        Uses the first configured media player as the unavailable target
        so the message reads realistically; falls back to a placeholder
        if no players are configured.
        """
        players = list(
            self.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []
        )
        target_ids = players[:1] if players else ["media_player.example"]
        await async_send_player_unavailable(self, target_ids)

    # -------------------- media selection --------------------

    @callback
    def register_media_sensor(self, sensor) -> None:
        """Called by the media_selection sensor on async_added_to_hass."""
        self._media_sensor = sensor

    @callback
    def current_media(self) -> dict | None:
        """Return the persisted media selection or None if nothing is picked."""
        if self._media_sensor is None:
            return None
        return self._media_sensor.selection_data()

    @callback
    def async_set_media(
        self,
        *,
        content_id: str,
        content_type: str,
        title: str,
        thumbnail: str | None,
    ) -> None:
        """Persist a new media selection. Used by wake_alarm.set_media."""
        if self._media_sensor is None:
            _LOGGER.warning(
                "set_media called for %s before media sensor was ready",
                self.slug,
            )
            return
        self._media_sensor.update_selection(
            content_id=content_id,
            content_type=content_type,
            title=title,
            thumbnail=thumbnail,
        )

    # -------------------- override detection --------------------

    async def async_call_light_turn_on(
        self,
        entity_ids: list[str],
        *,
        brightness_pct: int,
        kelvin: int,
    ) -> None:
        """Issue a tagged light.turn_on.

        The Context is tracked so the light state listener can distinguish
        our own changes from user overrides.
        """
        ctx = Context()
        self._track_context(ctx)
        await self.hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": entity_ids,
                "brightness_pct": brightness_pct,
                "color_temp_kelvin": kelvin,
            },
            blocking=False,
            context=ctx,
        )

    @callback
    def _async_on_light_state_change(self, event: Event) -> None:
        """End the ramp on the first state change we did not cause."""
        if self._state != STATE_RAMPING:
            return
        ctx = event.context
        ctx_id = getattr(ctx, "id", None)
        self._prune_issued_contexts()
        if ctx_id is not None and ctx_id in self._issued_contexts:
            return
        _LOGGER.info(
            "user override detected for %s (entity=%s ctx=%s); ending ramp",
            self.slug,
            event.data.get("entity_id"),
            ctx_id,
        )
        if self._ramp_cancel_event is not None:
            self._ramp_cancel_event.set()

    def _track_context(self, context: Context) -> None:
        self._issued_contexts[context.id] = dt_util.utcnow()
        self._issued_contexts.move_to_end(context.id)
        self._prune_issued_contexts()

    def _prune_issued_contexts(self) -> None:
        cutoff = dt_util.utcnow() - timedelta(seconds=_CTX_MAX_AGE_SEC)
        while self._issued_contexts:
            oldest_id = next(iter(self._issued_contexts))
            if self._issued_contexts[oldest_id] < cutoff:
                self._issued_contexts.popitem(last=False)
            else:
                break
        while len(self._issued_contexts) > _CTX_MAX_ENTRIES:
            self._issued_contexts.popitem(last=False)

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
        if new_state == STATE_IDLE:
            # Always roll sensor.<slug>_next_alarm forward when we go idle —
            # whether IDLE is reached via dismiss, ramp completion, music
            # completion, or an aborted on-fire path. Previously this only
            # happened on dismiss, so naturally-completed alarms left the
            # sensor pointing at the just-past fire time.
            self._clear_auto_dismiss_deadline()
            self.async_recompute_schedule()
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

    def read_number(self, key: str, default: float) -> float:
        """Public so light_ramp / music_sequence can pull config values."""
        st = self.hass.states.get(f"number.{self.slug}_{key}")
        if st is None or st.state in (None, "unknown", "unavailable", ""):
            return default
        try:
            return float(st.state)
        except ValueError:
            return default
