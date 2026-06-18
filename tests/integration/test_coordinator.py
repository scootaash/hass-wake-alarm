"""HA-backed coordinator state-machine + scheduling tests.

These drive a real ``WakeAlarmCoordinator`` (see ``conftest.py``'s ``env``
fixture) with frozen time, firing the ramp/alarm point-in-time timers via
``async_fire_time_changed`` and asserting on state transitions, the rolled
schedule, and the mocked side-effects (light/music runners, notifications,
media-player services).

Anchor date is Saturday 2026-05-09 (UTC); ``days={5}`` (Saturday only) makes the
post-fire roll-forward land deterministically +7 days.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.wake_alarm.const import (
    STATE_IDLE,
    STATE_PLAYING,
    STATE_RAMPING,
    STATE_SNOOZING,
)

SAT = {5}  # 2026-05-09 is a Saturday


def at(hour: int, minute: int, second: int = 0) -> datetime:
    """A UTC datetime on the anchor Saturday."""
    return datetime(2026, 5, 9, hour, minute, second, tzinfo=timezone.utc)


NEXT_WEEK = at(7, 0) + timedelta(days=7)


async def fire(hass, freezer, when: datetime) -> None:
    """Advance the frozen clock to ``when`` and fire due timers to completion.

    Use this when the runners run to completion (the default): it waits for the
    whole task chain to settle.
    """
    freezer.move_to(when)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def fire_until_started(hass, freezer, when: datetime, runner) -> None:
    """Fire due timers and pump the loop only until ``runner`` has started.

    Used when a runner is deliberately held (``runner.block()``) so the
    coordinator stays in RAMPING/PLAYING — ``async_block_till_done`` would hang
    on the held task, so instead we wait for the runner's ``started`` event,
    which guarantees the schedule callback chain has reached the running state.
    """
    freezer.move_to(when)
    async_fire_time_changed(hass)
    await asyncio.wait_for(runner.started.wait(), timeout=5)


# --------------------------------------------------------------------------
# normal cycle
# --------------------------------------------------------------------------


async def test_normal_cycle(env, freezer) -> None:
    """arm → ramp → alarm → music → settle IDLE → roll forward."""
    freezer.move_to(at(5, 0))
    entry = env.make_entry()
    coord = await env.build(entry, days=SAT)

    assert coord.state == STATE_IDLE
    assert coord.next_fire == at(7, 0)

    # Ramp fires at 06:45 (alarm 07:00 - 15 min). Hold it so we see RAMPING.
    env.ramp.block()
    await fire_until_started(env.hass, freezer, at(6, 45), env.ramp)
    assert coord.state == STATE_RAMPING
    assert env.ramp.calls == 1

    # Ramp finishes a quarter-hour before the alarm and we drop back to IDLE
    # WITHOUT re-firing (the #21 invariant).
    env.ramp.release()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    assert coord.next_fire == at(7, 0)

    # Alarm fires at 07:00 → music starts + standard notification.
    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING
    assert env.music.calls == 1

    env.music.release()
    await env.hass.async_block_till_done()
    assert env.send_standard.await_count == 1
    assert coord.state == STATE_IDLE
    # Schedule rolled to the next enabled day; ramp never restarted.
    assert coord.next_fire == NEXT_WEEK
    assert env.ramp.calls == 1


async def test_ramp_finishing_just_before_alarm_does_not_refire(
    env, freezer
) -> None:
    """#21 regression: ramp completing seconds before alarm never restarts."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)

    # Ramp fires and completes immediately, well before alarm_time.
    await fire(env.hass, freezer, at(6, 59, 52))
    assert env.ramp.calls == 1
    assert coord.state == STATE_IDLE
    # Today's alarm is still selected (not re-rolled by the IDLE transition).
    assert coord.next_fire == at(7, 0)

    # The alarm still fires exactly once; the ramp is not kicked off again.
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
    assert env.ramp.calls == 1
    assert coord.next_fire == NEXT_WEEK


async def test_music_survives_ramp_failure(env, freezer) -> None:
    """A raising light ramp must never stop the alarm from sounding."""
    freezer.move_to(at(5, 0))
    env.ramp.exc = RuntimeError("boom")
    coord = await env.build(env.make_entry(), days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    # Ramp raised, was contained, and we're back to IDLE.
    assert env.ramp.calls == 1
    assert coord.state == STATE_IDLE

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
    assert env.send_standard.await_count == 1


async def test_empty_light_list_still_plays_music(env, freezer) -> None:
    """No lights configured doesn't break the independent music path."""
    freezer.move_to(at(5, 0))
    entry = env.make_entry(light_entities=[])
    coord = await env.build(entry, days=SAT)

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING
    assert env.music.calls == 1
    env.music.release()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    assert coord.next_fire == NEXT_WEEK


async def test_zero_length_ramp_and_alarm_coincide(env, freezer) -> None:
    """length_min == 0 → ramp_start == alarm_time, fired without double-fire."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT, length_min=0)
    assert coord.next_fire == at(7, 0)

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
    assert coord.state == STATE_IDLE
    assert coord.next_fire == NEXT_WEEK


# --------------------------------------------------------------------------
# lights-only alarm (no media player configured) — #22
# --------------------------------------------------------------------------


async def test_lights_only_alarm_runs_ramp_no_music(env, freezer) -> None:
    """No media player → ramp runs, no music, friendly standard notice only."""
    freezer.move_to(at(5, 0))
    entry = env.make_entry(media_player_entities=[])
    coord = await env.build(entry, days=SAT)

    # The ramp still runs on its own timer.
    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 1

    # At alarm time: no music, the standard notification fires, and neither
    # urgent notice (players-unavailable / no-media) is sent.
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert env.send_standard.await_count == 1
    assert env.send_player_unavailable.await_count == 0
    assert env.send_no_media.await_count == 0
    assert coord.state == STATE_IDLE
    assert coord.next_fire == NEXT_WEEK


async def test_lights_only_snooze_during_ramp_settles_idle(env, freezer) -> None:
    """Snoozing a lights-only ramp has nothing to resume → settles to idle."""
    freezer.move_to(at(5, 0))
    entry = env.make_entry(media_player_entities=[])
    coord = await env.build(entry, days=SAT, snooze_min=4)

    env.ramp.block()
    await fire_until_started(env.hass, freezer, at(6, 45), env.ramp)
    assert coord.state == STATE_RAMPING

    await coord.async_snooze()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_SNOOZING

    # Snooze fires: no media players, so nothing resumes — must not hang.
    await fire(env.hass, freezer, at(6, 49))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert coord.state == STATE_IDLE


# --------------------------------------------------------------------------
# presence (checked independently at ramp_start and alarm_time)
# --------------------------------------------------------------------------


async def test_presence_away_at_ramp_home_at_alarm(env, freezer) -> None:
    """Away when the ramp would start → lights skipped; home → music plays."""
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("person.me", "not_home")
    entry = env.make_entry(person_entity="person.me")
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 0  # lights gated by absence
    assert coord.state == STATE_IDLE

    env.hass.states.async_set("person.me", "home")
    await env.hass.async_block_till_done()
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1


async def test_presence_home_at_ramp_away_at_alarm(env, freezer) -> None:
    """Home for the ramp but gone by alarm_time → lights run, music gated."""
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("person.me", "home")
    entry = env.make_entry(person_entity="person.me")
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 1

    env.hass.states.async_set("person.me", "not_home")
    await env.hass.async_block_till_done()
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    # Schedule still rolls forward even though the alarm was skipped.
    assert coord.next_fire == NEXT_WEEK


# --------------------------------------------------------------------------
# condition sensor gate (binary_sensor) — #23
# --------------------------------------------------------------------------


async def test_condition_off_skips_ramp_and_music(env, freezer) -> None:
    """Condition sensor off → neither the ramp nor the music run."""
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("binary_sensor.bed", "off")
    entry = env.make_entry(condition_entity="binary_sensor.bed")
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 0

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    # Schedule still rolls forward even though the alarm was gated off.
    assert coord.next_fire == NEXT_WEEK


async def test_condition_on_allows_alarm(env, freezer) -> None:
    """Condition sensor on → the alarm runs normally."""
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("binary_sensor.bed", "on")
    entry = env.make_entry(condition_entity="binary_sensor.bed")
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 1

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
    assert coord.next_fire == NEXT_WEEK


async def test_condition_on_at_ramp_off_at_alarm(env, freezer) -> None:
    """Checked twice: on at ramp-start (lights run), off by alarm (music gated)."""
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("binary_sensor.bed", "on")
    entry = env.make_entry(condition_entity="binary_sensor.bed")
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 1

    env.hass.states.async_set("binary_sensor.bed", "off")
    await env.hass.async_block_till_done()
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert coord.next_fire == NEXT_WEEK


async def test_presence_and_condition_are_anded(env, freezer) -> None:
    """Person home but condition off → still gated (presence AND condition)."""
    freezer.move_to(at(5, 0))
    env.hass.states.async_set("person.me", "home")
    env.hass.states.async_set("binary_sensor.bed", "off")
    entry = env.make_entry(
        person_entity="person.me", condition_entity="binary_sensor.bed"
    )
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert env.ramp.calls == 0
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert coord.next_fire == NEXT_WEEK


# --------------------------------------------------------------------------
# restart catch-up (computed at async_setup time)
# --------------------------------------------------------------------------


async def test_restart_within_grace_fires_now(env, freezer) -> None:
    """Booting just after a missed alarm (within grace) fires music now."""
    freezer.move_to(at(7, 5))  # 5 min after a 07:00 alarm, grace is 15
    coord = await env.build(env.make_entry(), days=SAT)
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
    assert coord.next_fire == NEXT_WEEK


async def test_restart_beyond_grace_rolls_forward(env, freezer) -> None:
    """Booting past the grace window just rolls to the next day; no fire."""
    freezer.move_to(at(7, 20))  # 20 min after, beyond the 15-min grace
    coord = await env.build(env.make_entry(), days=SAT)
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert coord.next_fire == NEXT_WEEK


async def test_restart_inside_ramp_window_skips_ramp_keeps_alarm(
    env, freezer
) -> None:
    """Boot mid-ramp-window: music still fires on time, the ramp is skipped."""
    freezer.move_to(at(6, 45))  # alarm 07:00, length 30 → ramp_start 06:30 (past)
    coord = await env.build(env.make_entry(), days=SAT, length_min=30)
    assert coord.next_fire == at(7, 0)

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.ramp.calls == 0  # ramp_start already elapsed at boot
    assert env.music.calls == 1


# --------------------------------------------------------------------------
# snooze / dismiss / auto-dismiss
# --------------------------------------------------------------------------


async def test_snooze_pauses_then_resumes(env, freezer) -> None:
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT, snooze_min=4)

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING

    await coord.async_snooze()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_SNOOZING
    assert len(env.media_calls["media_pause"]) == 1
    assert coord.snooze_finishes_at == at(7, 4)

    # Snooze timer fires → music resumes, skipping the group-join preamble.
    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 4), env.music)
    assert coord.state == STATE_PLAYING
    assert env.music.calls == 2
    assert env.music.kwargs_log[-1].get("from_snooze") is True


async def test_snooze_during_ramp_resumes_with_full_music_start(
    env, freezer
) -> None:
    """Snoozing during the ramp (music never played) resumes with
    from_snooze=False, so the Sonos group-join preamble still runs."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT, snooze_min=4)

    env.ramp.block()
    await fire_until_started(env.hass, freezer, at(6, 45), env.ramp)
    assert coord.state == STATE_RAMPING

    await coord.async_snooze()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_SNOOZING

    # Snooze fires at 06:49 → music starts fresh (no group formed during ramp).
    env.music.block()
    await fire_until_started(env.hass, freezer, at(6, 49), env.music)
    assert coord.state == STATE_PLAYING
    assert env.music.calls == 1
    assert env.music.kwargs_log[-1].get("from_snooze") is False


async def test_auto_dismiss_deadline_not_extended_by_snooze(
    env, freezer
) -> None:
    """The auto-dismiss deadline is fixed at first fire, never pushed out."""
    freezer.move_to(at(5, 0))
    coord = await env.build(
        env.make_entry(), days=SAT, snooze_min=4, auto_dismiss_min=30
    )

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord._auto_dismiss_deadline == at(7, 30)

    await coord.async_snooze()
    await env.hass.async_block_till_done()
    assert coord._auto_dismiss_deadline == at(7, 30)  # preserved across snooze

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 4), env.music)  # resume
    assert coord.state == STATE_PLAYING
    # Still 30 min after the *original* fire, not 30 after the resume.
    assert coord._auto_dismiss_deadline == at(7, 30)


async def test_auto_dismiss_fires_during_snooze(env, freezer) -> None:
    """#38: a snooze in progress must not let the alarm outlive auto-dismiss."""
    freezer.move_to(at(5, 0))
    coord = await env.build(
        env.make_entry(), days=SAT, snooze_min=10, auto_dismiss_min=2
    )

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING
    assert coord._auto_dismiss_deadline == at(7, 2)

    # Snooze for 10 min at 07:00 — without the fix this would resume music at
    # 07:10, well past the 07:02 auto-dismiss deadline.
    await coord.async_snooze()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_SNOOZING

    # The deadline lands mid-snooze: auto-dismiss fires and stops everything.
    await fire(env.hass, freezer, at(7, 2))
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    assert env.music.calls == 1  # snooze never resumed
    assert coord.next_fire == NEXT_WEEK


async def test_dismiss_during_ramp_skips_today(env, freezer) -> None:
    """Dismiss before alarm_time rolls past today; the alarm never fires."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)

    env.ramp.block()
    await fire_until_started(env.hass, freezer, at(6, 45), env.ramp)
    assert coord.state == STATE_RAMPING

    await coord.async_dismiss()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    assert len(env.media_calls["media_stop"]) == 1
    # Rolled past today even though we dismissed before alarm_time.
    assert coord.next_fire == NEXT_WEEK

    # The cancelled alarm timer must not fire.
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0


async def test_master_disable_mid_cycle_dismisses(env, freezer) -> None:
    """Flipping the enable switch off while active triggers a dismiss."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING

    env.hass.states.async_set("switch.test_enabled", "off")
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    assert len(env.media_calls["media_stop"]) == 1


# --------------------------------------------------------------------------
# failure / no-music paths
# --------------------------------------------------------------------------


async def test_player_unavailable_sends_urgent_and_settles(
    env, freezer
) -> None:
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)
    env.hass.states.async_set("media_player.bedroom", "unavailable")

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.send_player_unavailable.await_count == 1
    assert env.music.calls == 0
    assert coord.state == STATE_IDLE
    assert coord.next_fire == NEXT_WEEK


async def test_no_media_selected_sends_notice_and_settles(
    env, freezer
) -> None:
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT, media=None)

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.send_no_media.await_count == 1
    assert env.music.calls == 0
    assert coord.state == STATE_IDLE


# --------------------------------------------------------------------------
# before/after script hooks — #24
# --------------------------------------------------------------------------


async def test_before_at_ramp_after_on_music_end(env, freezer) -> None:
    """Before fires at ramp-start; after fires when music finishes naturally."""
    freezer.move_to(at(5, 0))
    before = async_mock_service(env.hass, "script", "before")
    after = async_mock_service(env.hass, "script", "after")
    entry = env.make_entry(
        before_script="script.before", after_script="script.after"
    )
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    await env.hass.async_block_till_done()
    assert len(before) == 1
    # Context variables are passed through to the script.
    assert before[0].data.get("slug") == "test"
    assert before[0].data.get("name") == "Test Alarm"
    assert len(after) == 0  # cycle still in progress

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
    assert len(after) == 1
    assert len(before) == 1  # before fires once per occurrence
    assert coord.state == STATE_IDLE


async def test_after_script_on_dismiss_not_snooze(env, freezer) -> None:
    """Snooze keeps the cycle open (no after); dismiss closes it (after once)."""
    freezer.move_to(at(5, 0))
    before = async_mock_service(env.hass, "script", "before")
    after = async_mock_service(env.hass, "script", "after")
    entry = env.make_entry(
        before_script="script.before", after_script="script.after"
    )
    coord = await env.build(entry, days=SAT, snooze_min=4)

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING
    assert len(before) == 1

    await coord.async_snooze()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_SNOOZING
    assert len(after) == 0  # snooze must not fire the after-script

    await coord.async_dismiss()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    assert len(after) == 1


async def test_scripts_run_for_lights_only_alarm(env, freezer) -> None:
    """Lights-only (#22) still runs both hooks: before at ramp, after at fire."""
    freezer.move_to(at(5, 0))
    before = async_mock_service(env.hass, "script", "before")
    after = async_mock_service(env.hass, "script", "after")
    entry = env.make_entry(
        media_player_entities=[],
        before_script="script.before",
        after_script="script.after",
    )
    await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert len(before) == 1

    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert len(after) == 1


async def test_master_disable_in_idle_gap_does_not_strand_cycle(
    env, freezer
) -> None:
    """#34 regression: disabling the master switch during the ramp→alarm gap
    must not strand _cycle_active, or the next occurrence's before-script is
    skipped.
    """
    freezer.move_to(at(5, 0))
    before = async_mock_service(env.hass, "script", "before")
    after = async_mock_service(env.hass, "script", "after")
    entry = env.make_entry(
        before_script="script.before", after_script="script.after"
    )
    coord = await env.build(entry, days=SAT)

    # Ramp fires at 06:45 and completes; cycle is now open across the idle gap.
    await fire(env.hass, freezer, at(6, 45))
    assert len(before) == 1
    assert coord.state == STATE_IDLE
    assert coord._cycle_active is True

    # User disables the master switch during the gap (before alarm_time).
    env.hass.states.async_set("switch.test_enabled", "off")
    await env.hass.async_block_till_done()
    # The cycle is closed out without firing the after-script (the alarm never
    # fired), and the alarm timer is cancelled.
    assert coord._cycle_active is False
    assert len(after) == 0
    assert coord.next_fire is None

    # Nothing fires at the old alarm time.
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0

    # Re-enable for the next occurrence; its before-script must fire again.
    env.hass.states.async_set("switch.test_enabled", "on")
    await env.hass.async_block_till_done()
    assert coord.next_fire == NEXT_WEEK

    nxt_ramp = at(6, 45) + timedelta(days=7)
    await fire(env.hass, freezer, nxt_ramp)
    await env.hass.async_block_till_done()
    assert len(before) == 2  # not stranded — before fires for the new occurrence


async def test_gated_alarm_after_ramp_abandons_cycle(env, freezer) -> None:
    """Home at ramp (before runs); away by alarm → after skipped, cycle reset."""
    freezer.move_to(at(5, 0))
    before = async_mock_service(env.hass, "script", "before")
    after = async_mock_service(env.hass, "script", "after")
    env.hass.states.async_set("person.me", "home")
    entry = env.make_entry(
        person_entity="person.me",
        before_script="script.before",
        after_script="script.after",
    )
    coord = await env.build(entry, days=SAT)

    await fire(env.hass, freezer, at(6, 45))
    assert len(before) == 1

    env.hass.states.async_set("person.me", "not_home")
    await env.hass.async_block_till_done()
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert len(after) == 0  # alarm gated → after not appropriate
    assert coord._cycle_active is False  # but the cycle is reset for next time


# --------------------------------------------------------------------------
# teardown / unload (#35)
# --------------------------------------------------------------------------


async def test_double_unload_is_idempotent(env, freezer) -> None:
    """async_unload must be safe to call twice (and clear tracked tasks)."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)
    await coord.async_unload()
    await coord.async_unload()  # must not raise
    assert coord._background_tasks == set()


async def test_unload_mid_ramp_cancels_ramp_task(env, freezer) -> None:
    """Unloading while the ramp is running cancels the task, leaving nothing."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)

    env.ramp.block()
    await fire_until_started(env.hass, freezer, at(6, 45), env.ramp)
    assert coord.state == STATE_RAMPING

    await coord.async_unload()
    await env.hass.async_block_till_done()
    assert coord._ramp_task is None
    assert coord._background_tasks == set()


async def test_unload_mid_music_no_timer_leak_no_after_script(
    env, freezer
) -> None:
    """Unloading while PLAYING must not let the cancelled music task's finally
    re-arm the schedule or fire the after-script.

    The teardown race: the music runner's finally runs on cancellation while
    still in PLAYING, which (with a deferred recompute pending) re-armed the
    ramp/alarm point-in-time timers AFTER async_unload had cancelled them, and
    fired the after-script on the way out.
    """
    freezer.move_to(at(5, 0))
    before = async_mock_service(env.hass, "script", "before")
    after = async_mock_service(env.hass, "script", "after")
    entry = env.make_entry(
        before_script="script.before", after_script="script.after"
    )
    coord = await env.build(entry, days=SAT)

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING
    assert len(before) == 1

    # A watched dependency changes during playback → deferred recompute, which
    # the music finally would otherwise apply (and re-arm timers) on unload.
    env.hass.states.async_set("time.test_alarm_time", "07:30:00")
    await asyncio.sleep(0)
    assert coord._recompute_pending is True

    await coord.async_unload()
    await env.hass.async_block_till_done()

    # No after-script on teardown, no lingering tasks, and both schedule timers
    # cancelled (not re-armed by the finally).
    assert len(after) == 0
    assert coord._cancel_alarm_schedule is None
    assert coord._cancel_ramp_schedule is None
    assert coord._background_tasks == set()


# --------------------------------------------------------------------------
# settings changes re-arm the timers
# --------------------------------------------------------------------------


async def test_setting_change_during_playback_no_same_day_refire(
    env, freezer
) -> None:
    """#44: editing the alarm time while PLAYING must not arm a second fire
    today; the change is deferred and applied (skipping today) on settle."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)

    env.music.block()
    await fire_until_started(env.hass, freezer, at(7, 0), env.music)
    assert coord.state == STATE_PLAYING
    # The schedule already rolled forward to next week when the alarm fired.
    assert coord.next_fire == NEXT_WEEK

    # User pushes the alarm later the same day while it's still playing. The
    # dependency-change callback runs synchronously on async_set, so we don't
    # block_till_done here (the music runner is held and would never settle).
    env.hass.states.async_set("time.test_alarm_time", "07:30:00")
    await asyncio.sleep(0)
    # Deferred: next_fire is untouched, NOT re-pointed at today 07:30.
    assert coord.next_fire == NEXT_WEEK
    assert coord._recompute_pending is True

    env.music.release()
    await env.hass.async_block_till_done()
    assert coord.state == STATE_IDLE
    # Now applied: next week at the new time, today skipped.
    assert coord.next_fire == NEXT_WEEK + timedelta(minutes=30)
    assert coord._recompute_pending is False

    # Nothing fires at today 07:30.
    await fire(env.hass, freezer, at(7, 30))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1


async def test_test_music_ignored_during_ramp_alarm_gap(env, freezer) -> None:
    """#43: Test music pressed in the ramp→alarm IDLE gap is refused, so it
    can't occupy the music task and silence the real alarm."""
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)

    # Ramp fires and settles; the occurrence stays open across the gap.
    await fire(env.hass, freezer, at(6, 45))
    assert coord.state == STATE_IDLE
    assert coord._cycle_active is True

    # Test music in the gap is rejected (IDLE, but a cycle is in flight).
    await coord.async_test_music()
    await env.hass.async_block_till_done()
    assert env.music.calls == 0
    assert coord.state == STATE_IDLE

    # The real alarm still plays music exactly once.
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1


async def test_alarm_time_change_rearms_timers(env, freezer) -> None:
    freezer.move_to(at(5, 0))
    coord = await env.build(env.make_entry(), days=SAT)
    assert coord.next_fire == at(7, 0)

    # Push the alarm an hour later; the schedule must re-arm to 08:00.
    env.hass.states.async_set("time.test_alarm_time", "08:00:00")
    await env.hass.async_block_till_done()
    assert coord.next_fire == at(8, 0)

    # The old 07:00 timer is gone — nothing fires.
    await fire(env.hass, freezer, at(7, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 0

    # The new 08:00 timer fires.
    await fire(env.hass, freezer, at(8, 0))
    await env.hass.async_block_till_done()
    assert env.music.calls == 1
