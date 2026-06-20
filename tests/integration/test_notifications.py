"""Notification payload tests.

The ``env`` fixture patches the *coordinator's* notification aliases, so these
call ``notifications.async_send_standard`` directly to exercise the real payload
builder and assert on what reaches the ``notify.*`` service.
"""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.wake_alarm import notifications
from custom_components.wake_alarm.notifications import _normalize_path


async def test_standard_notification_deep_links_when_tap_path_set(env) -> None:
    """A configured tap path becomes url + clickAction (normalised), and the
    Snooze/Dismiss action buttons are still present."""
    calls = async_mock_service(env.hass, "notify", "mobile")
    coord = await env.build(env.make_entry(notify_tap_path="lovelace/0"))

    await notifications.async_send_standard(coord)
    await env.hass.async_block_till_done()

    assert len(calls) == 1
    data = calls[0].data["data"]
    # Bare path gained a leading slash; both platform keys carry it.
    assert data["url"] == "/lovelace/0"
    assert data["clickAction"] == "/lovelace/0"
    # The action buttons are untouched.
    assert [a["title"] for a in data["actions"]] == ["Snooze", "Dismiss"]


async def test_standard_notification_no_deep_link_without_tap_path(env) -> None:
    """With no tap path configured the payload omits url/clickAction entirely."""
    calls = async_mock_service(env.hass, "notify", "mobile")
    coord = await env.build(env.make_entry())  # no notify_tap_path

    await notifications.async_send_standard(coord)
    await env.hass.async_block_till_done()

    assert len(calls) == 1
    data = calls[0].data["data"]
    assert "url" not in data
    assert "clickAction" not in data
    # Snooze/Dismiss are always present.
    assert [a["title"] for a in data["actions"]] == ["Snooze", "Dismiss"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("lovelace/0", "/lovelace/0"),  # bare path → leading slash
        ("  wake-alarm  ", "/wake-alarm"),  # trimmed + slashed
        ("/lovelace/home", "/lovelace/home"),  # already absolute → untouched
        ("homeassistant://navigate/lovelace/0", "homeassistant://navigate/lovelace/0"),
        ("https://ha.example/lovelace/0", "https://ha.example/lovelace/0"),
        ("", None),  # empty → nothing
        ("   ", None),  # whitespace only → nothing
        (None, None),  # unset → nothing
    ],
)
def test_normalize_path(raw, expected) -> None:
    assert _normalize_path(raw) == expected
