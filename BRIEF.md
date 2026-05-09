# Wake Alarm: Home Assistant Integration

## Overview

A productised, multi-instance wake-up alarm system for Home Assistant, evolved from an existing YAML package. Distributed via HACS as both a Python custom integration and a TypeScript Lovelace card from a single GitHub repository.

The system gradually brightens configured lights from a warm low-Kelvin start to a cool high-Kelvin target over a configurable duration, ending at the alarm time. At alarm time it plays a configured media source on configured speakers, fading volume from 0 to a target level. The integration is designed to be light-platform-agnostic and media-player-agnostic, with multi-room playback supported only on platforms that natively support synchronised group playback (`MediaPlayerEntityFeature.GROUPING`).

## Repository Structure

```
wake-alarm/
  custom_components/
    wake_alarm/
      __init__.py
      manifest.json
      const.py
      coordinator.py
      config_flow.py
      time.py
      switch.py
      number.py
      button.py
      sensor.py
      binary_sensor.py
      services.py
      services.yaml
      strings.json
      translations/en.json
  card/
    src/
      wake-alarm-card.ts
      main-view.ts
      settings-view.ts
      editor.ts
      styles.ts
    package.json
    rollup.config.js
    tsconfig.json
    README.md
  www/
    wake-alarm-card.js          # Built bundle, committed for HACS frontend distribution
  tests/
    integration/
    card/
  docs/
    install.md
    config.md
    legacy_yaml_reference.yaml  # Existing YAML, kept as algorithmic reference
    examples/
  hacs.json
  README.md
  LICENSE
  CHANGELOG.md
```

The repo serves both HACS categories. Users add the URL twice in HACS: once under "Integrations", once under "Frontend".

## Reference Implementation

The existing YAML package (provided as `docs/legacy_yaml_reference.yaml`) is the algorithmic source of truth for:

- Stepped light ramp math (20 steps per minute, brightness and Kelvin interpolation, current-state clamp to prevent dimming)
- Sonos sequence quirks (UPnP 800 mitigation via 3-second post-unjoin delay, volume-clamping before and after `play_media` because favourites can restore their own volume, 5-second post-play delay before fade)
- Linear volume fade from 0 to target over a configurable duration

Read the YAML before implementing those subsystems. Port the logic to async Python, do not reinvent.

## Custom Integration

### Domain and identity

- Domain: `wake_alarm`
- Manifest: declares `config_flow: true`, `iot_class: "local_push"`, optional `mobile_app` integration dependency for notifications
- Initial version: 0.1.0 (SemVer)

### Multi-instance model

Each alarm is a config entry. Users add the integration multiple times in Settings → Devices & Services for different alarms (weekday vs weekend, multiple bedrooms, etc.). Each config entry creates its own set of entities scoped by a slug derived from the user-provided name.

### Config entry contents

Stored in `config_entry.data` (changed only via Options Flow):

- `name`: user-friendly name for this alarm instance
- `slug`: derived from name, used in entity IDs
- `light_entities`: list of `light.*` entity IDs (one or more)
- `media_player_entities`: list of `media_player.*` entity IDs (one or more if all support GROUPING and share the same source integration)
- `media_content_id`: string for `media_player.play_media`
- `media_content_type`: string for `media_player.play_media` (e.g. `favorite_item_id` for Sonos with value like `FV:2/5`, `playlist`, `music`, `url`)
- `person_entity`: optional `person.*` entity ID for presence guard
- `notify_target_standard`: optional `notify.*` service for the standard alarm notification
- `notify_target_urgent`: optional `notify.*` service for the player-unavailable fallback notification

Runtime-tweakable settings live as entities (see below) with state restored across HA restarts via `RestoreEntity`.

### Config flow

Setup wizard steps:

1. **Name**: text input for a friendly name (e.g. "Master Bedroom Weekdays"). Slug auto-generated from this.
2. **Lights**: multi-select entity selector filtered to `light` domain.
3. **Media players**: multi-select entity selector filtered to `media_player` domain. Validation: if more than one is selected, all must originate from the same integration AND advertise `MediaPlayerEntityFeature.GROUPING`. Reject with a clear error otherwise, naming the incompatible players.
4. **Media content**: text input for `media_content_id` plus dropdown for `media_content_type`. Help text covers common values: Sonos `favorite_item_id` (`FV:2/5` format), Spotify `spotify:playlist:...`, generic stream `url`.
5. **Person presence (optional)**: entity selector filtered to `person` domain. Blank skips the presence check entirely.
6. **Notification targets (optional)**: two `notify.*` service dropdowns (standard, urgent). Can be the same service.
7. **Confirm**: summary of choices.

The Options Flow re-runs the same steps for editing existing instances.

### Entities created per config entry

All entity IDs follow the pattern `<platform>.<slug>_<purpose>`. Entity friendly names use the user-provided instance name as a prefix.

**Configuration entities (user-tweakable, persistent state):**

| Entity | Range | Default | Notes |
|---|---|---|---|
| `switch.<slug>_enabled` | bool | off at create | Master enable for this alarm |
| `switch.<slug>_mon` to `_sun` | bool | weekdays on | Day-of-week toggles |
| `time.<slug>_alarm_time` | time-of-day | 07:00 | HA `time` platform |
| `number.<slug>_length_min` | 1 to 120, step 1 | 15 | Ramp length in minutes |
| `number.<slug>_start_kelvin` | 1500 to 6500, step 50 | 1500 | Ramp start colour temperature |
| `number.<slug>_target_kelvin` | 1500 to 6500, step 50 | 4500 | Ramp target colour temperature |
| `number.<slug>_max_brightness_pct` | 1 to 100, step 1 | 35 | Target peak brightness |
| `number.<slug>_volume` | 0.0 to 1.0, step 0.01 | 0.08 | Target audio volume (default cap 0.2 to prevent accidents) |
| `number.<slug>_snooze_min` | 1 to 30, step 1 | 4 | Snooze duration |
| `number.<slug>_steps_per_min` | 5 to 60, step 1 | 20 | Light ramp granularity |
| `number.<slug>_music_fade_sec` | 0 to 300, step 5 | 60 | Volume fade duration after play starts |
| `number.<slug>_auto_dismiss_min` | 0 to 120, step 1 | 0 | Auto-dismiss timeout (0 disables) |

**Action entities (buttons):**

- `button.<slug>_test_light_ramp`: runs an unscheduled light ramp using current settings
- `button.<slug>_test_music`: runs the music sequence using current settings
- `button.<slug>_dismiss`: full dismiss
- `button.<slug>_snooze`: snooze trigger
- `button.<slug>_cancel_ramp`: stops the light ramp without dismissing the alarm

**Status entities:**

- `sensor.<slug>_next_alarm`: next scheduled alarm time (timestamp `device_class`)
- `sensor.<slug>_state`: enum string, one of `idle`, `ramping`, `playing`, `snoozing`
- `binary_sensor.<slug>_active`: true while a sequence is running (any state other than `idle`)

### Coordinator and trigger logic

A single `WakeAlarmCoordinator` per config entry, owning the state machine and scheduling. Subclasses `DataUpdateCoordinator` only loosely; this is event-driven, not polled.

**State machine:**

- `idle`: waiting for next scheduled fire
- `ramping`: light ramp in progress (between alarm_time minus length, and alarm_time)
- `playing`: music sequence active (after alarm_time)
- `snoozing`: snooze timer running, awaiting replay

**Scheduling:** the coordinator computes the next fire time from `time.<slug>_alarm_time`, the day switches, and current local time. Uses `async_track_point_in_time(hass, callback, ramp_start_dt)` where `ramp_start_dt = alarm_time - length`. Recomputes whenever any of those entities change state. **No minute-pattern polling** (replaces the existing YAML's `time_pattern` triggers).

**On fire:**

1. Check `switch.<slug>_enabled`. If off, abort silently.
2. Check person presence if configured. If person not home, abort silently and recompute next fire.
3. Transition state to `ramping`. Start the light ramp task.
4. Schedule music start at `alarm_time` via another `async_track_point_in_time`.
5. At alarm_time: check media_player availability. If any required player is unavailable, send the urgent notification and skip music. Lights continue ramping to completion, then transition to `idle`. If players are available, transition to `playing`, start the music sequence, and send the standard notification.
6. After `auto_dismiss_min` minutes (if configured > 0): trigger dismiss automatically.

### Light ramp algorithm

Stepped, default 20 steps per minute. Total steps = `length_min × steps_per_min`. Per step:

1. Compute target brightness percent linearly from 1% to `max_brightness_pct`
2. Compute target Kelvin linearly from `start_kelvin` to `target_kelvin`
3. Read each light's current brightness; clamp the next-step brightness to never dim below current (preserves user override behaviour from the YAML)
4. Issue `light.turn_on` with `brightness_pct` and `color_temp_kelvin` for all configured lights in a single call

Initial state: lights set to 1% brightness at `start_kelvin` at ramp start. Lights that are off at ramp start are turned on.

**User override detection:** every `light.turn_on` call uses a fresh `Context` object created by the integration. The coordinator subscribes to `state_changed` events for the configured lights. When a state change fires with a `context.id` not in the integration's recently-issued context set (sliding window of last 50 contexts, max age 60 seconds), treat it as a user override. End the ramp immediately and transition through to either `playing` (if alarm time passed) or `idle`. Music is unaffected.

### Music sequence algorithm

Two paths.

**Single player, or multi-player non-Sonos / non-grouping (config flow blocks the latter, but defensive):**

1. Set volume to 0 on the player(s).
2. `media_player.play_media` with configured `media_content_id` and `media_content_type`.
3. Linearly fade volume from 0 to `target_volume` over `music_fade_sec` seconds in 20 steps.

**Multi-player Sonos or other GROUPING-capable:**

1. Designate the first selected player as group coordinator.
2. `media_player.unjoin` on the coordinator (clears any existing group state).
3. Wait 3 seconds (Sonos UPnP 800 mitigation, ported from existing YAML).
4. Set volume to 0 on the coordinator.
5. `media_player.join` with `group_members` = the other selected players.
6. Wait 1 second for the group to form.
7. Set volume to 0 on each member individually (join does not propagate volume).
8. Enable shuffle if applicable: `media_player.shuffle_set` true.
9. `media_player.play_media` on the coordinator.
10. Wait 5 seconds for queue to start.
11. Linearly fade volume from 0 to `target_volume` across all group members synchronously.

**Sonos quirks ported from existing YAML:**

- Pre-set volume to 0 *before* and *after* the `play_media` call (favourites can restore their own volume)
- 3-second delay after unjoin before next operation
- 5-second delay after `play_media` before starting the volume fade

### Snooze flow

1. Pause music on the active player or group (`media_player.media_pause`)
2. Cancel any pending music ramp task
3. Start an internal snooze timer for `snooze_min` minutes
4. Transition to `snoozing` state
5. Lights untouched
6. On timer fire: re-run the music sequence (skip group join if group already formed), transition back to `playing`

### Dismiss flow

1. Stop music on all configured players (`media_player.media_stop`)
2. Unjoin any group formed
3. Cancel any pending ramp, snooze, or auto-dismiss task
4. Lights left as the user has them (no override)
5. Transition to `idle`
6. Compute next scheduled fire time

### Mobile notifications

**Standard alarm notification** (sent at alarm_time, only if `notify_target_standard` configured):

- Service: configured `notify.*` target
- Title: instance name, e.g. "Master Bedroom Alarm"
- Message: "Alarm playing. Snooze or Dismiss."
- Actions: snooze (calls `wake_alarm.snooze` with this entity_id), dismiss (calls `wake_alarm.dismiss`)
- Priority: normal
- iOS: default interruption-level
- Android: notification channel `wake_alarm_standard`, importance DEFAULT

**Urgent fallback notification** (sent if any required media_player is unavailable at alarm_time, only if `notify_target_urgent` configured):

- Service: configured `notify.*` target (can be the same as standard)
- Title: "Alarm: speaker unavailable"
- Message: "Lights are on but {player_name} couldn't play. Wake up."
- Actions: snooze, dismiss
- iOS: `push.sound.critical: 1`, `push.interruption-level: critical`
- Android: notification channel `wake_alarm_urgent`, importance HIGH, separate from standard so the user can configure a custom sound for it in the Companion app's channel settings

The two notifications use distinct iOS interruption-levels and distinct Android channels precisely so users can configure custom sounds per channel.

### Services

All accept a `target` (entity_id of any of the integration's button entities, used to identify the config entry):

- `wake_alarm.dismiss`: full dismiss
- `wake_alarm.snooze`: snooze (uses configured `snooze_min`)
- `wake_alarm.cancel_ramp`: stop light ramp without dismissing
- `wake_alarm.test_light_ramp`: run ramp now (test)
- `wake_alarm.test_music`: run music sequence now (test)

### Person presence behaviour

- If `person_entity` configured and not `home` at the moment the coordinator would transition to `ramping`: log info, skip the entire sequence, recompute next fire. No notification sent.
- If `person_entity` not configured: no check applied, alarm always fires.

This is **applied consistently to the whole sequence**, unlike the existing YAML which only checks on the pre-phase.

### Mid-cycle disable

If `switch.<slug>_enabled` flips to off while in any non-idle state, the coordinator triggers a full dismiss.

### Restart behaviour

Use `RestoreEntity` for state-bearing entities to preserve user-tweaked values. For the state machine: regardless of restored state, transition to `idle` on startup and recompute next fire time. Don't attempt to resume an interrupted ramp or music; clean slate is safer.

## Custom Lovelace Card

### Distribution

TypeScript source in `card/src/`, built with rollup to a single `wake-alarm-card.js` bundle, committed to `www/wake-alarm-card.js` for HACS frontend distribution.

`hacs.json` declares:

```json
{
  "name": "Wake Alarm",
  "filename": "wake-alarm-card.js",
  "render_readme": true
}
```

### Card configuration

Lovelace YAML:

```yaml
type: custom:wake-alarm-card
entity: switch.master_bedroom_enabled
```

The card derives all related entities from the config entry that owns the provided `entity`. Internally queries the entity registry (via the HA WebSocket API `config/entity_registry/list`) and filters by `config_entry_id`.

### Main view (default)

Mirrors the first attached screenshot. Components:

- Header: instance name, settings cog icon (navigates to settings view), close-X icon (dismisses popup if used in popup mode)
- Alarm Mode indicator: current state derived from `switch.<slug>_enabled` and `sensor.<slug>_state`. Tap toggles enabled.
- Time picker: hour and minute with up/down arrow buttons (matches existing design). Updates `time.<slug>_alarm_time`.
- Day-of-week chips: 7 chips Mon to Sun, tap to toggle each `switch.<slug>_<day>`. Visual checkmark when on, cross when off.
- Snooze button: visible only when `binary_sensor.<slug>_active` is on. Calls `button.<slug>_snooze`.
- Dismiss button: visible only when `binary_sensor.<slug>_active` is on. Calls `button.<slug>_dismiss`.

### Settings view (cog navigation)

Mirrors the second and third attached screenshots:

- Snooze (min) slider: bound to `number.<slug>_snooze_min`
- Test Light Ramp button: calls `button.<slug>_test_light_ramp`
- Length (min) slider: `number.<slug>_length_min`
- Start K slider: `number.<slug>_start_kelvin`
- Target K slider: `number.<slug>_target_kelvin`
- Max % Brightness slider: `number.<slug>_max_brightness_pct`
- Cancel Ramp button: visible only when `sensor.<slug>_state == "ramping"`. Calls `button.<slug>_cancel_ramp`.
- Test Music button: calls `button.<slug>_test_music`
- Alarm Volume (0-1) slider: `number.<slug>_volume`
- Targets & Audio section: read-only display of person, lights, media players, media_content_id, media_content_type, with an "Edit" link that opens the Options Flow (deep-link to Settings → Devices & Services → this config entry → Configure)

### Card editor

Visual config UI for adding the card via Lovelace's "Edit Card" → "Visual Editor". Single field:

- Entity: dropdown of `switch.*_enabled` entities owned by the wake_alarm integration

### Build and packaging

- TypeScript with strict mode
- Lit (HA's standard custom element framework)
- Rollup with terser plugin
- Output: ES module bundle at `www/wake-alarm-card.js`
- npm scripts: `build`, `build:watch`, `lint`, `test`
- GitHub Actions: build the bundle on tag push, attach to the GitHub release

## Migration from existing YAML package

No automated migration. Document manual migration in `docs/install.md`:

1. Install the integration via HACS (custom repository as Integration)
2. Install the card via HACS (same repository as Frontend)
3. Restart Home Assistant
4. Add an alarm via Settings → Devices & Services → Add Integration → Wake Alarm
5. Configure with the same entity IDs the YAML package referenced
6. Replace existing dashboard cards with `type: custom:wake-alarm-card`
7. Remove `packages/wake_alarm.yaml` from the user's `configuration.yaml`
8. Optionally remove the `input_select.alarm_mode` UI helper

## Testing requirements

### Integration tests (pytest, HA's test framework)

- Coordinator schedules correctly across day boundaries (DST transitions explicitly tested)
- Day-of-week filtering works for all combinations including all-off (no fire)
- Person presence guard skips when not home, fires when home, ignored when unset
- Light ramp produces correct brightness and Kelvin curves at given step counts
- User override detection ends ramp on external context state change but not on integration-issued ones
- Music sequence handles single player correctly
- Music sequence handles multi-Sonos group: unjoin, delay, join, volume zero, shuffle, play, fade
- Music sequence skips music when player unavailable, sends urgent notification, lights continue
- Mobile notifications dispatched correctly per scenario, with correct payload shape per platform
- Mid-cycle disable triggers dismiss
- Auto-dismiss timeout fires correctly at configured offset
- Restart resets state to idle cleanly even mid-sequence
- Config flow validates player grouping compatibility correctly (rejects mixed-platform multi-select)
- Options flow updates config entry data without losing user-tweaked entity state

### Card tests

- Renders main view with sample state for each state machine value
- Renders settings view with sample state
- Day chips toggle correctly via service calls
- Time picker updates time entity correctly
- Sliders dispatch number entity service calls
- Editor produces valid card config
- Tests run in jsdom or Playwright

## v2 backlog (out of scope for v1)

- One-off override boolean (auto-disables `switch.enabled` after firing)
- Skip-next-occurrence button (suppresses one upcoming fire only)
- Calendar-aware skip (skip on bank holidays, on calendar "off" entries)
- Voice Assist intents ("snooze ten minutes", "stop alarm")
- TTS announcements (good morning, weather, calendar preview)
- Weather-aware ramp adjustments
- Custom post-alarm light state on dismiss
- Per-day separate alarm times within one instance
- Alarm history/log entity for "last fired", "last snoozed", "last dismissed"
- Random track-skip on Sonos start (currently dead code in the existing YAML)

## References

- HA developer manifest: https://developers.home-assistant.io/docs/creating_integration_manifest
- Config flow: https://developers.home-assistant.io/docs/config_entries_index
- Coordinator pattern: https://developers.home-assistant.io/docs/integration_fetching_data
- Time entity: https://developers.home-assistant.io/docs/core/entity/time
- Number entity: https://developers.home-assistant.io/docs/core/entity/number
- Switch entity: https://developers.home-assistant.io/docs/core/entity/switch
- Button entity: https://developers.home-assistant.io/docs/core/entity/button
- HACS publishing: https://hacs.xyz/docs/publish/start
- HA Companion critical notifications: https://companion.home-assistant.io/docs/notifications/critical-notifications
- Custom card development: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card
- Lit element framework: https://lit.dev/docs/

## Implementation order suggestion

1. Scaffold integration: manifest, `__init__.py`, `const.py`, basic config flow, single config entry creating a `switch.enabled` entity. Verify install via HACS.
2. Add all configuration entities (time, switches, numbers). Verify state persists across restarts.
3. Implement the coordinator and scheduling. Verify `sensor.next_alarm` updates correctly across changes to time and day switches.
4. Implement the light ramp algorithm with context-tracking override detection. Test via the test_light_ramp button.
5. Implement the music sequence. Test single-player path, then multi-Sonos path. Test via the test_music button.
6. Implement snooze, dismiss, cancel_ramp.
7. Implement mobile notifications (standard and urgent).
8. Add status entities and binary_sensor.
9. Write integration tests.
10. Scaffold the card project. Implement main view first, then settings view, then editor.
11. Write card tests.
12. Documentation pass: README, install.md, config.md.
13. Tag 0.1.0 release.
