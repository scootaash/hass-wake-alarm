import { describe, expect, it } from "vitest";
import { CardConfigError, buildRelated } from "../src/related";
import type { EntityRegistryEntry } from "../src/types";

const ENTRY = "01abcd";

function makeEntry(
  entity_id: string,
  unique_id: string,
  overrides: Partial<EntityRegistryEntry> = {},
): EntityRegistryEntry {
  return {
    entity_id,
    unique_id,
    config_entry_id: ENTRY,
    platform: "wake_alarm",
    device_id: null,
    disabled_by: null,
    hidden_by: null,
    ...overrides,
  };
}

const FULL_REGISTRY: EntityRegistryEntry[] = [
  makeEntry("switch.bedroom_enabled", `${ENTRY}_enabled`),
  makeEntry("switch.bedroom_d1_mon", `${ENTRY}_d1_mon`),
  makeEntry("switch.bedroom_d2_tue", `${ENTRY}_d2_tue`),
  makeEntry("switch.bedroom_d3_wed", `${ENTRY}_d3_wed`),
  makeEntry("switch.bedroom_d4_thu", `${ENTRY}_d4_thu`),
  makeEntry("switch.bedroom_d5_fri", `${ENTRY}_d5_fri`),
  makeEntry("switch.bedroom_d6_sat", `${ENTRY}_d6_sat`),
  makeEntry("switch.bedroom_d7_sun", `${ENTRY}_d7_sun`),
  makeEntry("time.bedroom_alarm_time", `${ENTRY}_alarm_time`),
  makeEntry("number.bedroom_length_min", `${ENTRY}_length_min`),
  makeEntry("number.bedroom_start_kelvin", `${ENTRY}_start_kelvin`),
  makeEntry("number.bedroom_target_kelvin", `${ENTRY}_target_kelvin`),
  makeEntry("number.bedroom_max_brightness_pct", `${ENTRY}_max_brightness_pct`),
  makeEntry("number.bedroom_volume", `${ENTRY}_volume`),
  makeEntry("number.bedroom_snooze_min", `${ENTRY}_snooze_min`),
  makeEntry("number.bedroom_steps_per_min", `${ENTRY}_steps_per_min`),
  makeEntry("number.bedroom_music_fade_sec", `${ENTRY}_music_fade_sec`),
  makeEntry("number.bedroom_auto_dismiss_min", `${ENTRY}_auto_dismiss_min`),
  makeEntry("button.bedroom_test_light_ramp", `${ENTRY}_test_light_ramp`),
  makeEntry("button.bedroom_cancel_ramp", `${ENTRY}_cancel_ramp`),
  makeEntry("button.bedroom_test_music", `${ENTRY}_test_music`),
  makeEntry("button.bedroom_dismiss", `${ENTRY}_dismiss`),
  makeEntry("button.bedroom_snooze", `${ENTRY}_snooze`),
  makeEntry("sensor.bedroom_next_alarm", `${ENTRY}_next_alarm`),
  makeEntry("sensor.bedroom_state", `${ENTRY}_state`),
  makeEntry("sensor.bedroom_media_selection", `${ENTRY}_media_selection`),
  makeEntry("binary_sensor.bedroom_active", `${ENTRY}_active`),
];

describe("buildRelated", () => {
  it("resolves every entity from a complete registry", () => {
    const r = buildRelated("switch.bedroom_enabled", FULL_REGISTRY);
    expect(r.configEntryId).toBe(ENTRY);
    expect(r.enabled).toBe("switch.bedroom_enabled");
    expect(r.alarmTime).toBe("time.bedroom_alarm_time");
    expect(r.active).toBe("binary_sensor.bedroom_active");
    expect(r.days.mon).toBe("switch.bedroom_d1_mon");
    expect(r.days.sun).toBe("switch.bedroom_d7_sun");
    expect(r.numbers.start_kelvin).toBe("number.bedroom_start_kelvin");
    expect(r.numbers.auto_dismiss_min).toBe("number.bedroom_auto_dismiss_min");
    expect(r.buttons.snooze).toBe("button.bedroom_snooze");
    expect(r.buttons.test_music).toBe("button.bedroom_test_music");
    expect(r.sensors.media_selection).toBe("sensor.bedroom_media_selection");
  });

  it("ignores entries from other config entries", () => {
    const otherEntry = "99zzzz";
    const noisy: EntityRegistryEntry[] = [
      ...FULL_REGISTRY,
      makeEntry("switch.other_enabled", `${otherEntry}_enabled`, {
        config_entry_id: otherEntry,
      }),
      makeEntry("light.lounge", "device_xx", {
        config_entry_id: "some_hue_entry",
        platform: "hue",
      }),
    ];
    const r = buildRelated("switch.bedroom_enabled", noisy);
    expect(r.enabled).toBe("switch.bedroom_enabled");
    expect(r.configEntryId).toBe(ENTRY);
  });

  it("throws when the provided entity is not in the registry", () => {
    expect(() =>
      buildRelated("switch.does_not_exist", FULL_REGISTRY),
    ).toThrow(CardConfigError);
  });

  it("throws when the provided entity is not a wake_alarm entity", () => {
    const reg: EntityRegistryEntry[] = [
      makeEntry("switch.lounge", "abc", { platform: "hue" }),
    ];
    expect(() => buildRelated("switch.lounge", reg)).toThrow(CardConfigError);
  });

  it("throws when a required entity is missing", () => {
    // Drop the alarm_time entity
    const partial = FULL_REGISTRY.filter(
      (e) => e.entity_id !== "time.bedroom_alarm_time",
    );
    expect(() =>
      buildRelated("switch.bedroom_enabled", partial),
    ).toThrow(/alarm_time/);
  });

  it("ignores entries whose unique_id doesn't follow the convention", () => {
    const reg: EntityRegistryEntry[] = [
      ...FULL_REGISTRY,
      makeEntry("switch.bedroom_legacy", "legacy_unique_id"),
    ];
    const r = buildRelated("switch.bedroom_enabled", reg);
    expect(r.enabled).toBe("switch.bedroom_enabled");
  });
});
