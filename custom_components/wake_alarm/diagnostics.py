"""Diagnostics support for Wake Alarm.

Home Assistant auto-discovers ``async_get_config_entry_diagnostics`` and wires up
the "Download diagnostics" button on the config entry. Returns the entry data
(with the person / notify targets redacted) plus a live snapshot of the
coordinator's scheduler + state machine, so a bug report carries the data needed
to see whether the alarm scheduled and fired correctly.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
    CONF_PERSON_ENTITY,
    DOMAIN,
)

# Entity IDs that name a person or a user's device are mildly identifying;
# redact them. Light / media-player / condition / script targets are kept —
# they're the useful part of a diagnostics dump and aren't sensitive.
TO_REDACT = {
    CONF_PERSON_ENTITY,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    coordinator = entry_data.get("coordinator") if entry_data else None
    return {
        "entry": {
            "version": entry.version,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "coordinator": (
            coordinator.diagnostics_snapshot() if coordinator is not None else None
        ),
    }
