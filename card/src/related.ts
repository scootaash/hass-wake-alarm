/**
 * Resolve every entity that belongs to the same wake_alarm config entry as
 * the user-provided enabled-switch entity.
 *
 * Strategy: look the provided entity up in the entity registry, take its
 * config_entry_id, then bucket every other entity in that config entry by
 * the suffix on its unique_id. Entity unique_ids in the integration follow
 * the pattern `<config_entry_id>_<key>` so the bucketing is deterministic.
 */

import {
  DAYS,
  type DayKey,
  type EntityRegistryEntry,
  type RelatedEntities,
} from "./types";

// Integration v2+ uses "d1_mon"..."d7_sun" as the entity-key suffix so
// HA's alphabetical entity sort displays the day toggles in calendar
// order. The card keeps the short Mon..Sun keys internally, so we map
// the suffix back to the friendlier name here.
const DAY_KEY_FROM_SUFFIX: Record<string, DayKey> = {
  d1_mon: "mon",
  d2_tue: "tue",
  d3_wed: "wed",
  d4_thu: "thu",
  d5_fri: "fri",
  d6_sat: "sat",
  d7_sun: "sun",
};

const NUMBER_KEYS = [
  "length_min",
  "start_kelvin",
  "target_kelvin",
  "max_brightness_pct",
  "volume",
  "snooze_min",
  "steps_per_min",
  "music_fade_sec",
  "auto_dismiss_min",
] as const;

const BUTTON_KEYS = [
  "test_light_ramp",
  "cancel_ramp",
  "test_music",
  "test_standard_notification",
  "test_urgent_notification",
  "dismiss",
  "snooze",
] as const;

const SENSOR_KEYS = ["next_alarm", "state", "media_selection"] as const;

export class CardConfigError extends Error {}

export function buildRelated(
  enabledEntityId: string,
  registry: EntityRegistryEntry[],
): RelatedEntities {
  const myEntry = registry.find((e) => e.entity_id === enabledEntityId);
  if (!myEntry) {
    throw new CardConfigError(
      `Entity ${enabledEntityId} is not in the entity registry.`,
    );
  }
  if (myEntry.platform !== "wake_alarm") {
    throw new CardConfigError(
      `Entity ${enabledEntityId} is not a wake_alarm entity (platform=${myEntry.platform}).`,
    );
  }
  const configEntryId = myEntry.config_entry_id;
  if (!configEntryId) {
    throw new CardConfigError(
      `Entity ${enabledEntityId} has no config_entry_id.`,
    );
  }

  // Bucket every related entity by its unique_id suffix.
  const byKey: Record<string, string> = {};
  const days = {} as RelatedEntities["days"];
  const prefix = `${configEntryId}_`;
  for (const e of registry) {
    if (e.config_entry_id !== configEntryId) continue;
    if (!e.unique_id || !e.unique_id.startsWith(prefix)) continue;
    const key = e.unique_id.slice(prefix.length);
    const dayKey = DAY_KEY_FROM_SUFFIX[key];
    if (dayKey) {
      days[dayKey] = e.entity_id;
    } else {
      byKey[key] = e.entity_id;
    }
  }

  const need = (k: string): string => {
    const v = byKey[k];
    if (!v) {
      throw new CardConfigError(
        `Wake Alarm entity for "${k}" is missing from the registry. ` +
          `Make sure the integration is fully loaded.`,
      );
    }
    return v;
  };

  for (const d of DAYS) {
    if (!days[d]) {
      throw new CardConfigError(
        `Wake Alarm day toggle for "${d}" is missing from the registry. ` +
          `Make sure the integration is fully loaded and migrated to v2+.`,
      );
    }
  }

  const numbers = {} as RelatedEntities["numbers"];
  for (const k of NUMBER_KEYS) numbers[k] = need(k);

  const buttons = {} as RelatedEntities["buttons"];
  for (const k of BUTTON_KEYS) buttons[k] = need(k);

  const sensors = {} as RelatedEntities["sensors"];
  for (const k of SENSOR_KEYS) sensors[k] = need(k);

  return {
    configEntryId,
    enabled: need("enabled"),
    active: need("active"),
    alarmTime: need("alarm_time"),
    days,
    numbers,
    buttons,
    sensors,
  };
}
