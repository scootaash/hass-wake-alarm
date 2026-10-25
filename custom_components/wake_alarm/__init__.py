"""The Wake Alarm integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from .const import (
    CONF_SLUG,
    DAY_KEY_MIGRATION,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import WakeAlarmCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

# The card bundle ships inside the integration so the user only has to
# install the repo once (HACS Integration). The integration registers the
# bundle as a static path at this URL and tells the frontend to load it.
_CARD_PATH_PART = "/wake_alarm/wake-alarm-card.js"
_CARD_PATH = Path(__file__).parent / "www" / "wake-alarm-card.js"

# Bookkeeping key inside hass.data[DOMAIN]; underscore-prefixed so the
# entry-id lookup ignores it.
_CARD_REGISTERED_KEY = "_card_registered"

# hass.data key of the lovelace component. Read by string rather than imported
# because its value changed shape across our supported range (a plain dict on
# the 2024.6 floor, a LovelaceData dataclass on current cores).
_LOVELACE_DATA = "lovelace"


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
        # The card static path + extra_js_url and the _card_registered flag are
        # deliberately left registered for the lifetime of the HA process:
        # HA's http stack has no clean per-path unregister, the resource is
        # domain-global (shared by all entries), and the flag keeps a later
        # re-add from registering a duplicate route (#19/#37). A full HA restart
        # clears and re-registers it cleanly.
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop the card's Lovelace resource when the last alarm is deleted.

    Otherwise an uninstalled integration leaves a resource that 404s on every
    dashboard load. The removed entry is still listed while this runs.
    """
    if any(
        other.entry_id != entry.entry_id
        for other in hass.config_entries.async_entries(DOMAIN)
    ):
        return
    resources = _lovelace_resources(hass)
    if resources is None or not _resources_writable(resources):
        return
    try:
        await _async_load_resources(resources)
        for item in list(resources.async_items()):
            if _is_card_resource(item):
                await resources.async_delete_item(item["id"])
    except Exception:  # cleanup must never block the removal
        _LOGGER.warning(
            "could not remove the wake-alarm-card Lovelace resource", exc_info=True
        )


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Migrate config entries to the current schema.

    v1 → v2: day-toggle entity keys renamed mon..sun → d1_mon..d7_sun
    so HA's alphabetical entity sort displays them in calendar order.
    Both unique_id and entity_id are updated in the entity registry; on/off
    state may reset to the default_on value (Mon-Fri on, Sat/Sun off) since
    RestoreEntity is keyed by entity_id and we are renaming it.

    v2 → v3: added the optional binary_sensor condition gate (#23). Additive
    optional field — absence of the key means no condition — so no stored-data
    transformation is needed; this step only advances the version.

    v3 → v4: added the optional before/after script hooks (#24). Additive
    optional fields; this step only advances the version.

    v4 → v5: added the optional at-alarm script hook. Additive optional field;
    this step only advances the version.

    v5 → v6: added the optional notification tap path (deep-link the
    notification to a dashboard). Additive optional field — absence of the key
    means tapping does nothing — so this step only advances the version.
    """
    if entry.version > 6:
        _LOGGER.error(
            "wake_alarm config entry %s is at version %s, cannot downgrade",
            entry.title,
            entry.version,
        )
        return False

    if entry.version == 1:
        registry = er.async_get(hass)
        slug = entry.data.get(CONF_SLUG, "")
        for old_key, new_key in DAY_KEY_MIGRATION.items():
            old_unique = f"{entry.entry_id}_{old_key}"
            entity_id = registry.async_get_entity_id(
                "switch", DOMAIN, old_unique
            )
            if entity_id is None:
                continue
            new_unique = f"{entry.entry_id}_{new_key}"
            new_entity_id = f"switch.{slug}_{new_key}" if slug else None
            registry.async_update_entity(
                entity_id,
                new_unique_id=new_unique,
                **(
                    {"new_entity_id": new_entity_id}
                    if new_entity_id
                    else {}
                ),
            )
            _LOGGER.info(
                "wake_alarm migration v1→v2: %s → %s", entity_id, new_entity_id
            )
        hass.config_entries.async_update_entry(entry, version=2)

    if entry.version == 2:
        hass.config_entries.async_update_entry(entry, version=3)

    if entry.version == 3:
        hass.config_entries.async_update_entry(entry, version=4)

    if entry.version == 4:
        hass.config_entries.async_update_entry(entry, version=5)

    if entry.version == 5:
        hass.config_entries.async_update_entry(entry, version=6)

    return True


async def _async_card_version(hass: HomeAssistant) -> str:
    """Return the integration's manifest version for cache-busting.

    Uses the loader, which reads the manifest off the event loop and caches it,
    rather than opening manifest.json synchronously (the #20 blocking call).
    Falls back to 'dev' if the version is missing.
    """
    integration = await async_get_integration(hass, DOMAIN)
    return str(integration.version) if integration.version else "dev"


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve the Lovelace card bundle and auto-register it as a frontend resource.

    Means a single HACS install (Integration category) is enough — the user
    does not have to add the same repo a second time as Dashboard, and does
    not have to register the URL in Settings → Dashboards → Resources.

    The URL we register with the frontend includes a ?v=<integration version>
    cache-bust suffix; the static path itself remains version-less, so
    browsers reliably fetch a fresh bundle when the integration is updated.

    The bundle is loaded as a Lovelace resource (see
    _async_ensure_lovelace_resource for why). add_extra_js_url is only the
    fallback for when that isn't possible, and never used alongside it.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_CARD_REGISTERED_KEY):
        return

    # Claim the flag before the first await. HA sets up multiple config entries
    # of a domain concurrently; if we only set this after awaiting the static
    # path registration, two entries both pass the guard above and the second
    # raises "method GET is already registered" (#19). Setting it here is
    # event-loop-atomic (no await between the guard check and this line). Roll
    # back on any failure (or a missing bundle) so a later retry can register.
    domain_data[_CARD_REGISTERED_KEY] = True
    try:
        # is_file() is a stat() — run it off the event loop rather than blocking
        # it (same class of issue as the #20 manifest open(); #37). Must come
        # after the flag claim above to keep that claim await-free (#19).
        if not await hass.async_add_executor_job(_CARD_PATH.is_file):
            _LOGGER.warning(
                "card bundle missing at %s; skipping resource registration",
                _CARD_PATH,
            )
            domain_data[_CARD_REGISTERED_KEY] = False
            return

        # Modern API (HA 2024.7+) takes a list of StaticPathConfig objects;
        # older versions had register_static_path. Use whichever is available.
        if hasattr(hass.http, "async_register_static_paths"):
            from homeassistant.components.http import StaticPathConfig

            await hass.http.async_register_static_paths(
                [StaticPathConfig(_CARD_PATH_PART, str(_CARD_PATH), True)]
            )
        else:
            hass.http.register_static_path(
                _CARD_PATH_PART, str(_CARD_PATH), True
            )

        version = await _async_card_version(hass)
        versioned_url = f"{_CARD_PATH_PART}?v={version}"
        # Never raises: a failure here must not roll back the flag after the
        # static route exists, or the next entry re-registers it (#19).
        if not await _async_ensure_lovelace_resource(hass, versioned_url):
            add_extra_js_url(hass, versioned_url)
    except Exception:
        domain_data[_CARD_REGISTERED_KEY] = False
        raise
    _LOGGER.info("registered wake-alarm-card at %s", versioned_url)


def _is_card_resource(item: dict[str, Any]) -> bool:
    """True for a Lovelace resource pointing at our bundle, any version.

    Matches on path so a stale ?v=, or a copy the user added by hand, is updated
    in place rather than duplicated.
    """
    return urlsplit(str(item.get("url", ""))).path == _CARD_PATH_PART


def _lovelace_resources(hass: HomeAssistant) -> Any | None:
    """Return the Lovelace resource collection, or None if lovelace isn't loaded.

    In YAML resource mode this is a read-only collection; see
    _resources_writable.
    """
    lovelace = hass.data.get(_LOVELACE_DATA)
    if lovelace is None:
        return None
    if isinstance(lovelace, dict):
        return lovelace.get("resources")
    return getattr(lovelace, "resources", None)


def _resources_writable(resources: Any) -> bool:
    """False for YAML resource mode, whose collection has no create/delete."""
    return hasattr(resources, "async_create_item")


async def _async_load_resources(resources: Any) -> None:
    """Load the resource collection from storage if nothing has yet.

    The collection loads lazily, and until recent cores its create/delete don't
    load it first: creating into an unloaded collection saves over the user's
    stored resources (and async_items() would miss an existing copy of ours).
    Mirrors HA's own guard.
    """
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True


async def _async_ensure_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Make the card bundle a Lovelace resource. True if it now is one.

    Why not add_extra_js_url: that injects the bundle into the page HTML, where
    it races HA's own app script. The app installs a polyfilled
    window.customElements registry as it starts (unconditionally, in at least
    the 2026.2 and 2026.10 frontends); anything defined in the native registry
    before that is invisible to HA's customElements.get(), so the dashboard
    shows "Custom element doesn't exist: wake-alarm-card" even though the
    bundle ran. Our 53 KB bundle usually wins that race. Lovelace resources are
    loaded by the dashboard itself, after the app is up, so they define into
    the right registry.

    A stored resource also survives restarts: a dashboard opened while HA is
    still starting (before this integration has set up) still gets the URL, and
    the browser serves the versioned bundle from its HTTP cache.

    YAML resource mode is read-only: True only if the user already lists our
    bundle there.
    """
    resources = _lovelace_resources(hass)
    if resources is None:
        return False
    try:
        if not _resources_writable(resources):
            if any(_is_card_resource(item) for item in resources.async_items() or []):
                return True
            _LOGGER.warning(
                "Lovelace resources are in YAML mode, so wake-alarm-card can't "
                "add itself; it may show as \"Custom element doesn't exist\". "
                "Add this to your Lovelace resources: url: %s, type: module",
                url,
            )
            return False
        await _async_load_resources(resources)
        ours = [item for item in resources.async_items() if _is_card_resource(item)]
        if not ours:
            await resources.async_create_item({"res_type": "module", "url": url})
            return True
        first, *duplicates = ours
        if first.get("url") != url or first.get("type") != "module":
            await resources.async_update_item(
                first["id"], {"res_type": "module", "url": url}
            )
        # A second URL for the bundle evaluates it twice; the second copy's
        # define() then throws.
        for item in duplicates:
            await resources.async_delete_item(item["id"])
    except Exception:  # the caller falls back to add_extra_js_url
        _LOGGER.warning(
            "could not register wake-alarm-card as a Lovelace resource",
            exc_info=True,
        )
        return False
    return True
