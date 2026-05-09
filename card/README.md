# Wake Alarm card

TypeScript Lovelace card for the [Wake Alarm](../) Home Assistant integration.

The built bundle lives at `../www/wake-alarm-card.js` and is committed to
the repo for HACS frontend distribution.

## Usage

```yaml
type: custom:wake-alarm-card
entity: switch.master_bedroom_enabled
```

The `entity` is the master enable switch for any wake_alarm instance. The
card derives every related entity (day toggles, sliders, buttons, sensors)
from the same config entry, so you don't have to list them.

## Local development

```bash
cd card
npm install
npm run build         # one-shot bundle to ../www/wake-alarm-card.js
npm run build:watch   # rebuild on save
npm run lint          # type-check via tsc --noEmit
```

After building, copy `www/wake-alarm-card.js` into your Home Assistant
`/config/www/` directory (or symlink) and add it as a Lovelace resource:

```yaml
resources:
  - url: /local/wake-alarm-card.js
    type: module
```

## Architecture

- `src/wake-alarm-card.ts` — top-level custom element. Resolves related
  entities from the registry, switches between main and settings views.
- `src/main-view.ts` — alarm-mode tile, time picker, day chips,
  snooze/dismiss buttons.
- `src/settings-view.ts` — sliders, test buttons, media picker modal,
  targets section.
- `src/editor.ts` — visual config (single dropdown).
- `src/related.ts` — entity-registry → related-entities resolver.
- `src/types.ts` — minimal HA + card types (no @types/home-assistant-js-websocket dependency).
- `src/styles.ts` — shared CSS.

The media picker mounts HA's built-in `<ha-media-player-browse>` Lit
element inside a modal, scoped to the first `media_player` configured
on the alarm. On pick it calls `wake_alarm.set_media`, which the
integration writes through to `sensor.<slug>_media_selection`.
