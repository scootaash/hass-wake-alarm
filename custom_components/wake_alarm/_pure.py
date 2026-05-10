"""Pure helpers with zero Home Assistant imports.

Anything in this module can be unit-tested in isolation by loading the
file directly (importlib.util.spec_from_file_location), no HA fixtures
required. Modules that need HA depend on this one rather than the other
way around.
"""
from __future__ import annotations

from datetime import datetime, time as dt_time, timedelta


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


# -------------------- notification action IDs --------------------


_ACTION_PREFIX = "wake_alarm:"


def build_action_id(action: str, entry_id: str) -> str:
    """Build a stable, parseable action ID for a notification button."""
    return f"{_ACTION_PREFIX}{action}:{entry_id}"


def parse_action_id(action: str) -> tuple[str, str] | None:
    """Inverse of build_action_id. Returns (action, entry_id) or None."""
    if not action.startswith(_ACTION_PREFIX):
        return None
    parts = action.split(":", 2)
    if len(parts) != 3:
        return None
    return parts[1], parts[2]
