# Changelog

All notable changes to this project will be documented here.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## 0.5.0 — 2026-06-18

Feature release: lights and media players are now independent (silent or
music-only alarms), with new condition and script gates, plus a substantial
round of state-machine and lifecycle hardening driven by a deep review.

### Added

- **Media player is optional — lights-only or music-only alarms (#22).** Lights
  and media players are each individually optional; pick at least one. With no
  media player the alarm runs the light ramp and sends the standard
  notification at alarm time (the "speaker unavailable" / "no media" urgent
  notices are suppressed) and settles — snooze and auto-dismiss are music-only
  and aren't armed.
- **Condition-sensor gate (#23).** An optional `binary_sensor` gates the cycle
  on an on/off state (bed sensor, Workday sensor, etc.). Works like presence —
  checked twice, at ramp-start and again at `alarm_time` — and is ANDed with
  presence when both are set.
- **Before / after script hooks (#24).** Two optional `script.*` targets run at
  the start and end of the cycle (ramp-start or alarm time, and music end /
  dismiss / auto-dismiss; not on snooze). Both fire non-blocking so a slow or
  failing script can never delay the wake-up, and receive the instance `slug`
  and `name` as variables.
- **Restart catch-up.** If Home Assistant is down across `alarm_time` but boots
  back within `CATCHUP_GRACE_MIN` minutes (default 15), the alarm fires
  immediately on startup so the user is still woken (music only; the light ramp
  is not replayed). Beyond the window the schedule simply rolls forward.

### Changed

- **Music is now scheduled independently of the light ramp.** The coordinator
  arms two separate timers — a light-ramp timer at `alarm_time − length` and an
  authoritative alarm/music timer at `alarm_time` — instead of arming music
  from inside the ramp callback. A failure anywhere in the light phase (the
  callback never running, an exception, no lights configured, presence failing
  at ramp-start, or a restart inside the ramp window) can no longer prevent the
  alarm from sounding. The music — the safety-critical feature — always fires
  on its own timer.
- **Presence is re-checked at alarm time.** Presence now gates the two phases
  independently: at ramp-start for the lights, and again (freshly) at
  `alarm_time` for the music. Someone out when the ramp would start but home by
  the alarm time is still woken; someone who leaves in between gets the lights
  but no music.
- **The card hides music-only controls for a lights-only alarm (#46).** The
  media picker, "Test music", and "Test urgent notification" controls are
  hidden when no media player is configured, since they'd be no-ops.
- **A player failing mid-sequence no longer aborts the alarm (#45).** Music
  service calls are routed through a guard that logs and continues, so a single
  speaker dropping out (or a half-formed group) can't take the rest of the
  wake-up down with it.

### Fixed

- **Unload/reload teardown race (#48).** A cancelled music task's completion
  handler ran during `async_unload` while still PLAYING, which (with a deferred
  recompute pending) re-armed the schedule timers after teardown had cancelled
  them and fired the after-script on unload/reload. Teardown now marks itself
  and makes the recompute / script paths inert.
- **Snooze during the ramp resumed ungrouped (#48).** Snoozing before any music
  played resumed via the snooze fast-path and skipped the Sonos group-join, so
  a multi-room alarm came back ungrouped. It now does a full music start unless
  music was actually playing when the snooze began.
- **Card stuck on a transient resolve error (#48).** A card that rendered before
  the integration finished registering its entities stuck on the error until a
  dashboard reload; it now retries (bounded) on later updates.
- **Mid-occurrence interference (#43, #44).** A settings change while the alarm
  is firing is deferred to the next idle settle so it can't arm a second fire
  the same day, and the test buttons are refused during the ramp→alarm gap so
  they can't silence the real alarm.
- **Auto-dismiss now fires during a snooze (#38)** so a long snooze can't let
  the alarm outlive the configured auto-dismiss window; background tasks are
  tracked and cancelled on unload (#35).
- **Stranded alarm cycle when disabled during the ramp→alarm gap (#34)** — the
  occurrence is now closed out so the next day's before-script still runs.
- **DST gap / fall-back alarm-time semantics pinned (#36).** Alarms on the far
  side of a transition fire at the intended wall-clock time; gap/overlap times
  resolve to a single deterministic instant.
- **Card registration hardening (#19, #20, #37).** The cache-bust version is
  read off the event loop (no blocking `open()`), the static route is claimed
  before the await so concurrent entry setups can't double-register it, and the
  bundle `is_file()` check runs in the executor. Broken Music Assistant artwork
  in the media picker is fixed by signing HA proxy URLs.
- **Ramp restarting from zero at alarm time.** When the light ramp finished a
  few seconds before the alarm/music time, the coordinator returned to IDLE and
  recomputed the schedule, re-selecting the still-future alarm for the same day
  (whose ramp-start was already in the past) and re-firing immediately — e.g. a
  06:00 / 30-min alarm ramped 05:30→05:59, then again 05:59→06:29. Fixed
  structurally: the schedule now rolls forward only when the alarm timer fires
  (`now >= alarm_time`, so the next-occurrence computation can never re-select
  today), and the IDLE transition no longer recomputes.

### Migration

Config entry version bumps from `2` to `4` (v2→v3 added the condition gate,
v3→v4 added the script hooks). Both steps are additive no-ops — no stored data
changes and nothing to re-toggle. Existing lights/media/presence/notification
settings and media selections are preserved.

### Tests / CI

- HA-backed coordinator tests driving a real coordinator with a frozen clock,
  plus `config_flow` and `async_migrate_entry` suites (#39, #40), coverage
  reporting, and a CI matrix across the min and latest supported HA.
- HACS + hassfest validation workflow.

## 0.4.0-beta.1 — 2026-05-13

First beta cut for the Home Assistant community-forum launch. Mostly
documentation + packaging since 0.3.0; the integration's runtime
behaviour is unchanged.

### Added

- **Brand icons** for the integration tile. HA 2026.3+ serves them via
  its built-in brands-proxy API
  (`/api/brands/integration/wake_alarm/...`) from
  `custom_components/wake_alarm/brand/`. No manifest changes, no code
  changes — HA picks them up automatically on next restart once the
  files are on disk.
- **README "How it works" section** covering the standard cycle, the
  presence guard, snooze + dismiss + cancel ramp, and both
  notification paths (standard + urgent / critical).
- **`info.md`** — short HACS-rendered intro so users get a meaningful
  first impression in the HACS Information tab.
- **Issue templates** as YAML forms with required fields and an
  HA-install-type dropdown, reducing back-and-forth on bug triage.
  Discussion and "how do I…" questions are routed to the HA community
  forum.

### Changed

- **Icon storage** collapsed to a single canonical copy under
  `custom_components/wake_alarm/brand/`. README and `info.md` image
  embeds point at the deeper path.

### Known limitations

- HACS for custom integrations doesn't yet consume HA's new
  brands-proxy API, so the integration card in HACS UI still shows the
  generic puzzle-piece icon. The README + `info.md` image embeds are
  the user-visible icon surface inside HACS until that lands upstream.

## 0.3.0 — 2026-05-11

Audit-driven cleanup pass. All changes are backwards-compatible; bumped to
0.3.0 because the volume of fixes is more than a patch warrants.

### Fixed

- **Schedule never rearmed after a natural fire.** When the alarm ran end-
  to-end (ramp completes naturally → music plays to fade-up → music
  completes), the coordinator dropped to IDLE but never called
  `async_recompute_schedule`. Result: `sensor.<slug>_next_alarm` kept
  pointing at the just-fired (past) time and no `async_track_point_in_time`
  was armed for the next day until the user poked a dependency. Same root
  cause covered the early-return branches of `_async_on_music_start`
  (player unavailable / no media). `_set_state(STATE_IDLE)` now triggers
  the recompute on every transition into IDLE, regardless of how IDLE was
  reached.
- **Auto-dismiss timer was re-armed on every snooze resume.** Each cycle
  restarted the timer at `auto_dismiss_min` from the resume moment, so
  three snoozes effectively extended auto-dismiss by `3 × snooze_min`.
  The deadline is now captured at the first PLAYING transition and
  preserved across snooze cycles — N minutes after the alarm originally
  fired always means N minutes.
- **Tapping the mode tile during snooze disarmed the alarm.** The tile
  showed `Music in M:SS` and tapping disabled `switch.<slug>_enabled`.
  Mode-tile tap is now a no-op while the alarm is active (ramping,
  playing, or snoozing); Snooze / Dismiss / Cancel ramp are the explicit
  controls.
- **Card instance-name was locale-fragile** — it parsed the enabled-
  switch's `friendly_name` and stripped a literal "Enabled" suffix, which
  only works in English. `sensor.<slug>_next_alarm` now carries the
  user-given instance name as an `instance_name` attribute and the card
  reads it from there.
- **`parse_action_id` accepted empty entry_ids.** `wake_alarm:snooze:` was
  parsed as `("snooze", "")`, which could never resolve to a coordinator.
  Now rejected.

### Changed

- **Multi-Sonos: random track-skip on every fire and snooze resume.**
  Sonos shuffle only reorders the queue; it doesn't pick a random
  starting track, so every alarm and every snooze used to begin on the
  same track from the configured favourite. The music sequence now
  skips 1–4 tracks forward (`media_next_track`, random per fire) after
  the 5-second queue settle and before the fade, so the wake-up song
  is genuinely different each cycle. Single-player path is unchanged
  (it doesn't shuffle in the first place; can revisit if needed).
- **Volume slider displays as percentage (0–100%)** instead of the raw
  0.0–1.0 fraction. The underlying `number.<slug>_volume` entity still
  stores 0.0–1.0; the card does the multiply/divide.
- **Cancel-ramp button visible on the main view during ramping** — used
  to be settings-only. Snooze / Dismiss are still always visible while
  active.
- **Card ticker only runs during snooze.** The 1Hz `requestUpdate` that
  drives the countdown used to run for the lifetime of every dashboard;
  it now starts when state transitions to SNOOZING and stops afterward.
- **`async_call_light_turn_on` is now properly async** (was a non-async
  def returning a coroutine — worked but read oddly).

### Docs

- `LICENSE` is now an actual MIT licence instead of an empty file.
- `BRIEF.md` day-toggle entity IDs updated to the v2 `d1_mon`..`d7_sun`
  scheme.

## 0.2.3 — 2026-05-11

### Fixed

- **Card editor's "Save" wrote the wrong entity.** `getStubConfig`
  was scanning `hass.states` for the first `switch.*_enabled` it
  found and could pick something like `switch.sonos_lounge_subwoofer_enabled`
  (the Sonos subwoofer's enabled toggle). The dropdown rendered the
  filtered wake_alarm options correctly so the user saw the right
  selection, but the underlying config still held the bad stub
  until they actively re-picked.

  `getStubConfig` is now async and consults the entity registry
  (`config/entity_registry/list` with `platform === "wake_alarm"`)
  to pick a real wake_alarm enabled-switch — no false positives from
  similarly-named entities in other integrations.

  The editor also self-heals: when it loads, if the current
  `_config.entity` isn't in the filtered wake_alarm list, it clears
  it and pushes the change back via `config-changed`, so a stale
  stub from an earlier card version can't survive into Save.

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
