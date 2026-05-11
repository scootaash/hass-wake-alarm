import { LitElement, css, html, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { sharedStyles } from "./styles";
import { DAYS, type DayKey, type HomeAssistant, type RelatedEntities } from "./types";

@customElement("wake-alarm-main-view")
export class WakeAlarmMainView extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public related?: RelatedEntities;

  private _tickInterval?: number;

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stopTicker();
  }

  protected updated(): void {
    // Only tick while we're actually showing a snooze countdown. Stops
    // a 1Hz no-op render loop running for the lifetime of the card on
    // every dashboard. Lifecycle: ticker starts the first render that
    // sees fsmState==="snoozing" and stops the next render where it
    // isn't (e.g. snooze finishes, dismiss, etc.).
    const fsmState =
      this.hass && this.related
        ? this.hass.states[this.related.sensors.state]?.state
        : undefined;
    if (fsmState === "snoozing") {
      this._startTicker();
    } else {
      this._stopTicker();
    }
  }

  private _startTicker(): void {
    if (this._tickInterval !== undefined) return;
    this._tickInterval = window.setInterval(() => this.requestUpdate(), 1000);
  }

  private _stopTicker(): void {
    if (this._tickInterval !== undefined) {
      window.clearInterval(this._tickInterval);
      this._tickInterval = undefined;
    }
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

    const snoozeUntilRaw = stateState?.attributes?.snooze_until as
      | string
      | null
      | undefined;
    const snoozeCountdown =
      fsmState === "snoozing" && snoozeUntilRaw
        ? formatCountdown(snoozeUntilRaw)
        : null;

    const nextLabel = snoozeCountdown
      ? `Music in ${snoozeCountdown}`
      : nextAlarmState?.state && nextAlarmState.state !== "unknown"
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

        <div class="mode-tile mode-${isEnabled ? fsmState : "off"}" @click=${this._handleModeTileClick}>
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

        ${isActive ? this._renderActiveActions(fsmState) : null}
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

  private _renderActiveActions(fsmState: string): TemplateResult {
    return html`
      <div class="action-row">
        ${fsmState === "ramping"
          ? html`
              <button class="action-btn cancel-ramp" @click=${this._cancelRamp}>
                <ha-icon icon="mdi:weather-sunset-down"></ha-icon>
                <span>Cancel ramp</span>
              </button>
            `
          : null}
        <button class="action-btn snooze" @click=${this._snooze}>
          <ha-icon icon="mdi:alarm-snooze"></ha-icon>
          <span>Snooze</span>
        </button>
        <button class="action-btn dismiss" @click=${this._dismiss}>
          <ha-icon icon="mdi:alarm-off"></ha-icon>
          <span>Dismiss</span>
        </button>
      </div>
    `;
  }

  private _cancelRamp = (): void => {
    if (!this.hass || !this.related) return;
    void this.hass.callService("button", "press", {
      entity_id: this.related.buttons.cancel_ramp,
    });
  };

  private _instanceName(): string {
    if (!this.hass || !this.related) return "Wake Alarm";
    // Integration mirrors the user-given name as an attribute on the
    // next_alarm sensor — use that so the title is locale-safe (we used
    // to strip /\s+Enabled$/ off the friendly_name which only worked in
    // English).
    const sensor = this.hass.states[this.related.sensors.next_alarm];
    const name = sensor?.attributes?.instance_name as string | undefined;
    return name && name.trim() ? name : "Wake Alarm";
  }

  private _toggleEnabled = (): void => {
    if (!this.hass || !this.related) return;
    void this.hass.callService("switch", "toggle", { entity_id: this.related.enabled });
  };

  private _handleModeTileClick = (): void => {
    // While the alarm is active (ramping / playing / snoozing) tapping
    // the mode tile shouldn't disarm the alarm — the user is likely
    // reading a countdown or status, not trying to flip it off. The
    // Snooze + Dismiss buttons (and Cancel ramp during ramping) handle
    // those actions explicitly.
    if (!this.hass || !this.related) return;
    const fsm = this.hass.states[this.related.sensors.state]?.state;
    if (fsm && fsm !== "idle") return;
    this._toggleEnabled();
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

      /* Snooze + Dismiss share the mode-tile vibe: tall, prominent,
         half-width each so they line up under the mode tile. */
      .action-row {
        display: flex;
        gap: 12px;
      }
      .action-btn {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 16px;
        border-radius: var(--wa-radius);
        border: 1px solid var(--divider-color);
        background: var(--ha-card-background, var(--card-background-color));
        color: var(--primary-text-color);
        font-size: 1rem;
        font-weight: 500;
        font-family: inherit;
        cursor: pointer;
        transition: background 0.15s ease;
      }
      .action-btn:hover { background: var(--secondary-background-color); }
      .action-btn ha-icon { --mdc-icon-size: 32px; }
      .action-btn.snooze {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.14);
      }
      .action-btn.snooze ha-icon { color: var(--primary-color); }
      .action-btn.dismiss {
        background: rgba(255, 82, 82, 0.14);
        color: rgb(255, 82, 82);
      }
      .action-btn.dismiss ha-icon { color: rgb(255, 82, 82); }
      .action-btn.cancel-ramp {
        background: rgba(255, 165, 0, 0.16);
      }
      .action-btn.cancel-ramp ha-icon { color: rgb(255, 165, 0); }
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

function formatCountdown(iso: string): string {
  const target = new Date(iso).getTime();
  if (Number.isNaN(target)) return iso;
  const remaining = Math.max(0, Math.round((target - Date.now()) / 1000));
  const min = Math.floor(remaining / 60);
  const sec = remaining % 60;
  return `${min}:${pad(sec)}`;
}
