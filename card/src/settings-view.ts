import { LitElement, css, html, type PropertyValues, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { sharedStyles } from "./styles";
import type { HomeAssistant, MediaPickedItem, RelatedEntities } from "./types";

interface NumberSpec {
  key: keyof RelatedEntities["numbers"];
  label: string;
  min: number;
  max: number;
  step: number;
}

const SLIDERS: NumberSpec[] = [
  { key: "snooze_min", label: "Snooze (min)", min: 1, max: 30, step: 1 },
  { key: "length_min", label: "Length (min)", min: 1, max: 120, step: 1 },
  { key: "start_kelvin", label: "Start K", min: 1500, max: 6500, step: 50 },
  { key: "target_kelvin", label: "Target K", min: 1500, max: 6500, step: 50 },
  { key: "max_brightness_pct", label: "Max % Brightness", min: 1, max: 100, step: 1 },
  { key: "volume", label: "Alarm Volume (0–1)", min: 0, max: 1, step: 0.01 },
  { key: "music_fade_sec", label: "Music fade (s)", min: 0, max: 300, step: 5 },
  { key: "auto_dismiss_min", label: "Auto-dismiss (min)", min: 0, max: 120, step: 1 },
];

@customElement("wake-alarm-settings-view")
export class WakeAlarmSettingsView extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public related?: RelatedEntities;

  @state() private _showMediaPicker = false;

  protected shouldUpdate(changed: PropertyValues): boolean {
    return (
      changed.has("hass") ||
      changed.has("related") ||
      changed.has("_showMediaPicker")
    );
  }

  protected render(): TemplateResult {
    if (!this.hass || !this.related) return html``;
    const r = this.related;
    const fsmState = this.hass.states[r.sensors.state]?.state ?? "idle";
    const mediaSensor = this.hass.states[r.sensors.media_selection];
    const mediaTitle = mediaSensor?.state ?? "none";
    const hasMedia = mediaTitle !== "none";
    const mediaThumb = mediaSensor?.attributes?.thumbnail as string | undefined;

    const nextAlarm = this.hass.states[r.sensors.next_alarm];
    const lights = (nextAlarm?.attributes?.light_entities as string[]) ?? [];
    const players = (nextAlarm?.attributes?.media_player_entities as string[]) ?? [];
    const person = nextAlarm?.attributes?.person_entity as string | null | undefined;

    return html`
      <ha-card>
        <div class="header">
          <ha-icon-button label="Back" @click=${this._goBack}>
            <ha-icon icon="mdi:arrow-left"></ha-icon>
          </ha-icon-button>
          <div class="title">Settings</div>
        </div>

        <div class="section">
          ${SLIDERS.map((s) => this._renderSlider(s))}
        </div>

        <div class="section actions">
          <button class="btn" @click=${() => this._press("test_light_ramp")}>
            Test light ramp
          </button>
          ${fsmState === "ramping"
            ? html`<button class="btn" @click=${() => this._press("cancel_ramp")}>
                Cancel ramp
              </button>`
            : null}
          <button class="btn" @click=${() => this._press("test_music")}>
            Test music
          </button>
        </div>

        <div class="section media">
          <div class="section-title">Media</div>
          <div class="media-row" @click=${this._openMediaPicker}>
            ${hasMedia
              ? html`
                  ${mediaThumb
                    ? html`<img src=${mediaThumb} alt="" class="thumb" />`
                    : html`<div class="thumb thumb-placeholder">
                        <ha-icon icon="mdi:music"></ha-icon>
                      </div>`}
                  <div class="media-text">
                    <div class="media-title">${mediaTitle}</div>
                    <div class="media-sub">Tap to change</div>
                  </div>
                `
              : html`
                  <div class="thumb thumb-placeholder">
                    <ha-icon icon="mdi:music-note-plus"></ha-icon>
                  </div>
                  <div class="media-text">
                    <div class="media-title">No media picked</div>
                    <div class="media-sub">Tap to choose</div>
                  </div>
                `}
          </div>
        </div>

        <div class="section">
          <div class="section-title">Targets</div>
          <div class="targets">
            <div class="target-row">
              <ha-icon icon="mdi:account"></ha-icon>
              <span>${person ?? "—"}</span>
            </div>
            <div class="target-row">
              <ha-icon icon="mdi:lightbulb"></ha-icon>
              <span>${lights.join(", ") || "—"}</span>
            </div>
            <div class="target-row">
              <ha-icon icon="mdi:speaker"></ha-icon>
              <span>${players.join(", ") || "—"}</span>
            </div>
            <button class="btn small" @click=${this._openOptionsFlow}>
              Edit targets in HA settings
            </button>
          </div>
        </div>

        ${this._showMediaPicker ? this._renderMediaPickerDialog() : null}
      </ha-card>
    `;
  }

  private _renderSlider(spec: NumberSpec): TemplateResult {
    if (!this.hass || !this.related) return html``;
    const id = this.related.numbers[spec.key];
    const raw = this.hass.states[id]?.state;
    const val = raw && !["unknown", "unavailable"].includes(raw)
      ? Number(raw)
      : spec.min;
    const display = spec.step >= 1 ? val.toFixed(0) : val.toFixed(2);
    return html`
      <div class="slider-row">
        <div class="slider-head">
          <span class="label">${spec.label}</span>
          <span class="value">${display}</span>
        </div>
        <input
          type="range"
          min=${spec.min}
          max=${spec.max}
          step=${spec.step}
          .value=${String(val)}
          @change=${(ev: Event) => this._setNumber(id, ev)}
        />
      </div>
    `;
  }

  private _setNumber(entityId: string, ev: Event): void {
    if (!this.hass) return;
    const v = Number((ev.target as HTMLInputElement).value);
    void this.hass.callService("number", "set_value", {
      entity_id: entityId,
      value: v,
    });
  }

  private _press(key: keyof RelatedEntities["buttons"]): void {
    if (!this.hass || !this.related) return;
    void this.hass.callService("button", "press", {
      entity_id: this.related.buttons[key],
    });
  }

  private _openMediaPicker = (): void => {
    this._showMediaPicker = true;
  };

  private _closeMediaPicker = (): void => {
    this._showMediaPicker = false;
  };

  private _renderMediaPickerDialog(): TemplateResult {
    if (!this.hass || !this.related) return html``;
    const players = (this.hass.states[this.related.sensors.next_alarm]?.attributes
      ?.media_player_entities as string[]) ?? [];
    const targetPlayer = players[0];

    if (!targetPlayer) {
      return html`
        <div class="modal-backdrop" @click=${this._closeMediaPicker}>
          <div class="modal" @click=${(e: Event) => e.stopPropagation()}>
            <div class="modal-header">
              <div class="title">Pick media</div>
              <ha-icon-button @click=${this._closeMediaPicker}>
                <ha-icon icon="mdi:close"></ha-icon>
              </ha-icon-button>
            </div>
            <div class="error">
              No media players are configured for this alarm. Add one in
              Settings → Devices & Services.
            </div>
          </div>
        </div>
      `;
    }

    return html`
      <div class="modal-backdrop" @click=${this._closeMediaPicker}>
        <div class="modal large" @click=${(e: Event) => e.stopPropagation()}>
          <div class="modal-header">
            <div class="title">Pick media</div>
            <ha-icon-button @click=${this._closeMediaPicker}>
              <ha-icon icon="mdi:close"></ha-icon>
            </ha-icon-button>
          </div>
          <ha-media-player-browse
            .hass=${this.hass}
            .entityId=${targetPlayer}
            .navigateIds=${[{ media_content_id: undefined, media_content_type: undefined }]}
            @media-picked=${this._onMediaPicked}
          ></ha-media-player-browse>
        </div>
      </div>
    `;
  }

  private _onMediaPicked = (ev: CustomEvent<{ item: MediaPickedItem }>): void => {
    if (!this.hass || !this.related) return;
    const item = ev.detail?.item;
    if (!item) return;
    void this.hass.callService(
      "wake_alarm",
      "set_media",
      {
        media_content_id: item.media_content_id,
        media_content_type: item.media_content_type,
        title: item.title ?? item.media_content_id,
        thumbnail: item.thumbnail,
      },
      { entity_id: this.related.enabled },
    );
    this._closeMediaPicker();
  };

  private _openOptionsFlow = (): void => {
    if (!this.related) return;
    // Deep-link into Settings → Devices & Services → this entry → Configure
    history.pushState(
      null,
      "",
      `/config/integrations/integration/wake_alarm`,
    );
    window.dispatchEvent(new Event("location-changed"));
  };

  private _goBack = (): void => {
    this.dispatchEvent(
      new CustomEvent("navigate-back", { bubbles: true, composed: true }),
    );
  };

  static styles = [
    sharedStyles,
    css`
      .section {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .section-title {
        font-size: 0.95rem;
        font-weight: 500;
        color: var(--secondary-text-color);
      }
      .actions {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
      }

      .slider-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .slider-head {
        display: flex;
        align-items: center;
      }
      .slider-row input[type="range"] {
        width: 100%;
        accent-color: var(--primary-color);
      }

      .media-row {
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 8px;
        border-radius: var(--wa-radius);
        background: var(--ha-card-background, var(--card-background-color));
        border: 1px solid var(--divider-color);
        cursor: pointer;
      }
      .media-row:hover { background: var(--secondary-background-color); }
      .thumb {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        object-fit: cover;
      }
      .thumb-placeholder {
        background: var(--secondary-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--secondary-text-color);
      }
      .media-text { display: flex; flex-direction: column; gap: 2px; }
      .media-title { font-size: 1rem; font-weight: 500; }
      .media-sub { font-size: 0.85rem; color: var(--secondary-text-color); }

      .targets {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .target-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        color: var(--primary-text-color);
        word-break: break-all;
      }
      .target-row ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }
      button.btn.small {
        padding: 6px 12px;
        font-size: 0.85rem;
        align-self: flex-start;
      }

      .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999;
      }
      .modal {
        background: var(--card-background-color, white);
        border-radius: var(--wa-radius);
        max-width: 90vw;
        width: 480px;
        max-height: 90vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }
      .modal.large {
        width: 720px;
        height: 80vh;
      }
      .modal-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border-bottom: 1px solid var(--divider-color);
      }
      .modal-header .title {
        flex: 1;
        font-size: 1.1rem;
        font-weight: 500;
      }
      ha-media-player-browse {
        flex: 1;
        overflow: auto;
      }
    `,
  ];
}
