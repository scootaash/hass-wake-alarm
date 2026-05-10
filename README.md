# hass-wake-alarm

Sunrise wake-up alarms for Home Assistant. Lights ramp up before alarm
time, music fades in at alarm time. Multi-instance, multi-room, custom
Lovelace card included.

## Install

1. HACS → ⋮ → Custom repositories → add `https://github.com/scootaash/hass-wake-alarm` with category **Integration**.
2. HACS → Wake Alarm → Download.
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → search "Wake Alarm".

The card ships **inside the integration** and registers itself as a
Lovelace resource at `/wake_alarm/wake-alarm-card.js`. There's no
separate HACS Dashboard install or manual `Settings → Dashboards →
Resources` step.

## Default card

```yaml
type: custom:wake-alarm-card
entity: switch.<your_slug>_enabled
```

Pass any wake_alarm enabled-switch as `entity` and the card derives
every related entity from the same config entry.

## Building your own dashboard

Each alarm instance creates a fixed set of entities scoped by `<slug>`,
all of which can be used in any standard HA card (entities, gauges,
buttons, conditional cards, automations…). Replace `<slug>` with the
slug HA derived from your alarm name (e.g. `master_bedroom`).

### Switches

- `switch.<slug>_enabled` — master enable; toggle to arm/disarm
- `switch.<slug>_mon` … `switch.<slug>_sun` — day-of-week toggles

### Time + numbers (all writable via UI)

- `time.<slug>_alarm_time`
- `number.<slug>_length_min` (1–120)
- `number.<slug>_start_kelvin` (1500–6500)
- `number.<slug>_target_kelvin` (1500–6500)
- `number.<slug>_max_brightness_pct` (1–100)
- `number.<slug>_volume` (0.0–1.0)
- `number.<slug>_snooze_min` (1–30)
- `number.<slug>_steps_per_min` (5–60)
- `number.<slug>_music_fade_sec` (0–300)
- `number.<slug>_auto_dismiss_min` (0–120, 0 disables)

### Action buttons

Press via `button.press` service or tap in the UI:

- `button.<slug>_test_light_ramp`
- `button.<slug>_test_music`
- `button.<slug>_cancel_ramp`
- `button.<slug>_dismiss`
- `button.<slug>_snooze`

### Status

- `sensor.<slug>_next_alarm` — timestamp of the next scheduled fire.
  Attributes: `light_entities`, `media_player_entities`, `person_entity`.
- `sensor.<slug>_state` — enum: `idle` / `ramping` / `playing` / `snoozing`.
  When `snoozing`, attribute `snooze_until` is the ISO timestamp the
  music will resume.
- `sensor.<slug>_media_selection` — friendly title of the picked media,
  or `none`. Attributes: `media_content_id`, `media_content_type`,
  `thumbnail`.
- `binary_sensor.<slug>_active` — on whenever a sequence is running
  (any state other than `idle`).

### Services

- `wake_alarm.snooze` (target = any wake_alarm entity)
- `wake_alarm.dismiss`
- `wake_alarm.cancel_ramp`
- `wake_alarm.test_light_ramp`
- `wake_alarm.test_music`
- `wake_alarm.set_media` — persists the picked media for an alarm; called
  by the card after the user picks via the media browser. Fields:
  `media_content_id`, `media_content_type`, `title`, `thumbnail`.

### Example automation

```yaml
alias: Lights off when alarm dismissed
trigger:
  - platform: state
    entity_id: sensor.master_bedroom_state
    from: playing
    to: idle
action:
  - service: light.turn_off
    target:
      entity_id: light.bedroom
```
