"""Tests for compute_next_fire (next-alarm scheduling).

Validates the day-of-week + future-only filter logic. DST is exercised
by anchoring `now` to a date right around a UK clocks-forward transition.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from datetime import time as dt_time
from types import ModuleType
from zoneinfo import ZoneInfo


class TestComputeNextFire:
    def test_returns_none_with_no_enabled_days(self, pure: ModuleType) -> None:
        now = datetime(2026, 5, 9, 6, 0, tzinfo=timezone.utc)
        assert pure.compute_next_fire(now, dt_time(7, 0), set()) is None

    def test_today_when_alarm_in_future(self, pure: ModuleType) -> None:
        # Saturday May 9 2026, 06:00 UTC; alarm at 07:00 today.
        now = datetime(2026, 5, 9, 6, 0, tzinfo=timezone.utc)
        result = pure.compute_next_fire(now, dt_time(7, 0), {5})  # Saturday=5
        assert result is not None
        assert result.weekday() == 5
        assert result.hour == 7
        assert result.date() == now.date()

    def test_skips_today_when_alarm_in_past(self, pure: ModuleType) -> None:
        # Saturday 09:00; alarm at 07:00 today has passed → next Sat
        now = datetime(2026, 5, 9, 9, 0, tzinfo=timezone.utc)
        result = pure.compute_next_fire(now, dt_time(7, 0), {5})
        assert result is not None
        assert result.weekday() == 5
        assert (result - now) >= timedelta(days=6)

    def test_picks_next_enabled_weekday(self, pure: ModuleType) -> None:
        # Saturday May 9 2026, weekdays-only (Mon=0..Fri=4) → next is Mon
        now = datetime(2026, 5, 9, 9, 0, tzinfo=timezone.utc)
        result = pure.compute_next_fire(
            now, dt_time(7, 0), {0, 1, 2, 3, 4}
        )
        assert result is not None
        assert result.weekday() == 0  # Monday
        assert result.date() == (now.date() + timedelta(days=2))

    def test_alarm_strictly_in_future(self, pure: ModuleType) -> None:
        # If now == alarm-time-on-today, it's NOT in the future → next week.
        now = datetime(2026, 5, 9, 7, 0, tzinfo=timezone.utc)
        result = pure.compute_next_fire(now, dt_time(7, 0), {5})
        assert result is not None
        assert (result - now) == timedelta(days=7)

    def test_seven_day_window(self, pure: ModuleType) -> None:
        # Single enabled day, alarm has passed → exactly +7 days.
        now = datetime(2026, 5, 4, 9, 0, tzinfo=timezone.utc)  # Mon
        result = pure.compute_next_fire(now, dt_time(7, 0), {0})
        assert result is not None
        assert result == datetime(2026, 5, 11, 7, 0, tzinfo=timezone.utc)

    def test_dst_spring_forward_uk(self, pure: ModuleType) -> None:
        # 2026-03-29 is the UK clocks-forward date (BST starts 01:00 UTC).
        # Alarm 07:00 local on Sunday should still fire at 07:00 local even
        # though the previous day was 23h long.
        london = ZoneInfo("Europe/London")
        now = datetime(2026, 3, 28, 23, 0, tzinfo=london)  # Sat 23:00 BST eve
        result = pure.compute_next_fire(
            now, dt_time(7, 0), {6}  # Sunday=6
        )
        assert result is not None
        assert result.tzinfo is not None
        # 07:00 on the Sunday, regardless of DST shift overnight.
        assert result.hour == 7
        assert result.weekday() == 6

    def test_dst_normal_alarm_across_transition_keeps_wall_time(
        self, pure: ModuleType
    ) -> None:
        # #36: the everyday-important property. A 07:00 alarm on the Sunday
        # *after* spring-forward (BST) still fires at 07:00 wall-clock when
        # computed from a Friday that's still GMT. zoneinfo recomputes the
        # offset from the fields, so the resulting instant is 06:00 UTC.
        london = ZoneInfo("Europe/London")
        now = datetime(2026, 3, 27, 9, 0, tzinfo=london)  # Fri (GMT)
        result = pure.compute_next_fire(now, dt_time(7, 0), {6})  # Sunday (BST)
        assert result is not None
        assert result.hour == 7
        assert result.astimezone(timezone.utc) == datetime(
            2026, 3, 29, 6, 0, tzinfo=timezone.utc
        )

    def test_dst_spring_forward_gap_alarm_is_deterministic(
        self, pure: ModuleType
    ) -> None:
        # #36: an alarm at 01:30 on the spring-forward day is a non-existent
        # local time (clocks jump 01:00 GMT → 02:00 BST). fold=0 resolves it to
        # a single, deterministic instant (01:30 GMT == 01:30 UTC) rather than
        # erroring or firing twice.
        london = ZoneInfo("Europe/London")
        now = datetime(2026, 3, 29, 0, 0, tzinfo=london)
        result = pure.compute_next_fire(now, dt_time(1, 30), {6})  # Sunday
        assert result is not None
        assert result.astimezone(timezone.utc) == datetime(
            2026, 3, 29, 1, 30, tzinfo=timezone.utc
        )

    def test_dst_fall_back_ambiguous_alarm_picks_earliest(
        self, pure: ModuleType
    ) -> None:
        # #36: an alarm at 01:30 on the fall-back day is ambiguous (01:30 BST
        # and 01:30 GMT both occur). fold=0 fires once, at the earliest (BST)
        # instance == 00:30 UTC.
        london = ZoneInfo("Europe/London")
        now = datetime(2026, 10, 25, 0, 0, tzinfo=london)
        result = pure.compute_next_fire(now, dt_time(1, 30), {6})  # Sunday
        assert result is not None
        assert result.astimezone(timezone.utc) == datetime(
            2026, 10, 25, 0, 30, tzinfo=timezone.utc
        )

    def test_returns_none_when_only_today_after_alarm_disabled(
        self, pure: ModuleType
    ) -> None:
        # If only Sunday is enabled and we're Sunday after the alarm time,
        # the next fire is +7 days.
        now = datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc)  # Sunday
        result = pure.compute_next_fire(now, dt_time(7, 0), {6})
        assert result is not None
        assert (result - now).days >= 6


class TestPlanSchedule:
    """plan_schedule: restart catch-up + arming decision (pure)."""

    SAT = {5}  # 2026-05-09 is a Saturday
    GRACE = 15

    def test_missed_within_grace_fires_now(self, pure: ModuleType) -> None:
        # 5 minutes after a 06:00 alarm that we missed (HA was down).
        now = datetime(2026, 5, 9, 6, 5, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), self.SAT, 30, self.GRACE)
        assert d.fire_now is True
        assert d.next_fire == datetime(2026, 5, 9, 6, 0, tzinfo=timezone.utc)
        assert d.ramp_start == datetime(2026, 5, 9, 5, 30, tzinfo=timezone.utc)

    def test_missed_beyond_grace_rolls_forward(self, pure: ModuleType) -> None:
        # 20 minutes after the alarm, past the 15-minute grace → next week.
        now = datetime(2026, 5, 9, 6, 20, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), self.SAT, 30, self.GRACE)
        assert d.fire_now is False
        assert d.next_fire == datetime(2026, 5, 16, 6, 0, tzinfo=timezone.utc)

    def test_grace_boundary_is_inclusive(self, pure: ModuleType) -> None:
        # Exactly grace minutes after the alarm still counts as catch-up.
        now = datetime(2026, 5, 9, 6, 15, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), self.SAT, 30, self.GRACE)
        assert d.fire_now is True

    def test_future_alarm_arms_not_fires(self, pure: ModuleType) -> None:
        # An hour before the alarm: normal arm, no catch-up.
        now = datetime(2026, 5, 9, 5, 0, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), self.SAT, 30, self.GRACE)
        assert d.fire_now is False
        assert d.next_fire == datetime(2026, 5, 9, 6, 0, tzinfo=timezone.utc)
        assert d.ramp_start == datetime(2026, 5, 9, 5, 30, tzinfo=timezone.utc)
        # now (05:00) is before ramp_start (05:30) → not inside the window.
        assert d.inside_ramp_window is False

    def test_inside_ramp_window_detected(self, pure: ModuleType) -> None:
        # Between ramp_start (05:30) and alarm (06:00).
        now = datetime(2026, 5, 9, 5, 45, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), self.SAT, 30, self.GRACE)
        assert d.fire_now is False
        assert d.inside_ramp_window is True

    def test_missed_today_but_today_disabled_no_catchup(
        self, pure: ModuleType
    ) -> None:
        # 5 min after 06:00 on Saturday, but only Monday is enabled →
        # no catch-up, roll forward to Monday.
        now = datetime(2026, 5, 9, 6, 5, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), {0}, 30, self.GRACE)
        assert d.fire_now is False
        assert d.next_fire == datetime(2026, 5, 11, 6, 0, tzinfo=timezone.utc)

    def test_zero_length_ramp_start_equals_next_fire(
        self, pure: ModuleType
    ) -> None:
        now = datetime(2026, 5, 9, 5, 0, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), self.SAT, 0, self.GRACE)
        assert d.ramp_start == d.next_fire

    def test_no_enabled_days_returns_empty(self, pure: ModuleType) -> None:
        now = datetime(2026, 5, 9, 6, 5, tzinfo=timezone.utc)
        d = pure.plan_schedule(now, dt_time(6, 0), set(), 30, self.GRACE)
        assert d.next_fire is None and d.fire_now is False

    def test_dst_spring_forward_catchup(self, pure: ModuleType) -> None:
        # 2026-03-29 UK clocks-forward Sunday; alarm 07:00 local, booting at
        # 07:05 local should catch up to 07:00 the same morning.
        london = ZoneInfo("Europe/London")
        now = datetime(2026, 3, 29, 7, 5, tzinfo=london)
        d = pure.plan_schedule(now, dt_time(7, 0), {6}, 30, self.GRACE)
        assert d.fire_now is True
        assert d.next_fire.hour == 7
        assert d.next_fire.date() == now.date()


class TestRescheduleTrap:
    """Regression guard for the mid-cycle ramp-restart bug.

    When a ramp finished a few seconds *before* alarm_time, recomputing the
    schedule at that instant re-selected today's alarm (still strictly in the
    future), whose ramp_start (alarm_time - length) was already in the past.
    async_track_point_in_time fires past targets immediately, so the alarm
    restarted its ramp from zero.

    The fix is structural: the coordinator no longer recomputes on the IDLE
    transition. Its non-catch-up recompute only runs when now >= alarm_time
    (the alarm firing), where compute_next_fire deterministically rolls to the
    next enabled day. These tests pin both halves of that invariant.
    """

    def test_recompute_just_before_alarm_would_pick_today(
        self, pure: ModuleType
    ) -> None:
        length_min = 30
        # Saturday 2026-05-09, 8 seconds before a 06:00 alarm.
        now = datetime(2026, 5, 9, 5, 59, 52, tzinfo=timezone.utc)
        next_fire = pure.compute_next_fire(now, dt_time(6, 0), {5})
        assert next_fire is not None
        # Today's alarm is still selected (strictly in the future)...
        assert next_fire == datetime(2026, 5, 9, 6, 0, tzinfo=timezone.utc)
        # ...with a past ramp_start — which is exactly why the coordinator must
        # NOT recompute at this moment (it no longer does).
        ramp_start = next_fire - timedelta(minutes=length_min)
        assert ramp_start < now

    def test_recompute_at_alarm_time_rolls_to_next_day(
        self, pure: ModuleType
    ) -> None:
        # The safe recompute moment: at/after alarm_time, today is excluded.
        now = datetime(2026, 5, 9, 6, 0, tzinfo=timezone.utc)
        next_fire = pure.compute_next_fire(now, dt_time(6, 0), {5})
        assert next_fire == datetime(2026, 5, 16, 6, 0, tzinfo=timezone.utc)


class TestActionId:
    def test_round_trip(self, pure: ModuleType) -> None:
        action_id = pure.build_action_id("snooze", "abc123")
        assert pure.parse_action_id(action_id) == ("snooze", "abc123")

    def test_round_trip_with_underscores(self, pure: ModuleType) -> None:
        # entry_ids are 32-char hex but other separators must round-trip too.
        action_id = pure.build_action_id("dismiss", "01HZ_VS_GP9_TEST")
        assert pure.parse_action_id(action_id) == ("dismiss", "01HZ_VS_GP9_TEST")

    def test_rejects_non_wake_alarm_prefix(self, pure: ModuleType) -> None:
        assert pure.parse_action_id("foo:bar:baz") is None
        assert pure.parse_action_id("WAKE_ALARM_SNOOZE_X") is None

    def test_rejects_too_few_parts(self, pure: ModuleType) -> None:
        assert pure.parse_action_id("wake_alarm:snooze") is None
        assert pure.parse_action_id("wake_alarm:") is None

    def test_rejects_empty_entry_id(self, pure: ModuleType) -> None:
        # An empty entry_id can never resolve to a coordinator, so treat it
        # as malformed rather than parsing as ("snooze", "").
        assert pure.parse_action_id("wake_alarm:snooze:") is None
        assert pure.parse_action_id("wake_alarm::abc") is None
