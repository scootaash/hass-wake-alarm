import { LitElement, css, html, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { EntityRegistryEntry, HomeAssistant, WakeAlarmCardConfig } from "./types";

@customElement("wake-alarm-card-editor")
export class WakeAlarmCardEditor extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;

  @state() private _config?: WakeAlarmCardConfig;
  @state() private _enabledSwitches: string[] = [];
  @state() private _loadError?: string;

  public setConfig(config: WakeAlarmCardConfig): void {
    this._config = config;
  }

  protected firstUpdated(): void {
    void this._loadEnabledSwitches();
  }

  private async _loadEnabledSwitches(): Promise<void> {
    if (!this.hass) return;
    try {
      const entries = await this.hass.callWS<EntityRegistryEntry[]>({
        type: "config/entity_registry/list",
      });
      // wake_alarm enabled-switches: platform == wake_alarm, unique_id endswith "_enabled"
      this._enabledSwitches = entries
        .filter(
          (e) =>
            e.platform === "wake_alarm" &&
            (e.unique_id ?? "").endsWith("_enabled") &&
            e.entity_id.startsWith("switch."),
        )
        .map((e) => e.entity_id)
        .sort();

      // Self-heal: if the incoming config (e.g. a bad stub from an older
      // build) points to an entity that isn't actually a wake_alarm
      // enabled-switch, clear it so the user has to pick a valid one
      // before saving. Push the cleared config back via config-changed
      // so the parent editor preview matches what's saved.
      if (
        this._config?.entity &&
        !this._enabledSwitches.includes(this._config.entity)
      ) {
        const cleared = { ...this._config, entity: "" };
        this._config = cleared;
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config: cleared },
            bubbles: true,
            composed: true,
          }),
        );
      }
    } catch (e) {
      this._loadError = `${e}`;
    }
  }

  protected render(): TemplateResult {
    if (!this._config) return html``;
    if (this._loadError) {
      return html`<div class="error">Failed to load wake_alarm entities: ${this._loadError}</div>`;
    }
    return html`
      <div class="row">
        <label for="entity">Wake Alarm instance</label>
        <select
          id="entity"
          .value=${this._config.entity ?? ""}
          @change=${this._onEntityChange}
        >
          <option value="" disabled ?selected=${!this._config.entity}>
            Pick a wake_alarm enabled-switch…
          </option>
          ${this._enabledSwitches.map(
            (e) => html`<option value=${e} ?selected=${this._config!.entity === e}>${e}</option>`,
          )}
        </select>
      </div>
      ${this._enabledSwitches.length === 0
        ? html`<div class="hint">
            No wake_alarm instances yet. Add one in
            Settings → Devices &amp; Services → Add Integration → Wake Alarm.
          </div>`
        : null}
    `;
  }

  private _onEntityChange = (ev: Event): void => {
    const newEntity = (ev.target as HTMLSelectElement).value;
    const next = { ...(this._config ?? { type: "custom:wake-alarm-card" }), entity: newEntity };
    this._config = next as WakeAlarmCardConfig;
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: next },
        bubbles: true,
        composed: true,
      }),
    );
  };

  static styles = css`
    :host { display: block; padding: 12px; }
    .row { display: flex; flex-direction: column; gap: 6px; }
    label { font-size: 0.9rem; color: var(--secondary-text-color); }
    select {
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--primary-text-color);
      font-size: 0.95rem;
    }
    .hint { padding-top: 8px; color: var(--secondary-text-color); font-size: 0.85rem; }
    .error { color: var(--error-color, rgb(255, 82, 82)); }
  `;
}
