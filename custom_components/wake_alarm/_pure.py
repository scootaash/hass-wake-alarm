"""Pure helpers with zero Home Assistant imports.

Anything in this module can be unit-tested in isolation by loading the
file directly (importlib.util.spec_from_file_location), no HA fixtures
required. Modules that need HA depend on this one rather than the other
way around.
"""
from __future__ import annotations

from datetime import datetime, time as dt_time, timedelta
from typing import NamedTuple


# -------------------- light ramp math --------------------


def compute_step_target(
    idx: int, total_steps: int, max_pct: int, start_k: int, target_k: int
) -> tuple[int, int]:
    """Per-step linear interpolation.

    Returns (brightness_pct, kelvin) for the given 0-based step index.
    Mirrors scripts.alarm_light_ramp's idx ∈ [0, total_steps-1] interpolation
    using denom = total_steps - 1.
    """
    if total_steps <= 1:
        return max_pct, target_k
    denom = total_steps - 1
    pct = round(1.0 + ((max_pct - 1.0) / denom) * idx)
    kelvin = round(start_k + ((target_k - start_k) / denom) * idx)
    return int(pct), int(kelvin)


def clamp_kelvin(k: int) -> int:
    if k < 1500:
        return 1500
    if k > 6500:
        return 6500
    return k


# -------------------- schedule math --------------------


def compute_next_fire(
    now: datetime, alarm_time: dt_time, enabled_days: set[int]
) -> datetime | None:
    """Next future occurrence of alarm_time on an enabled day.

    For each weekday offset 0..7, materialise alarm_time on that day and
    return the first candidate that is both on an enabled day AND strictly
    in the future. Day boundaries roll over correctly because we anchor on
    `now`'s timezone-aware date and walk forward in 1-day steps.
    """
    if not enabled_days:
        return None
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


class ScheduleDecision(NamedTuple):
    """Outcome of deciding what the scheduler should do right now.

    next_fire           the alarm_time we are aiming for (catch-up target if
                        fire_now is set, otherwise the next future occurrence);
                        None when nothing is scheduled.
    ramp_start          next_fire - length_min, or None when next_fire is None.
    fire_now            True when alarm_time on an enabled day has already
                        passed within the grace window (HA was down) and we
                        should fire the alarm immediately.
    inside_ramp_window  True when now falls between ramp_start and next_fire
                        (informational; lets callers decide on a partial ramp).
    """

    next_fire: datetime | None
    ramp_start: datetime | None
    fire_now: bool
    inside_ramp_window: bool


def plan_schedule(
    now: datetime,
    alarm_time: dt_time,
    enabled_days: set[int],
    length_min: int,
    grace_min: int,
) -> ScheduleDecision:
    """Decide whether to fire now (catch-up), arm timers, or skip.

    Wraps compute_next_fire and layers a restart catch-up window on top: if
    today's alarm sits on an enabled day, has already passed, and did so within
    `grace_min` minutes, we return fire_now=True targeting today so the alarm
    still goes off after a late boot. Otherwise we return the next strictly
    future occurrence with fire_now=False.

    Pure: no Home Assistant imports, fully unit-testable.
    """
    if not enabled_days:
        return ScheduleDecision(None, None, False, False)

    length = timedelta(minutes=length_min)
    today_at = now.replace(
        hour=alarm_time.hour,
        minute=alarm_time.minute,
        second=alarm_time.second,
        microsecond=0,
    )

    if (
        today_at.weekday() in enabled_days
        and today_at <= now
        and (now - today_at) <= timedelta(minutes=grace_min)
    ):
        ramp_start = today_at - length
        return ScheduleDecision(
            next_fire=today_at,
            ramp_start=ramp_start,
            fire_now=True,
            inside_ramp_window=ramp_start <= now,
        )

    future = compute_next_fire(now, alarm_time, enabled_days)
    if future is None:
        return ScheduleDecision(None, None, False, False)
    ramp_start = future - length
    return ScheduleDecision(
        next_fire=future,
        ramp_start=ramp_start,
        fire_now=False,
        inside_ramp_window=ramp_start <= now < future,
    )


# -------------------- notification action IDs --------------------


_ACTION_PREFIX = "wake_alarm:"


def build_action_id(action: str, entry_id: str) -> str:
    """Build a stable, parseable action ID for a notification button."""
    return f"{_ACTION_PREFIX}{action}:{entry_id}"


def parse_action_id(action: str) -> tuple[str, str] | None:
    """Inverse of build_action_id. Returns (action, entry_id) or None.

    Rejects malformed strings: missing prefix, fewer than three parts, or
    either part empty.
    """
    if not action.startswith(_ACTION_PREFIX):
        return None
    parts = action.split(":", 2)
    if len(parts) != 3:
        return None
    action_name, entry_id = parts[1], parts[2]
    if not action_name or not entry_id:
        return None
    return action_name, entry_id
