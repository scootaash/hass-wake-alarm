# Wake Alarm — contributor / agent guide

Sunrise wake-up alarm for Home Assistant: lights ramp up before alarm time,
music fades in at alarm time. Multi-instance, multi-room, ships its own Lovelace
card. User-facing docs are in `README.md`; this file is the durable engineering
context (architecture, testing, CI, conventions) so it doesn't have to be
re-explained each session.

## Repository layout

- `custom_components/wake_alarm/` — the integration (Python).
- `card/` — the Lovelace card (TypeScript / Lit), built into a bundle that is
  **committed** at `custom_components/wake_alarm/www/wake-alarm-card.js`.
- `tests/` — Python test suite (pytest + pytest-homeassistant-custom-component).
- `.github/workflows/ci.yml` — CI (pytest matrix, ruff, card build).
- `hacs.json` / `custom_components/wake_alarm/manifest.json` — HACS / HA metadata.

## Architecture (integration)

- `__init__.py` — `async_setup_entry` / `async_unload_entry`, the config-entry
  migration (`async_migrate_entry`, **currently entry version 2**), and the
  Lovelace card registration (`_async_register_card`, signs nothing — serves the
  static bundle + `add_extra_js_url`).
- `coordinator.py` — the heart: the alarm **state machine** and scheduling.
  Arms timers via `async_track_point_in_time`, fires the light ramp at
  `alarm_time − length`, music at `alarm_time`, handles snooze / dismiss /
  auto-dismiss, restart catch-up, and **presence gating** (checked twice — at
  ramp-start for lights and again at alarm time for music). Side-effects
  (`async_run_light_ramp`, `async_run_music_sequence`, `async_send_*`
  notifications) are module-level functions so tests can patch them.
- `_pure.py` — HA-free scheduling math (`plan_schedule`, next-fire/rollover/DST).
  Kept import-free of `homeassistant` so it's unit-testable in isolation.
- `const.py` — `DOMAIN`, `PLATFORMS` (switch, time, number, sensor,
  binary_sensor, button), `DAYS`, and all `CONF_*` entry-data keys
  (`CONF_SLUG`, `CONF_LIGHT_ENTITIES`, `CONF_MEDIA_PLAYER_ENTITIES`,
  `CONF_PERSON_ENTITY`, `CONF_NOTIFY_TARGET_STANDARD/URGENT`; `CONF_NAME` from
  `homeassistant.const`).
- `config_flow.py` — `ConfigFlow` + `OptionsFlow` (uses `ConfigFlowResult`,
  HA 2024.4+). New user-configurable options go here **and** in the options flow.
- `light_ramp.py`, `music_sequence.py`, `notifications.py`, `services.py`
  (incl. the `set_media` service), and the entity platforms
  `switch/number/time/sensor/binary_sensor/button/entity.py`.

When adding fields to config-entry **data**, bump the entry version and extend
`async_migrate_entry`, and provide sensible defaults for existing entries.

## Architecture (card)

- Lit components in `card/src/`: `wake-alarm-card.ts` (root + entity resolver),
  `main-view.ts`, `settings-view.ts`, `media-browser.ts`, `media-thumb.ts`
  (`<wake-alarm-thumb>` — signs HA image-proxy thumbnails via `auth/sign_path`,
  square box + icon fallback), `media-image.ts`, `related.ts`, `editor.ts`,
  `types.ts` (minimal hand-written HA types; no `@types/...` dep).
- The card derives every entity from one config entry given the enabled-switch
  as `entity`. It talks to HA over `hass.callWS` / `hass.callService`.

## Development & testing

### Python
- Two local virtualenvs exist: `.venv` (latest HA, Python 3.13) and `.venv-min`
  (Python 3.12). Run the suite on both before pushing:
  - `.venv/bin/python -m pytest tests/ -q`
  - `.venv-min/bin/python -m pytest tests/ -q`
- Test layers:
  - `tests/integration/test_coordinator.py` — drives a **real coordinator** with
    a frozen clock (`freezer` + `async_fire_time_changed`) and mocked
    side-effects. Add a scenario here for every behaviour change.
  - `tests/integration/conftest.py` — the `env` harness (entry/state builders,
    patched runners + notifications, `async_mock_service`) and the
    `card_frontend` fixture (the real `frontend` component can't load under PHACC
    — `hass_frontend` isn't installed — so it stubs `http` + the
    `add_extra_js_url` data store).
  - `tests/integration/test_setup.py` — full config-entry setup/unload smoke
    test (`skipif` below HA 2024.4, where `config_flow`'s `ConfigFlowResult`
    import fails).
  - `tests/integration/test_card_registration.py` — card static-route + version
    signing regression tests.
  - `tests/integration/test_schedule.py` / `test_light_ramp.py` — `_pure` math.
- `pyproject.toml`: `asyncio_mode = "auto"`; warnings are surfaced, not errors
  (the HA matrix emits version-specific deprecations). Coverage is reported
  (advisory, no enforced threshold) via `pytest-cov` — run with
  `pytest tests/ --cov --cov-report=term-missing`.

### Lint
- `ruff check custom_components tests` — rules `E,F,W,I`, line-length 88. Must be
  clean (hard CI gate).

### Card
- `cd card && npm ci`
- `npm run lint` (`tsc --noEmit`), `npm test` (vitest), `npm run build` (rollup).
- The build is **deterministic**; CI fails if the committed
  `custom_components/wake_alarm/www/wake-alarm-card.js` isn't a fresh build. So
  after any `card/src` change, rebuild and **commit the regenerated bundle**.

## CI (`.github/workflows/ci.yml`)
- `ruff` job.
- `pytest` matrix: **min** = PHACC `0.13.132` (HA 2024.6.0, py3.12, with a
  `josepy<2` pin — josepy 2.x breaks that HA's `acme` import) and **latest** =
  PHACC `0.13.316` (py3.13). PHACC version → HA version is fixed; 2024.4/2024.5
  PHACC builds pin a removed `mypy-dev` alpha and won't install, so 2024.6 is the
  oldest installable floor.
- `card` job: lint + vitest + build + **bundle-freshness** check.

## Minimum supported HA
**2024.6** (`hacs.json`). Keep changes compatible with it (e.g. `config_flow`
needs `ConfigFlowResult`, present since 2024.4; the card guards the newer
`async_register_static_paths` with a fallback).

## Conventions
- Develop on a feature branch off the latest `main`; open PRs **ready for
  review**, one per logical change. Keep diffs focused/reviewable.
- Don't merge on red CI. Add regression tests for every behaviour change — this
  repo treats "does the alarm actually fire?" as a CI gate (see #25).
- If a behaviour change affects what the card shows, update the card (and rebuild
  the bundle) in the same PR.
- Match the existing commit/PR style in `git log`. Do **not** put model
  identifiers in commits, PRs, code, or any committed artifact.
- Feature/triage discussion lives in GitHub issues; link PRs to the issue they
  close.
