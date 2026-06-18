/**
 * Wake Alarm: Lovelace card.
 *
 * Top-level custom element. Reads the user-provided `entity:` (a
 * switch.<slug>_enabled), looks up its config_entry_id in the entity
 * registry, and resolves every related entity (day toggles, sliders,
 * buttons, sensors) by unique_id suffix. Two views (main, settings)
 * are rendered as child elements; a small navigate-* event swaps them.
 *
 * Pairs with the wake_alarm custom integration. Distributed via HACS.
 */
import { LitElement, html, type PropertyValues, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { sharedStyles } from "./styles";
import { CardConfigError, buildRelated } from "./related";
import type {
  EntityRegistryEntry,
  HomeAssistant,
  RelatedEntities,
  WakeAlarmCardConfig,
} from "./types";

import "./main-view";
import "./settings-view";
import "./editor";

@customElement("wake-alarm-card")
export class WakeAlarmCard extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: WakeAlarmCardConfig;
  @state() private _view: "main" | "settings" = "main";
  @state() private _related?: RelatedEntities;
  @state() private _resolveError?: string;

  // Bounded retry: a card can render before the integration has finished
  // registering its entities, in which case the first resolve throws. Retry on
  // later hass/config updates so it self-heals, but cap it so a genuinely
  // misconfigured entity can't spin the WS call forever.
  private static readonly _MAX_RESOLVE_ATTEMPTS = 10;
  private _resolving = false;
  private _resolveAttempts = 0;

  public setConfig(config: WakeAlarmCardConfig): void {
    // Allow incomplete config (e.g. the stub HA hands us when the user
    // first picks the card from the "Add Card" list). The editor pushes
    // a valid `entity` before the user can save, and render() short-
    // circuits with a "pick an entity" placeholder until then.
    if (
      config?.entity &&
      !config.entity.startsWith("switch.")
    ) {
      throw new Error(
        "wake-alarm-card: `entity` must be a switch (the wake_alarm enabled switch).",
      );
    }
    this._config =
      config ?? ({ type: "custom:wake-alarm-card", entity: "" } as WakeAlarmCardConfig);
    this._related = undefined;
    this._resolveError = undefined;
    this._resolving = false;
    this._resolveAttempts = 0;
  }

  public getCardSize(): number {
    return 6;
  }

  public static getConfigElement(): HTMLElement {
    return document.createElement("wake-alarm-card-editor");
  }

  public static async getStubConfig(
    hass?: HomeAssistant,
  ): Promise<WakeAlarmCardConfig> {
    // Look up the first real wake_alarm enabled-switch via the entity
    // registry so the stub picks something actually compatible — naive
    // hass.states matching on `switch.*_enabled` also grabs things like
    // Sonos subwoofer-enabled switches, which then fail resolution on save.
    if (!hass) {
      return { type: "custom:wake-alarm-card", entity: "" };
    }
    try {
      const entries = await hass.callWS<EntityRegistryEntry[]>({
        type: "config/entity_registry/list",
      });
      const candidate = entries.find(
        (e) =>
          e.platform === "wake_alarm" &&
          (e.unique_id ?? "").endsWith("_enabled") &&
          (e.entity_id ?? "").startsWith("switch."),
      );
      return {
        type: "custom:wake-alarm-card",
        entity: candidate?.entity_id ?? "",
      };
    } catch {
      return { type: "custom:wake-alarm-card", entity: "" };
    }
  }

  protected willUpdate(changed: PropertyValues): void {
    // Resolve once the registry is reachable. Retry only on real hass/config
    // updates (not on our own _resolveError state change) so the attempts
    // spread out as the integration finishes loading, rather than bursting
    // through the cap instantly.
    if (
      this.hass &&
      this._config?.entity &&
      !this._related &&
      !this._resolving &&
      this._resolveAttempts < WakeAlarmCard._MAX_RESOLVE_ATTEMPTS &&
      (changed.has("hass") || changed.has("_config"))
    ) {
      void this._resolveRelated();
    }
  }

  private async _resolveRelated(): Promise<void> {
    if (!this.hass || !this._config) return;
    this._resolving = true;
    this._resolveAttempts += 1;
    try {
      const entries = await this.hass.callWS<EntityRegistryEntry[]>({
        type: "config/entity_registry/list",
      });
      this._related = buildRelated(this._config.entity, entries);
      this._resolveError = undefined;
    } catch (e) {
      if (e instanceof CardConfigError) {
        this._resolveError = e.message;
      } else {
        this._resolveError = `Could not resolve wake_alarm entities: ${e}`;
      }
    } finally {
      this._resolving = false;
    }
  }

  protected render(): TemplateResult {
    if (!this._config) return html``;
    if (!this._config.entity) {
      // First-time "Add Card" path before the visual editor has run.
      return html`<ha-card><div class="loading">
        Pick a Wake Alarm enabled-switch in the visual editor.
      </div></ha-card>`;
    }
    if (this._resolveError) {
      return html`<ha-card><div class="error">${this._resolveError}</div></ha-card>`;
    }
    if (!this._related || !this.hass) {
      return html`<ha-card><div class="loading">Loading…</div></ha-card>`;
    }
    return this._view === "settings"
      ? html`
          <wake-alarm-settings-view
            .hass=${this.hass}
            .related=${this._related}
            @navigate-back=${this._goMain}
          ></wake-alarm-settings-view>
        `
      : html`
          <wake-alarm-main-view
            .hass=${this.hass}
            .related=${this._related}
            @navigate-settings=${this._goSettings}
          ></wake-alarm-main-view>
        `;
  }

  private _goMain = (): void => { this._view = "main"; };
  private _goSettings = (): void => { this._view = "settings"; };

  static styles = sharedStyles;
}

// Register in HA's "Add Card" picker.
window.customCards = window.customCards ?? [];
window.customCards.push({
  type: "wake-alarm-card",
  name: "Wake Alarm",
  description: "Wake-up alarm with a gradual light ramp and a music sequence.",
  preview: false,
});

// eslint-disable-next-line no-console
console.info(
  "%c WAKE-ALARM-CARD %c v0.5.0 ",
  "color: white; background: #ff5722; font-weight: 700;",
  "color: #ff5722; background: white; font-weight: 700;",
);
