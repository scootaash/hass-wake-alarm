# hass-wake-alarm

Sunrise wake-up alarms for Home Assistant. Lights ramp up before alarm
time, music fades in at alarm time. Multi-instance, multi-room, custom
Lovelace card included.

**Tested with:** Philips Hue lights, Sonos speakers, and the iOS
Companion app. Not tested on Android or with other light / media-player
integrations — should work everywhere HA supports the underlying
`light.turn_on` and `media_player.play_media` services, but YMMV.

## Install

1. HACS → ⋮ → Custom repositories → add `https://github.com/scootaash/hass-wake-alarm` with category **Integration**.
2. HACS → Wake Alarm → Download.
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → search "Wake Alarm".
5. Set up the instance with the wizard to select which media player and lights are used. If desired add notification and presence
6. Add the card and select a playlist. Adjust other settings if desired

The card ships **inside the integration** and registers itself as a
Lovelace resource at `/wake_alarm/wake-alarm-card.js`. There's no
separate HACS Dashboard install or manual `Settings → Dashboards →
Resources` step.



## Default card

```yaml
type: custom:wake-alarm-card
entity: switch.my_alarm_enabled
```

Pass any wake_alarm enabled-switch as `entity` and the card derives
every related entity from the same config entry.

## Alarm Card options
<img width="655" height="561" alt="image" src="https://github.com/user-attachments/assets/4f0224a6-de5a-4801-aee0-00f3b178eaa4" />

The card shows a large off/on button, a time select with rocker switches to select the time and days of the week switches to control which days the alarm will sound. 

<img width="485" height="1036" alt="image" src="https://github.com/user-attachments/assets/4d2977df-3574-45c2-b328-6b4b7845b8d3" />

Clicking the cog takes you to the setup page to adjust:
1. Settings for the alarm logic
2. Run test patterns
3. Select a media source
4. Shows targets set in setup wizard

## Building your own dashboard

Every example below assumes you named your alarm **My Alarm** at setup,
which gives a slug of `my_alarm`. Replace `my_alarm` with whatever slug
HA derived from your instance name.

Each alarm instance creates a fixed set of entities all of which can be
used in any standard HA card (entities, gauges, buttons, conditional
cards, automations…).

### Switches

- `switch.my_alarm_enabled` — master enable; toggle to arm/disarm
- `switch.my_alarm_d1_mon` … `switch.my_alarm_d7_sun` — day-of-week toggles
  (the `dN_` prefix gives calendar order in HA's device card)

### Time + numbers (all writable via UI)

- `time.my_alarm_alarm_time`
- `number.my_alarm_length_min` (1–120)
- `number.my_alarm_start_kelvin` (1500–6500)
- `number.my_alarm_target_kelvin` (1500–6500)
- `number.my_alarm_max_brightness_pct` (1–100)
- `number.my_alarm_volume` (0.0–1.0)
- `number.my_alarm_snooze_min` (1–30)
- `number.my_alarm_steps_per_min` (5–60)
- `number.my_alarm_music_fade_sec` (0–300)
- `number.my_alarm_auto_dismiss_min` (0–120, 0 disables)

### Action buttons

Press via `button.press` service or tap in the UI:

- `button.my_alarm_test_light_ramp`
- `button.my_alarm_test_music`
- `button.my_alarm_test_standard_notification`
- `button.my_alarm_test_urgent_notification`
- `button.my_alarm_cancel_ramp`
- `button.my_alarm_dismiss`
- `button.my_alarm_snooze`

### Status

- `sensor.my_alarm_next_alarm` — timestamp of the next scheduled fire.
  Attributes: `light_entities`, `media_player_entities`, `person_entity`.
- `sensor.my_alarm_state` — enum: `idle` / `ramping` / `playing` / `snoozing`.
  When `snoozing`, attribute `snooze_until` is the ISO timestamp the
  music will resume.
- `sensor.my_alarm_media_selection` — friendly title of the picked media,
  or `none`. Attributes: `media_content_id`, `media_content_type`,
  `thumbnail`.
- `binary_sensor.my_alarm_active` — on whenever a sequence is running
  (any state other than `idle`).

### Services

- `wake_alarm.snooze` (target = any wake_alarm entity)
- `wake_alarm.dismiss`
- `wake_alarm.cancel_ramp`
- `wake_alarm.test_light_ramp`
- `wake_alarm.test_music`
- `wake_alarm.test_standard_notification`
- `wake_alarm.test_urgent_notification`
- `wake_alarm.set_media` — persists the picked media for an alarm; called
  by the card after the user picks via the media browser. Fields:
  `media_content_id`, `media_content_type`, `title`, `thumbnail`.

### Example automation

Auto-dismiss the alarm if you leave home while it's still running
(useful if you snoozed and walked out):

```yaml
alias: "Wake Alarm: dismiss if I leave home while it's running"
trigger:
  - platform: state
    entity_id: person.me
    to: not_home
condition:
  - condition: state
    entity_id: binary_sensor.my_alarm_active
    state: "on"
action:
  - service: wake_alarm.dismiss
    target:
      entity_id: switch.my_alarm_enabled
```
