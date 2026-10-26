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
from datetime import datetime, timedelta
from datetime import time as dt_time
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

from ._pure import ScheduleDecision, compute_next_fire, plan_schedule
from .const import (
    CATCHUP_GRACE_MIN,
    CONF_AFTER_SCRIPT,
    CONF_AT_ALARM_SCRIPT,
    CONF_BEFORE_SCRIPT,
    CONF_CONDITION_ENTITY,
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

        # Two independent timers: the light ramp is armed at ramp_start, the
        # authoritative wake-up (music) at alarm_time. Decoupling them means a
        # failure in the light path can never stop the alarm from sounding.
        self._cancel_ramp_schedule: CALLBACK_TYPE | None = None
        self._cancel_alarm_schedule: CALLBACK_TYPE | None = None
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

        # Whether an alarm occurrence is currently in progress. Delimits the
        # before-script (run once when the occurrence begins, at ramp-start or
        # alarm time) and the after-script (run once when it ends). See #24.
        self._cycle_active: bool = False

        # Fire-and-forget tasks (catch-up fire, mid-cycle dismiss, before/after
        # scripts). Tracked so async_unload can cancel anything still in flight
        # rather than leaving it to run against a torn-down entry (#35).
        self._background_tasks: set[asyncio.Task] = set()

        # A dependency change (alarm time / length / day toggles) that arrives
        # while the alarm is already PLAYING/SNOOZING is deferred to the next
        # IDLE settle, so it can never arm a second fire for the same day (#44).
        self._recompute_pending: bool = False

        # Set once async_unload starts. A cancelled ramp/music task runs its
        # finally on the way out, which can otherwise re-arm the schedule timers
        # (via the deferred recompute) and fire the after-script after teardown
        # has finished cleaning up. Guards in async_recompute_schedule and
        # _run_script make those finallys inert once unloading.
        self._unloading: bool = False

        # Whether music was actually PLAYING when the current snooze began. Only
        # then is the (Sonos) group already formed, so only then may the
        # snooze-resume skip the group-join preamble (from_snooze). Snoozing
        # during the ramp has no group yet and needs a full music start.
        self._snooze_from_playing: bool = False

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

    @callback
    def diagnostics_snapshot(self) -> dict:
        """Live state snapshot for config-entry diagnostics (no secrets).

        Surfaces the scheduler decision, state-machine flags, which timers/tasks
        are armed, and a read-back of the entities the coordinator drives — the
        data needed to diagnose "did it schedule/fire correctly?" without
        reproducing under debug logging.
        """
        def _iso(value: datetime | None) -> str | None:
            return value.isoformat() if value is not None else None

        alarm_time = self._read_alarm_time()
        return {
            "state": self._state,
            "is_active": self.is_active,
            "cycle_active": self._cycle_active,
            "recompute_pending": self._recompute_pending,
            "unloading": self._unloading,
            "next_fire": _iso(self._next_fire),
            "next_ramp_start": _iso(self._next_ramp_start),
            "snooze_finishes_at": _iso(self._snooze_finishes_at),
            "auto_dismiss_deadline": _iso(self._auto_dismiss_deadline),
            "timers_armed": {
                "ramp": self._cancel_ramp_schedule is not None,
                "alarm": self._cancel_alarm_schedule is not None,
                "snooze": self._snooze_cancel is not None,
                "auto_dismiss": self._auto_dismiss_cancel is not None,
            },
            "tasks": {
                "ramp_running": (
                    self._ramp_task is not None and not self._ramp_task.done()
                ),
                "music_running": (
                    self._music_task is not None and not self._music_task.done()
                ),
                "background": len(self._background_tasks),
            },
            "config_readback": {
                "enabled": self._read_enabled(),
                "alarm_time": alarm_time.isoformat() if alarm_time else None,
                "enabled_days": sorted(self._read_enabled_days()),
                "length_min": self.read_number("length_min", DEFAULT_LENGTH_MIN),
            },
            "media_selected": self.current_media() is not None,
        }

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

    @callback
    def _track_task(self, coro) -> asyncio.Task:
        """Create a background task tracked for cancellation on unload (#35)."""
        task = self.hass.async_create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

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

        # catch_up=True: if HA was down past today's alarm but is back within
        # the grace window, fire it now rather than waiting for tomorrow.
        self.async_recompute_schedule(catch_up=True)

    async def async_unload(self) -> None:
        # Mark teardown first so any ramp/music task finally that runs while we
        # cancel below cannot re-arm timers or fire scripts (see the guards in
        # async_recompute_schedule / _run_script).
        self._unloading = True
        for cancel in self._cancel_listeners:
            cancel()
        self._cancel_listeners.clear()
        self._cancel_scheduled_timers()
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
        # Cancel any fire-and-forget tasks still in flight (#35).
        for task in list(self._background_tasks):
            task.cancel()
        self._background_tasks.clear()

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
                self._track_task(self.async_dismiss())
                return
        if self._state in (STATE_PLAYING, STATE_SNOOZING):
            # The alarm has already fired today. Re-arming the schedule now off
            # a settings change could select today's (still-future) occurrence
            # again and fire a second time the same morning (#44). Defer the
            # recompute until the occurrence settles back to IDLE, where it is
            # applied with skip_today.
            self._recompute_pending = True
            return
        self.async_recompute_schedule()

    @callback
    def _cancel_scheduled_timers(self) -> None:
        """Cancel both the ramp and alarm point-in-time timers."""
        if self._cancel_ramp_schedule is not None:
            self._cancel_ramp_schedule()
            self._cancel_ramp_schedule = None
        if self._cancel_alarm_schedule is not None:
            self._cancel_alarm_schedule()
            self._cancel_alarm_schedule = None

    @callback
    def async_recompute_schedule(
        self, *, catch_up: bool = False, skip_today: bool = False
    ) -> None:
        """(Re)compute the next fire and (re)arm both independent timers.

        catch_up   apply the restart grace window (startup only): if today's
                   alarm was missed within CATCHUP_GRACE_MIN, fire it now.
        skip_today exclude today's occurrence entirely — used by dismiss, which
                   means "not this one", even when today's alarm is still ahead.
        """
        if self._unloading:
            # Teardown in progress: never arm new timers. A cancelled ramp/music
            # task's finally can reach here via the deferred recompute in
            # _set_state; without this guard those timers would outlive unload.
            return
        # Any explicit recompute consumes a pending deferred one (#44).
        self._recompute_pending = False
        self._cancel_scheduled_timers()

        decision = self._compute_schedule(
            catch_up=catch_up, skip_today=skip_today
        )
        if decision is None:
            # No schedule (disabled / no enabled days / no alarm time) cancels
            # the armed alarm timer above, so _async_on_alarm — which would
            # otherwise close the occurrence — will never run. End any pending
            # occurrence here so _cycle_active can't get stranded True and
            # suppress the next occurrence's before-script (#34).
            _LOGGER.debug(
                "%s: no schedule (disabled / no enabled days / no alarm time)",
                self.slug,
            )
            self._abandon_cycle()
            self._next_fire = None
            self._next_ramp_start = None
            self._notify_listeners()
            return

        self._next_fire = decision.next_fire
        self._next_ramp_start = decision.ramp_start

        if decision.fire_now:
            # HA was down past alarm_time but within grace: fire the alarm now.
            # Music only — a partial ramp from a cold boot adds no value. The
            # alarm callback rolls the schedule forward to the next day itself.
            _LOGGER.debug(
                "%s: restart catch-up — firing alarm now (target %s)",
                self.slug,
                decision.next_fire,
            )
            self._track_task(self._async_on_alarm(dt_util.now()))
        else:
            now = dt_util.now()
            _LOGGER.debug(
                "%s: scheduled next_fire=%s ramp_start=%s",
                self.slug,
                decision.next_fire,
                decision.ramp_start,
            )
            if (
                decision.ramp_start is not None
                and decision.ramp_start > now
            ):
                self._cancel_ramp_schedule = async_track_point_in_time(
                    self.hass, self._async_on_ramp_start, decision.ramp_start
                )
            if decision.next_fire is not None and decision.next_fire > now:
                self._cancel_alarm_schedule = async_track_point_in_time(
                    self.hass, self._async_on_alarm, decision.next_fire
                )

        self._notify_listeners()

    def _compute_schedule(
        self, *, catch_up: bool = False, skip_today: bool = False
    ) -> ScheduleDecision | None:
        if not self._read_enabled():
            return None
        alarm_time = self._read_alarm_time()
        if alarm_time is None:
            return None
        enabled_days = self._read_enabled_days()
        if not enabled_days:
            return None
        length_min = int(self.read_number("length_min", DEFAULT_LENGTH_MIN))
        now = dt_util.now()

        if catch_up and not skip_today:
            return plan_schedule(
                now, alarm_time, enabled_days, length_min, CATCHUP_GRACE_MIN
            )

        # Normal arm / post-fire roll-forward / dismiss: the next strictly
        # future occurrence, never catching up a missed alarm (catch-up only
        # makes sense at startup). For skip_today we advance the anchor to
        # today's alarm_time so compute_next_fire rolls past today even when
        # called before it (dismiss during the ramp).
        anchor = now
        if skip_today:
            today_at = now.replace(
                hour=alarm_time.hour,
                minute=alarm_time.minute,
                second=alarm_time.second,
                microsecond=0,
            )
            anchor = max(now, today_at)
        future = compute_next_fire(anchor, alarm_time, enabled_days)
        if future is None:
            return None
        ramp_start = future - timedelta(minutes=length_min)
        return ScheduleDecision(
            next_fire=future,
            ramp_start=ramp_start,
            fire_now=False,
            inside_ramp_window=ramp_start <= now < future,
        )

    def _presence_ok(self) -> bool:
        """True when no person is configured, or the configured person is home."""
        person = self.entry.data.get(CONF_PERSON_ENTITY)
        if not person:
            return True
        st = self.hass.states.get(person)
        return st is not None and st.state == "home"

    def _condition_ok(self) -> bool:
        """True when no condition entity is configured, or it is currently on.

        The optional binary_sensor gate (#23): works exactly like presence but
        accepts any on/off sensor (bed sensor, workday sensor, etc.). ANDed
        with presence — both must pass for the alarm to run.
        """
        entity = self.entry.data.get(CONF_CONDITION_ENTITY)
        if not entity:
            return True
        st = self.hass.states.get(entity)
        return st is not None and st.state == "on"

    def _gate_ok(self, *, what: str) -> bool:
        """Combined presence + condition gate, with a logged reason on skip."""
        if not self._presence_ok():
            _LOGGER.info(
                "%s for %s skipped: %s not home",
                what,
                self.slug,
                self.entry.data.get(CONF_PERSON_ENTITY),
            )
            return False
        if not self._condition_ok():
            _LOGGER.info(
                "%s for %s skipped: condition %s not on",
                what,
                self.slug,
                self.entry.data.get(CONF_CONDITION_ENTITY),
            )
            return False
        return True

    # -------------------- fire callbacks --------------------

    async def _async_on_ramp_start(self, _now: datetime) -> None:
        """Light-ramp timer (lights only).

        Never schedules music. An exception here is contained to the light
        path; the independently armed alarm timer (_async_on_alarm) is
        untouched and still fires. Presence is checked here for the lights;
        the alarm re-checks it separately at alarm_time.
        """
        self._cancel_ramp_schedule = None
        if not self._read_enabled():
            return
        if not self._gate_ok(what="light ramp"):
            return
        _LOGGER.debug("%s: ramp-start firing", self.slug)
        self._start_cycle()
        await self._async_start_ramp(end_state=STATE_IDLE)

    async def _async_on_alarm(self, _now: datetime) -> None:
        """Authoritative wake-up timer, fired at alarm_time.

        Independent of the light ramp: runs even if the ramp callback never
        fired or raised. Presence is re-checked here (fresh, at alarm time) so
        leaving/arriving between ramp_start and alarm_time is honoured for the
        alarm itself. The schedule is always rolled forward in the finally —
        at this point now >= alarm_time, so compute_next_fire picks the next
        enabled day and the old mid-cycle re-selection loop cannot occur.
        """
        self._cancel_alarm_schedule = None
        try:
            if not self._read_enabled():
                self._abandon_cycle()
                return
            if not self._gate_ok(what="alarm"):
                self._abandon_cycle()
                return
            _LOGGER.debug("%s: alarm firing (music phase)", self.slug)
            self._start_cycle()
            # The at-alarm hook fires exactly at alarm_time — the moment the
            # alarm sounds — for every non-gated outcome (music, lights-only,
            # players unavailable, no media). Non-blocking, so it never delays
            # the wake-up. Only reached once the gate has passed, so it does not
            # fire when presence/condition skip the alarm.
            self._run_script(CONF_AT_ALARM_SCRIPT, "at-alarm")
            await self._fire_music()
        finally:
            self.async_recompute_schedule()

    async def _fire_music(self) -> None:
        """Decide between music, urgent (players down), or no-media notice.

        Self-contained so a failure in the light path can never reach it. On
        any no-music outcome, settle to IDLE if nothing else is running.
        """
        players = list(
            self.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []
        )
        if not players:
            # Lights-only alarm (#22): no media player configured. Still send
            # the friendly standard notification so the user gets a morning
            # ping and a Dismiss handle, but skip the urgent "players
            # unavailable" / "no media" notices — those only make sense once
            # the user has opted into music. Snooze/auto-dismiss are music
            # concepts and are not armed here; the ramp settles to idle.
            await async_send_standard(self)
            self._settle_idle_if_not_active()
            self._finish_cycle()
            return

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
            self._settle_idle_if_not_active()
            self._finish_cycle()
            return

        if self.current_media() is None:
            _LOGGER.warning(
                "alarm at %s: no media set; skipping music",
                self.slug,
            )
            await async_send_no_media(self)
            self._settle_idle_if_not_active()
            self._finish_cycle()
            return

        await self._async_start_music(end_state=STATE_IDLE, is_alarm=True)
        await async_send_standard(self)

    @callback
    def _settle_idle_if_not_active(self) -> None:
        """Drop to IDLE when no music will play and nothing is still running.

        A ramp that finished early leaves us in RAMPING; when music is then
        skipped (players unavailable / no media) nothing else rolls us back, so
        do it here. If a ramp or music task is still running, its own
        completion handles the transition.
        """
        if (
            self._state in (STATE_RAMPING, STATE_PLAYING)
            and (self._ramp_task is None or self._ramp_task.done())
            and (self._music_task is None or self._music_task.done())
        ):
            self._set_state(STATE_IDLE)

    # -------------------- light ramp --------------------

    async def async_test_light_ramp(self) -> None:
        """User-pressed test-ramp button: run the ramp standalone."""
        if self._state != STATE_IDLE or self._cycle_active:
            # _cycle_active guards the ramp→alarm IDLE gap: the state reads IDLE
            # but a real occurrence is in flight, so a test press here would
            # collide with the imminent alarm (#43).
            _LOGGER.warning(
                "test_light_ramp ignored for %s: state=%s cycle_active=%s",
                self.slug,
                self._state,
                self._cycle_active,
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
            # Revert to IDLE if the ramp ended while still RAMPING. This is
            # harmless now: IDLE no longer recomputes the schedule, and the
            # music timer is armed independently, so a ramp finishing a few
            # seconds before alarm_time can't re-fire the alarm.
            if self._state == STATE_RAMPING:
                self._set_state(end_state)

    # -------------------- music sequence --------------------

    async def async_test_music(self) -> None:
        """User-pressed test-music button: run the sequence standalone."""
        if self._state != STATE_IDLE or self._cycle_active:
            # _cycle_active guards the ramp→alarm IDLE gap: starting test music
            # there would occupy the music task and the real alarm's music
            # start would then be skipped, silencing the wake-up (#43).
            _LOGGER.warning(
                "test_music ignored for %s: state=%s cycle_active=%s",
                self.slug,
                self._state,
                self._cycle_active,
            )
            return
        await self._async_start_music(end_state=STATE_IDLE)

    async def _async_start_music(
        self,
        *,
        end_state: str,
        from_snooze: bool = False,
        is_alarm: bool = False,
    ) -> None:
        if self._music_task is not None and not self._music_task.done():
            _LOGGER.debug(
                "music already running for %s; skipping start", self.slug
            )
            return
        # Precondition: no media player configured (lights-only alarm, #22) →
        # there is nothing to play on, so skip music entirely.
        if not (self.entry.data.get(CONF_MEDIA_PLAYER_ENTITIES) or []):
            _LOGGER.debug(
                "music skipped for %s: no media players configured", self.slug
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
            self._music_runner(
                end_state, from_snooze=from_snooze, is_alarm=is_alarm
            )
        )
        self._start_auto_dismiss_if_configured()

    async def _music_runner(
        self,
        end_state: str,
        *,
        from_snooze: bool = False,
        is_alarm: bool = False,
    ) -> None:
        try:
            await async_run_music_sequence(
                self, self._music_cancel_event, from_snooze=from_snooze
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            _LOGGER.exception("music for %s failed", self.slug)
            # Hard failure mid-sequence: settle so we don't strand PLAYING in
            # silence. The common unavailable-players / no-media cases are
            # caught pre-flight in _fire_music before music ever starts, so
            # this only covers an unexpected mid-sequence error. For a real
            # alarm that's the end of the occurrence → run the after-script.
            if self._state == STATE_PLAYING:
                self._set_state(end_state)
                if is_alarm:
                    self._finish_cycle()
        finally:
            self._music_task = None
            self._music_cancel_event = None
            # NB: completing the fade does NOT end the occurrence. The media
            # player keeps playing on its own, so the coordinator stays in
            # PLAYING (keeping the card's snooze/dismiss buttons visible and
            # auto-dismiss armed) until the user snoozes/dismisses or the
            # auto-dismiss timer fires. A snooze/dismiss moves the state out of
            # PLAYING and cancels the music task before reaching here, so the
            # leftover `end_state` from a natural fade is intentionally unused.

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

        # Capture whether music is already playing (group formed) before we
        # transition out of PLAYING below. Drives whether the resume may skip
        # the Sonos group-join preamble; snoozing mid-ramp must not, since the
        # group isn't formed yet.
        self._snooze_from_playing = self._state == STATE_PLAYING

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

        # Leave the auto-dismiss timer armed across the snooze so "stop after N
        # minutes" is honoured even mid-snooze (#38). The deadline is fixed at
        # the first fire and never extended, so a long snooze can't push the
        # stop past it.
        self._set_state(STATE_SNOOZING)

        snooze_min = int(self.read_number("snooze_min", DEFAULT_SNOOZE_MIN))
        self._snooze_finishes_at = dt_util.now() + timedelta(minutes=snooze_min)
        _LOGGER.debug(
            "%s: snoozing for %d min (resume at %s)",
            self.slug,
            snooze_min,
            self._snooze_finishes_at,
        )
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
        _LOGGER.debug(
            "%s: snooze finished — resuming music (from_playing=%s)",
            self.slug,
            self._snooze_from_playing,
        )
        # Re-run music. Skip the Sonos group-join preamble only if the group
        # was already formed during a prior PLAYING phase; snoozing mid-ramp
        # has no group yet, so it needs the full start.
        await self._async_start_music(
            end_state=STATE_IDLE,
            from_snooze=self._snooze_from_playing,
            is_alarm=True,
        )
        if self._state == STATE_SNOOZING:
            # Nothing resumed — lights-only alarm (#22) or the media selection
            # was cleared during the snooze. Don't hang in SNOOZING; settle,
            # and close out the occurrence (run the after-script).
            self._set_state(STATE_IDLE)
            self._finish_cycle()

    async def async_dismiss(self) -> None:
        """Full dismiss per the brief.

        Stops music on all configured players, unjoins any formed group,
        cancels every pending task/timer, leaves lights as the user has
        them, returns to IDLE, and rolls the schedule forward past today's
        occurrence (dismiss means "skip this one").
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
        self._cancel_scheduled_timers()
        self._cancel_snooze()
        self._cancel_auto_dismiss()

        self._set_state(STATE_IDLE)
        # Dismiss ends the occurrence (manual or via auto-dismiss, which calls
        # here) → run the after-script. Snooze does not reach this path.
        self._finish_cycle()
        # IDLE no longer recomputes, so roll forward explicitly. skip_today
        # excludes today's occurrence even if dismiss happened during the ramp
        # (before alarm_time) — otherwise we'd re-select and re-fire today.
        self.async_recompute_schedule(skip_today=True)

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
            # Already past the deadline — fire immediately.
            self._track_task(self.async_dismiss())
            return
        self._auto_dismiss_cancel = async_call_later(
            self.hass,
            remaining,
            self._async_auto_dismiss_fire,
        )

    async def _async_auto_dismiss_fire(self, _now: datetime) -> None:
        self._auto_dismiss_cancel = None
        # Fire while PLAYING or SNOOZING — a snooze in progress must not let the
        # alarm outlive the configured auto-dismiss window (#38).
        if self._state not in (STATE_PLAYING, STATE_SNOOZING):
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

    # -------------------- before/after script hooks (#24) --------------------

    @callback
    def _start_cycle(self) -> None:
        """Begin an alarm occurrence and fire the before-script once.

        Idempotent within an occurrence: the cycle may begin at ramp-start
        (the usual case) or at alarm time when the ramp was skipped (length 0,
        a restart inside the ramp window, or catch-up), and only the first
        call fires the before-script.
        """
        if self._cycle_active:
            return
        self._cycle_active = True
        self._run_script(CONF_BEFORE_SCRIPT, "before")

    @callback
    def _finish_cycle(self) -> None:
        """End an alarm occurrence and fire the after-script once.

        Fired on every terminal outcome — a dismiss, an auto-dismiss, or a
        no-music settle (lights-only / players unavailable / no media). Music
        playing does not end the cycle on its own (the player keeps playing
        until dismissed), so the after-script waits for the dismiss. Snooze
        keeps the cycle active, so it never fires here.
        """
        if not self._cycle_active:
            return
        self._cycle_active = False
        self._run_script(CONF_AFTER_SCRIPT, "after")

    @callback
    def _abandon_cycle(self) -> None:
        """End the occurrence without firing the after-script.

        Used when the alarm is gated off (master switch / presence /
        condition) at alarm time after the ramp already started a cycle: the
        before may have run, but the alarm itself did not fire, so the
        after-script is not appropriate. Resetting the flag keeps the next
        occurrence's before-script working.
        """
        self._cycle_active = False

    @callback
    def _run_script(self, conf_key: str, label: str) -> None:
        """Fire-and-forget the configured before/after script, if any.

        Runs in a tracked background task, never awaited from the alarm path,
        so a slow or failing script can never delay the wake-up (and is
        cancelled on unload). The instance slug + name are passed as script
        variables for context.
        """
        if self._unloading:
            # A cancelled music task's finally can reach _finish_cycle during
            # teardown; the after-script must not fire on unload/reload.
            return
        target = self.entry.data.get(conf_key)
        if not target:
            return
        _LOGGER.debug("%s: running %s-script %s", self.slug, label, target)
        self._track_task(self._async_call_script(target, label))

    async def _async_call_script(self, target: str, label: str) -> None:
        domain, _, object_id = target.partition(".")
        if domain != "script" or not object_id:
            _LOGGER.warning(
                "%s-script target %r for %s is not a script entity; skipping",
                label,
                target,
                self.slug,
            )
            return
        try:
            # blocking=True so this tracked task actually represents the
            # script's run and the except below catches real execution errors;
            # the wake-up is never delayed because this runs off the alarm path
            # in its own background task (#35).
            await self.hass.services.async_call(
                "script",
                object_id,
                {"slug": self.slug, "name": self.name},
                blocking=True,
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "%s-script %s for %s failed", label, target, self.slug
            )

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
        _LOGGER.debug("%s: state %s -> %s", self.slug, self._state, new_state)
        self._state = new_state
        if new_state == STATE_IDLE:
            # Clear the auto-dismiss deadline so the next fire starts fresh.
            # We intentionally do NOT recompute the schedule here: rolling the
            # next-fire forward happens at well-defined moments (the alarm
            # firing, dependency changes, dismiss, startup), never on the
            # IDLE transition. Recomputing here is what caused the ramp to
            # re-fire when it finished a few seconds before alarm_time.
            self._clear_auto_dismiss_deadline()
        self._notify_listeners()
        if new_state == STATE_IDLE and self._recompute_pending:
            # A settings change arrived while the alarm was firing (#44). Apply
            # it now that the occurrence is over, skipping today — the
            # occurrence that just ended already fired today.
            self._recompute_pending = False
            self.async_recompute_schedule(skip_today=True)

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
