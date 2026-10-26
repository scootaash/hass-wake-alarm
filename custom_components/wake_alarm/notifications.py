"""Mobile notifications for wake_alarm.

Three payloads, one transport:

- standard: sent at alarm_time when music starts. Distinct iOS
  interruption-level "active" + Android channel "wake_alarm_standard"
  so users can configure a custom sound per channel.
- player_unavailable: sent when any required media_player is
  unavailable at alarm_time. Critical iOS payload + Android channel
  "wake_alarm_urgent" with importance HIGH.
- no_media: same urgent transport as player_unavailable, different
  copy (the user has not yet picked media via the card).

Each payload includes two action buttons (Snooze + Dismiss) whose
action IDs encode the config-entry ID; services.py listens for
mobile_app_notification_action events and routes by entry.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ._pure import build_action_id, parse_action_id
from .const import (
    CONF_NOTIFY_TAP_PATH,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
)

if TYPE_CHECKING:
    from .coordinator import WakeAlarmCoordinator

_LOGGER = logging.getLogger(__name__)

ACTION_SNOOZE = "snooze"
ACTION_DISMISS = "dismiss"

# Re-exported so existing imports (services.py) keep working.
__all__ = (
    "ACTION_SNOOZE",
    "ACTION_DISMISS",
    "build_action_id",
    "parse_action_id",
    "async_send_standard",
    "async_send_player_unavailable",
    "async_send_no_media",
)


def _action_buttons(entry_id: str) -> list[dict]:
    return [
        {"action": build_action_id(ACTION_SNOOZE, entry_id), "title": "Snooze"},
        {"action": build_action_id(ACTION_DISMISS, entry_id), "title": "Dismiss"},
    ]


def _normalize_path(raw: str | None) -> str | None:
    """Normalise the configured notification tap target into a deep link.

    Returns None when nothing is configured. A bare dashboard path
    (``lovelace/0``) gets a leading slash so the companion app treats it as an
    in-app navigation; an explicit scheme (``homeassistant://navigate/...``,
    ``https://...``) or an already-absolute path is passed through untouched.
    """
    if not raw:
        return None
    path = raw.strip()
    if not path:
        return None
    if "://" in path or path.startswith("/"):
        return path
    return f"/{path}"


async def _send(
    coordinator: "WakeAlarmCoordinator",
    *,
    target: str,
    title: str,
    message: str,
    urgent: bool,
) -> None:
    if not target or not target.startswith("notify."):
        _LOGGER.debug(
            "skipping notification for %s: invalid target %r",
            coordinator.slug,
            target,
        )
        return
    service = target.split(".", 1)[1]

    data: dict = {"actions": _action_buttons(coordinator.entry.entry_id)}

    # Optional deep link: tapping the notification body opens this dashboard
    # path. iOS uses `url`, Android uses `clickAction` — set both so one
    # configured path works on either companion app.
    tap_path = _normalize_path(
        coordinator.entry.data.get(CONF_NOTIFY_TAP_PATH)
    )
    if tap_path:
        data["url"] = tap_path
        data["clickAction"] = tap_path

    if urgent:
        # iOS critical alert + Android urgent channel
        data["push"] = {
            "sound": {"critical": 1, "name": "default", "volume": 1.0},
            "interruption-level": "critical",
        }
        data["channel"] = "wake_alarm_urgent"
        data["importance"] = "high"
    else:
        # iOS active interruption + Android default channel
        data["push"] = {"interruption-level": "active"}
        data["channel"] = "wake_alarm_standard"
        data["importance"] = "default"

    payload = {"title": title, "message": message, "data": data}
    try:
        await coordinator.hass.services.async_call(
            "notify", service, payload, blocking=False
        )
    except Exception:  # noqa: BLE001
        _LOGGER.exception(
            "failed to send notification for %s via notify.%s",
            coordinator.slug,
            service,
        )


async def async_send_standard(coordinator: "WakeAlarmCoordinator") -> None:
    """Standard alarm notification at alarm_time."""
    target = coordinator.entry.data.get(CONF_NOTIFY_TARGET_STANDARD)
    if not target:
        return
    await _send(
        coordinator,
        target=target,
        title=f"{coordinator.name} Alarm",
        message="Alarm playing. Snooze or Dismiss.",
        urgent=False,
    )


async def async_send_player_unavailable(
    coordinator: "WakeAlarmCoordinator",
    unavailable_entity_ids: list[str],
) -> None:
    """Urgent fallback when any required player is unavailable."""
    target = coordinator.entry.data.get(CONF_NOTIFY_TARGET_URGENT)
    if not target:
        return
    label = _friendly_label(coordinator, unavailable_entity_ids)
    await _send(
        coordinator,
        target=target,
        title="Alarm: speaker unavailable",
        message=f"Lights are on but {label} couldn't play. Wake up.",
        urgent=True,
    )


async def async_send_no_media(coordinator: "WakeAlarmCoordinator") -> None:
    """Urgent fallback when nothing has been picked via the card."""
    target = coordinator.entry.data.get(CONF_NOTIFY_TARGET_URGENT)
    if not target:
        return
    await _send(
        coordinator,
        target=target,
        title="Alarm: no media configured",
        message=(
            "Lights are on but no media is configured. "
            "Open the alarm card to pick what to play."
        ),
        urgent=True,
    )


def _friendly_label(
    coordinator: "WakeAlarmCoordinator", entity_ids: list[str]
) -> str:
    labels: list[str] = []
    for ent_id in entity_ids:
        st = coordinator.hass.states.get(ent_id)
        if st is not None and st.attributes.get("friendly_name"):
            labels.append(st.attributes["friendly_name"])
        else:
            labels.append(ent_id)
    return ", ".join(labels)
