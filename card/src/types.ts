/**
 * Minimal Home Assistant types used by the card.
 *
 * Avoids depending on @types/home-assistant-js-websocket so the bundle
 * stays small and the card has zero runtime deps beyond Lit.
 */

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  context: { id: string; user_id: string | null; parent_id: string | null };
  last_changed: string;
  last_updated: string;
}

export interface ServiceCallOptions {
  return_response?: boolean;
}

export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  callService: (
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: { entity_id?: string | string[] },
    options?: ServiceCallOptions,
  ) => Promise<unknown>;
  callWS: <T = unknown>(msg: WSMessage) => Promise<T>;
  language: string;
  locale: { language: string };
  user?: { name: string };
}

export interface EntityRegistryEntry {
  entity_id: string;
  unique_id: string | null;
  config_entry_id: string | null;
  platform: string;
  device_id: string | null;
  disabled_by: string | null;
  hidden_by: string | null;
  name?: string | null;
  original_name?: string | null;
}

export interface WakeAlarmCardConfig {
  type: string;
  entity: string;
}

export type DayKey = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export const DAYS: DayKey[] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

/** Resolved Wake Alarm entity IDs, keyed by purpose. */
export interface RelatedEntities {
  configEntryId: string;
  // Top-level
  enabled: string; // switch.<slug>_enabled
  active: string; // binary_sensor.<slug>_active
  alarmTime: string; // time.<slug>_alarm_time
  // Day toggles
  days: Record<DayKey, string>;
  // Number config
  numbers: {
    length_min: string;
    start_kelvin: string;
    target_kelvin: string;
    max_brightness_pct: string;
    volume: string;
    snooze_min: string;
    steps_per_min: string;
    music_fade_sec: string;
    auto_dismiss_min: string;
  };
  // Action buttons
  buttons: {
    test_light_ramp: string;
    cancel_ramp: string;
    test_music: string;
    test_standard_notification: string;
    test_urgent_notification: string;
    dismiss: string;
    snooze: string;
  };
  // Status sensors
  sensors: {
    next_alarm: string;
    state: string;
    media_selection: string;
  };
}

/** Detail emitted by ha-media-player-browse when the user picks an item. */
export interface MediaPickedItem {
  media_content_id: string;
  media_content_type: string;
  title?: string;
  thumbnail?: string;
}

/** HA frontend exposes window.loadCardHelpers() etc; we mostly don't need it. */
declare global {
  interface Window {
    customCards?: Array<{
      type: string;
      name: string;
      description?: string;
      preview?: boolean;
    }>;
  }
}
