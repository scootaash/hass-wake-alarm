<img src="custom_components/wake_alarm/brand/icon.png" alt="Wake Alarm" width="128" align="right" />

# Wake Alarm

Gentle sunrise wake-up alarms for Home Assistant. Lights ramp from
warm + dim to cool + bright across a configurable duration, then music
fades in at alarm time. Multi-instance, multi-room, and a custom
Lovelace card included.

## Features

- **Stepped sunrise ramp** with brightness + colour-temperature
  interpolation, defaulting to 20 steps/min. Never dims a light below
  its current brightness, so if you brighten the room mid-ramp it
  stays.
- **Music fade-in** from 0 to a configured target volume across
  `music_fade_sec`. Random track-skip so every alarm and every snooze
  starts on a different track from the favourite.
- **Multi-room playback** if your speakers advertise the
  `GROUPING` feature. Sonos tested, with the full UPnP quirks ironed
  out (unjoin → settle → join → volume-zero per member → shuffle → play).
- **Mobile notifications** with separate standard and urgent paths —
  iOS critical sound bypasses Do Not Disturb if the speaker fails to
  start.
- **Snooze, Dismiss, Cancel ramp** from the card, the mobile
  notification action buttons, or `wake_alarm.*` services.
- **Optional presence guard** — silently skip the alarm if a
  configured person isn't home.
- **Custom Lovelace card** with day-of-week toggles, time picker, and
  an in-card media browser. Single HACS install (Integration only) —
  the card ships inside the integration and auto-registers as a
  Lovelace resource.

## Quick install

1. Add this repository to HACS as a **custom repository**, category
   **Integration**.
2. Download via HACS, restart Home Assistant.
3. Settings → Devices & Services → Add Integration → Wake Alarm.
4. Add `type: custom:wake-alarm-card` to a dashboard.

See the full [README](https://github.com/scootaash/hass-wake-alarm)
for setup details, the "How it works" walkthrough, and dashboard
recipes.

## Tested with

Philips Hue + Sonos + iOS Companion app. Other light / media-player
integrations should work via the standard HA service interfaces but
haven't been validated — feedback welcome on the [Home Assistant
community forum](https://community.home-assistant.io/). Bug reports
and feature requests go on
[GitHub Issues](https://github.com/scootaash/hass-wake-alarm/issues).
