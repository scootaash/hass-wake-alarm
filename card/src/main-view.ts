import { LitElement, css, html, type PropertyValues, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { sharedStyles } from "./styles";
import { DAYS, type DayKey, type HomeAssistant, type RelatedEntities } from "./types";

@customElement("wake-alarm-main-view")
export class WakeAlarmMainView extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public related?: RelatedEntities;

  protected shouldUpdate(changed: PropertyValues): boolean {
    return changed.has("hass") || changed.has("related");
  }

  protected render(): TemplateResult {
    if (!this.hass || !this.related) return html``;
    const r = this.related;
    const enabledState = this.hass.states[r.enabled];
    const stateState = this.hass.states[r.sensors.state];
    const activeState = this.hass.states[r.active];
    const alarmTimeState = this.hass.states[r.alarmTime];
    const nextAlarmState = this.hass.states[r.sensors.next_alarm];

    const isEnabled = enabledState?.state === "on";
    const fsmState = stateState?.state ?? "idle";
    const isActive = activeState?.state === "on";
    const time = parseTime(alarmTimeState?.state);

    const modeIcon = ICONS[fsmState] ?? ICONS.idle;
    const modeLabel = isEnabled
      ? labelForFsmState(fsmState)
      : "Off";

    const nextLabel = nextAlarmState?.state && nextAlarmState.state !== "unknown"
      ? formatNext(nextAlarmState.state)
      : "No upcoming alarm";

    return html`
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:alarm"></ha-icon>
          <div class="title">${this._instanceName()}</div>
          <ha-icon-button
            label="Settings"
            @click=${this._goSettings}
          >
            <ha-icon icon="mdi:cog"></ha-icon>
          </ha-icon-button>
        </div>

        <div class="mode-tile mode-${isEnabled ? fsmState : "off"}" @click=${this._toggleEnabled}>
          <ha-icon icon=${modeIcon}></ha-icon>
          <div class="mode-text">
            <div class="mode-label">${modeLabel}</div>
            <div class="mode-next">${isEnabled ? nextLabel : "Tap to enable"}</div>
          </div>
        </div>

        <div class="time-picker">
          <div class="time-col">
            <ha-icon-button @click=${() => this._adjustTime(1, 0)}>
              <ha-icon icon="mdi:menu-up"></ha-icon>
            </ha-icon-button>
            <div class="time-num">${pad(time.h)}</div>
            <ha-icon-button @click=${() => this._adjustTime(-1, 0)}>
              <ha-icon icon="mdi:menu-down"></ha-icon>
            </ha-icon-button>
          </div>
          <div class="time-sep">:</div>
          <div class="time-col">
            <ha-icon-button @click=${() => this._adjustTime(0, 1)}>
              <ha-icon icon="mdi:menu-up"></ha-icon>
            </ha-icon-button>
            <div class="time-num">${pad(time.m)}</div>
            <ha-icon-button @click=${() => this._adjustTime(0, -1)}>
              <ha-icon icon="mdi:menu-down"></ha-icon>
            </ha-icon-button>
          </div>
        </div>

        <div class="day-chips">
          ${DAYS.map((d) => this._renderDayChip(d))}
        </div>

        ${isActive ? this._renderActiveActions() : null}
      </ha-card>
    `;
  }

  private _renderDayChip(day: DayKey): TemplateResult {
    if (!this.hass || !this.related) return html``;
    const id = this.related.days[day];
    const on = this.hass.states[id]?.state === "on";
    return html`
      <div
        class="chip ${on ? "chip-on" : "chip-off"}"
        @click=${() => this._toggleDay(day)}
      >
        <ha-icon icon=${on ? "mdi:check-circle" : "mdi:close-circle-outline"}></ha-icon>
        <span>${LABELS[day]}</span>
      </div>
    `;
  }

  private _renderActiveActions(): TemplateResult {
    return html`
      <div class="row">
        <button class="btn" @click=${this._snooze}>Snooze</button>
        <button class="btn danger" @click=${this._dismiss}>Dismiss</button>
      </div>
    `;
  }

  private _instanceName(): string {
    if (!this.hass || !this.related) return "Wake Alarm";
    // Friendly name of enabled switch is "<instance> Enabled" — strip suffix.
    const name = this.hass.states[this.related.enabled]?.attributes?.friendly_name as
      | string
      | undefined;
    if (!name) return "Wake Alarm";
    return name.replace(/\s+Enabled$/, "");
  }

  private _toggleEnabled = (): void => {
    if (!this.hass || !this.related) return;
    void this.hass.callService("switch", "toggle", { entity_id: this.related.enabled });
  };

  private _toggleDay(day: DayKey): void {
    if (!this.hass || !this.related) return;
    void this.hass.callService("switch", "toggle", {
      entity_id: this.related.days[day],
    });
  }

  private _adjustTime(dh: number, dm: number): void {
    if (!this.hass || !this.related) return;
    const cur = parseTime(this.hass.states[this.related.alarmTime]?.state);
    let h = cur.h + dh;
    let m = cur.m + dm;
    if (m >= 60) { m -= 60; h += 1; }
    if (m < 0) { m += 60; h -= 1; }
    h = ((h % 24) + 24) % 24;
    void this.hass.callService("time", "set_value", {
      entity_id: this.related.alarmTime,
      time: `${pad(h)}:${pad(m)}:00`,
    });
  }

  private _snooze = (): void => {
    if (!this.hass || !this.related) return;
    void this.hass.callService("button", "press", {
      entity_id: this.related.buttons.snooze,
    });
  };

  private _dismiss = (): void => {
    if (!this.hass || !this.related) return;
    void this.hass.callService("button", "press", {
      entity_id: this.related.buttons.dismiss,
    });
  };

  private _goSettings = (): void => {
    this.dispatchEvent(
      new CustomEvent("navigate-settings", { bubbles: true, composed: true }),
    );
  };

  static styles = [
    sharedStyles,
    css`
      .mode-tile {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        border-radius: var(--wa-radius);
        cursor: pointer;
        transition: background 0.15s ease;
      }
      .mode-tile ha-icon {
        --mdc-icon-size: 36px;
      }
      .mode-text { display: flex; flex-direction: column; gap: 2px; }
      .mode-label { font-size: 1rem; font-weight: 500; }
      .mode-next { font-size: 0.85rem; color: var(--secondary-text-color); }

      .mode-off {
        background: var(--ha-card-background, var(--card-background-color));
        border: 1px solid var(--divider-color);
      }
      .mode-off ha-icon { color: var(--disabled-text-color); }
      .mode-idle {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.12);
      }
      .mode-idle ha-icon { color: var(--primary-color); }
      .mode-ramping {
        background: rgba(255, 165, 0, 0.18);
      }
      .mode-ramping ha-icon { color: rgb(255, 165, 0); }
      .mode-playing {
        background: rgba(76, 175, 80, 0.20);
      }
      .mode-playing ha-icon { color: rgb(76, 175, 80); }
      .mode-snoozing {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.20);
      }
      .mode-snoozing ha-icon { color: var(--primary-color); }

      .time-picker {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
      .time-col {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      .time-num {
        font-size: 2.2rem;
        font-variant-numeric: tabular-nums;
        font-weight: 500;
        min-width: 64px;
        text-align: center;
      }
      .time-sep {
        font-size: 2.2rem;
        line-height: 2.2rem;
        color: var(--secondary-text-color);
      }

      .day-chips {
        display: flex;
        gap: 8px;
        justify-content: space-between;
      }
      .chip {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 8px 4px;
        border-radius: var(--wa-radius);
        cursor: pointer;
        font-size: 0.8rem;
        background: var(--ha-card-background, var(--card-background-color));
        border: 1px solid var(--divider-color);
        user-select: none;
      }
      .chip-on ha-icon { color: rgb(76, 175, 80); }
      .chip-off ha-icon { color: var(--disabled-text-color); }
      .chip-on { border-color: rgba(76, 175, 80, 0.4); }
    `,
  ];
}

const ICONS: Record<string, string> = {
  idle: "mdi:alarm",
  ramping: "mdi:weather-sunset-up",
  playing: "mdi:music-note",
  snoozing: "mdi:alarm-snooze",
  off: "mdi:alarm-off",
};

const LABELS: Record<DayKey, string> = {
  mon: "Mon",
  tue: "Tue",
  wed: "Wed",
  thu: "Thu",
  fri: "Fri",
  sat: "Sat",
  sun: "Sun",
};

function labelForFsmState(s: string): string {
  switch (s) {
    case "ramping": return "Ramping";
    case "playing": return "Playing";
    case "snoozing": return "Snoozing";
    default: return "On";
  }
}

function parseTime(raw: string | undefined): { h: number; m: number } {
  if (!raw) return { h: 7, m: 0 };
  const m = /^(\d{1,2}):(\d{1,2})/.exec(raw);
  if (!m) return { h: 7, m: 0 };
  return { h: parseInt(m[1]!, 10), m: parseInt(m[2]!, 10) };
}

function pad(n: number): string {
  return n.toString().padStart(2, "0");
}

function formatNext(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  const opts: Intl.DateTimeFormatOptions = {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  };
  return new Intl.DateTimeFormat(undefined, opts).format(dt);
}
