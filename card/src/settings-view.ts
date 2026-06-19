import { LitElement, css, html, type PropertyValues, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { sharedStyles } from "./styles";
import { showsMediaControls } from "./view-logic";
import "./media-browser";
import "./media-thumb";
import type { HomeAssistant, MediaPickedItem, RelatedEntities } from "./types";

interface NumberSpec {
  key: keyof RelatedEntities["numbers"];
  label: string;
  description: string;
  min: number;
  max: number;
  step: number;
  /** Multiplier applied when *displaying* the entity value. The slider's
   *  min/max/step refer to the displayed value; the underlying entity is
   *  written as displayedValue / displayMultiplier on change. Use this to
   *  show 0–1.0 entities as percentages. */
  displayMultiplier?: number;
}

const SLIDERS: NumberSpec[] = [
  {
    key: "snooze_min",
    label: "Snooze (min)",
    description: "How long the snooze pause lasts before music resumes.",
    min: 1, max: 30, step: 1,
  },
  {
    key: "length_min",
    label: "Length (min)",
    description: "Total minutes the lights ramp up before the alarm time.",
    min: 1, max: 120, step: 1,
  },
  {
    key: "start_kelvin",
    label: "Start K",
    description: "Warm colour temperature at the beginning of the ramp.",
    min: 1500, max: 6500, step: 50,
  },
  {
    key: "target_kelvin",
    label: "Target K",
    description: "Cool colour temperature reached at the alarm time.",
    min: 1500, max: 6500, step: 50,
  },
  {
    key: "max_brightness_pct",
    label: "Max % Brightness",
    description: "Peak brightness reached at the alarm time.",
    min: 1, max: 100, step: 1,
  },
  {
    key: "volume",
    label: "Alarm Volume (%)",
    description: "Final volume the music fades up to. Defaults to a low value so test plays don't blast.",
    min: 0, max: 100, step: 1,
    displayMultiplier: 100,
  },
  {
    key: "music_fade_sec",
    label: "Music fade (s)",
    description: "How long the volume takes to fade from 0 to the target volume.",
    min: 0, max: 300, step: 5,
  },
  {
    key: "auto_dismiss_min",
    label: "Auto-dismiss (min)",
    description: "Stop everything this long after the music starts (the alarm time) — not the start of the light ramp. 0 disables.",
    min: 0, max: 120, step: 1,
  },
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
    const showMedia = showsMediaControls(players);

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
          ${showMedia
            ? html`<button class="btn" @click=${() => this._press("test_music")}>
                Test music
              </button>`
            : null}
        </div>

        <div class="section">
          <div class="section-title">Notifications</div>
          <div class="notif-item">
            <button
              class="btn"
              @click=${() => this._press("test_standard_notification")}
            >
              Test standard notification
            </button>
            <div class="slider-desc">
              Sends a mobile notification on this device at alarm time to allow
              easy access to snooze.
            </div>
          </div>
          ${showMedia
            ? html`<div class="notif-item">
                <button
                  class="btn"
                  @click=${() => this._press("test_urgent_notification")}
                >
                  Test urgent notification
                </button>
                <div class="slider-desc">
                  Sends an urgent mobile notification on this device when
                  speakers are unavailable or no media has been picked, so you
                  should still be woken up — although less pleasantly :-)
                </div>
              </div>`
            : null}
        </div>

        ${showMedia
          ? html`<div class="section media">
              <div class="section-title">Media</div>
              <div class="media-row" @click=${this._openMediaPicker}>
                ${hasMedia
                  ? html`
                      <wake-alarm-thumb
                        class="thumb"
                        .hass=${this.hass}
                        .thumbnail=${mediaThumb ?? null}
                        icon="mdi:music"
                      ></wake-alarm-thumb>
                      <div class="media-text">
                        <div class="media-title">${mediaTitle}</div>
                        <div class="media-sub">Tap to change</div>
                      </div>
                    `
                  : html`
                      <wake-alarm-thumb
                        class="thumb"
                        icon="mdi:music-note-plus"
                      ></wake-alarm-thumb>
                      <div class="media-text">
                        <div class="media-title">No media picked</div>
                        <div class="media-sub">Tap to choose</div>
                      </div>
                    `}
              </div>
            </div>`
          : null}

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
    const entityVal =
      raw && !["unknown", "unavailable"].includes(raw)
        ? Number(raw)
        : spec.min / (spec.displayMultiplier ?? 1);
    const multiplier = spec.displayMultiplier ?? 1;
    const displayedVal = entityVal * multiplier;
    const display =
      spec.step >= 1 ? displayedVal.toFixed(0) : displayedVal.toFixed(2);
    return html`
      <div class="slider-row">
        <div class="slider-head">
          <span class="label">${spec.label}</span>
          <span class="value">${display}</span>
        </div>
        <div class="slider-desc">${spec.description}</div>
        <input
          type="range"
          min=${spec.min}
          max=${spec.max}
          step=${spec.step}
          .value=${String(displayedVal)}
          @change=${(ev: Event) => this._setNumber(id, ev, multiplier)}
        />
      </div>
    `;
  }

  private _setNumber(entityId: string, ev: Event, multiplier: number): void {
    if (!this.hass) return;
    const displayed = Number((ev.target as HTMLInputElement).value);
    const entityValue = displayed / multiplier;
    void this.hass.callService("number", "set_value", {
      entity_id: entityId,
      value: entityValue,
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
          <wake-alarm-media-browser
            .hass=${this.hass}
            .entityId=${targetPlayer}
            @media-picked=${this._onMediaPicked}
          ></wake-alarm-media-browser>
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

      .notif-item {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .notif-item .btn {
        align-self: flex-start;
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
      .slider-desc {
        font-size: 0.8rem;
        color: var(--secondary-text-color);
        line-height: 1.3;
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
        border-radius: 8px;
        flex: 0 0 auto;
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
      wake-alarm-media-browser {
        flex: 1;
        overflow: auto;
        min-height: 0;
      }
    `,
  ];
}
