"""The Wake Alarm integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import WakeAlarmCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

# The card bundle ships inside the integration so the user only has to
# install the repo once (HACS Integration). The integration registers the
# bundle as a static path at this URL and tells the frontend to load it.
_CARD_URL = "/wake_alarm/wake-alarm-card.js"
_CARD_PATH = Path(__file__).parent / "www" / "wake-alarm-card.js"

# Bookkeeping key inside hass.data[DOMAIN]; underscore-prefixed so the
# entry-id lookup ignores it.
_CARD_REGISTERED_KEY = "_card_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wake Alarm from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = WakeAlarmCoordinator(hass, entry)
    await coordinator.async_setup()
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async_setup_services(hass)
    await _async_register_card(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data is not None:
            coordinator: WakeAlarmCoordinator = data["coordinator"]
            await coordinator.async_unload()
        # Drop services + the global action listener once the last entry
        # is gone. Internal keys (prefixed with "_") are bookkeeping for
        # async_setup_services itself and the card registration.
        domain_data = hass.data.get(DOMAIN, {})
        if not any(not k.startswith("_") for k in domain_data):
            async_unload_services(hass)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve the Lovelace card bundle and auto-register it as a frontend resource.

    Means a single HACS install (Integration category) is enough — the user
    does not have to add the same repo a second time as Dashboard, and does
    not have to register the URL in Settings → Dashboards → Resources.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_CARD_REGISTERED_KEY):
        return
    if not _CARD_PATH.is_file():
        _LOGGER.warning(
            "card bundle missing at %s; skipping resource registration",
            _CARD_PATH,
        )
        return

    # Modern API (HA 2024.7+) takes a list of StaticPathConfig objects;
    # older versions had register_static_path. Use whichever is available.
    if hasattr(hass.http, "async_register_static_paths"):
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(_CARD_PATH), True)]
        )
    else:
        hass.http.register_static_path(_CARD_URL, str(_CARD_PATH), True)

    add_extra_js_url(hass, _CARD_URL)
    domain_data[_CARD_REGISTERED_KEY] = True
    _LOGGER.info("registered wake-alarm-card at %s", _CARD_URL)
