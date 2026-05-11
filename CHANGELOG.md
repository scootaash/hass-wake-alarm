# Changelog

All notable changes to this project will be documented here.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## 0.2.2 — 2026-05-11

### Fixed

- **Card couldn't be added via "Add Card"** — the visual-editor flow
  hands `setConfig` an empty stub (`entity: ""`) before the user has
  picked one, and the previous strict validator threw, leaving the
  card preview hung on a spinner. `setConfig` now accepts an empty
  entity; the card renders a "Pick a Wake Alarm enabled-switch in the
  visual editor" placeholder until the editor pushes a real value.
- **`getStubConfig` now seeds a sensible default** by scanning
  `hass.states` for the first `switch.*_enabled`, so the card preview
  is meaningful from the moment the user picks it from the card list.

## 0.2.1 — 2026-05-10

### Fixed

- **Card bundle was cached across updates.** The integration registered
  the card at a static URL without a cache-busting suffix, so browsers
  kept serving the previous bundle after an integration update. Now the
  registered frontend URL includes `?v=<integration version>`, so each
  release invalidates the cache automatically.

## 0.2.0 — 2026-05-10

### Added

- **Card UX overhaul** based on first-install feedback:
  - Snooze countdown in the mode tile (`Music in M:SS`), updated every second.
  - Larger Snooze + Dismiss action buttons — half-width each, mode-tile styling
    (blue snooze, red dismiss).
  - One-line description under every settings slider so what each value does
    is clear without referring to the docs.
- **Custom media browser**: a self-contained Lit element backed by HA's
  `media_player/browse_media` WebSocket API, replacing the previous
  `<ha-media-player-browse>` dependency that wasn't always lazy-loaded into
  dashboard contexts. Single dependency on `hass.callWS`, works on every HA
  version. Fixes the "media select doesn't work" bug.
- **Single-screen config + options wizard**: the previous six-step flow is
  collapsed into one screen with per-field help text rendered under each
  label. The options flow mirrors the same layout (without the name field —
  slugs are locked once entity IDs exist).
- **README "Building your own dashboard" section** listing every entity and
  service the integration exposes for use in custom Lovelace cards.
- **Snooze sensor attribute**: `sensor.<slug>_state` exposes `snooze_until`
  as an ISO-string attribute while snoozing, surfaced in the card's mode
  tile and available for any custom UI.
- **Test-notification buttons + services**: `button.<slug>_test_standard_notification`
  and `button.<slug>_test_urgent_notification` (plus matching
  `wake_alarm.test_*_notification` services) fire the actual standard /
  urgent payloads on demand so you can verify the iOS interruption
  level + sound and the Android channel without scheduling an alarm.
- **README**: documents `my_alarm` as the example slug, lists tested
  platforms (Hue, Sonos, iOS Companion), and includes a project-relevant
  automation example (auto-dismiss when you leave home).

### Changed

- **Day-of-week toggles renamed** to `switch.<slug>_d1_mon` …
  `switch.<slug>_d7_sun` so HA's alphabetical entity sort displays them in
  calendar order in Settings → Devices & Services. The user-facing labels
  ("Mon" through "Sun") become "Enable Mon" through "Enable Sun" so the
  intent is obvious in the device card.
- **Device-card layout**: day toggles, alarm time, and every number entity
  now declare `entity_category=CONFIG`. They cluster under a "Configuration"
  section, leaving the master enable as the only top-level control next to
  the action buttons and status sensors.

### Migration

Config entry version bumps from `1` to `2`. On first load of a v1 entry,
`async_migrate_entry` walks the entity registry and renames each day toggle's
`unique_id` and `entity_id` to the new prefixed scheme. Day-toggle on/off
state may reset to the default (Mon-Fri on, Sat/Sun off) — re-toggle once
after upgrade. All other entities, settings, and media selections are
preserved.

If your dashboards or automations reference the old `switch.<slug>_<day>`
entity IDs, update them to `switch.<slug>_d<n>_<day>` after upgrading.

## 0.1.0 — 2026-05-10

Initial release. Wake Alarm integration + Lovelace card distributed via HACS
as a single Integration install. The integration ships the bundled card and
auto-registers it as a Lovelace resource at `/wake_alarm/wake-alarm-card.js`
on first setup.

### Integration

- Multi-instance config flow (lights, media players with grouping
  validation, optional presence and notification targets).
- Stepped sunrise light ramp with user-override detection: every
  `light.turn_on` call is tagged with a tracked `Context`; an unknown
  context.id during ramping ends the ramp.
- Music sequence with two paths: single-player and multi-Sonos with the
  full UPnP-quirks preamble (unjoin → 3s → vol-zero → join → vol-zero per
  member → shuffle → play → vol-zero again → 5s → fade).
- Snooze, dismiss, cancel-ramp, auto-dismiss, mid-cycle disable.
- Mobile notifications: standard at alarm time, urgent fallback when
  speakers are unavailable or no media is picked. Action buttons (Snooze /
  Dismiss) call back via the `wake_alarm.*` services with entry-id-encoded
  action IDs.
- Media selection via the `wake_alarm.set_media` service, surfaced as
  `sensor.<slug>_media_selection`.

### Card

- Main view with state-driven mode tile, time picker, day chips, and
  snooze/dismiss buttons (visible only while a sequence is running).
- Settings view with sliders for every tweakable number, test buttons, and
  a media picker modal.
- Visual editor with a single dropdown of every wake_alarm enabled-switch.

### Tests + CI

- `pytest` suite for the algorithmic helpers (light-ramp math, scheduling,
  action-id encoding) — 27 tests.
- `vitest` suite for the card's resolver — 6 tests.
- GitHub Actions running both suites + a card type-check + bundle-staleness
  check on every push and PR.
