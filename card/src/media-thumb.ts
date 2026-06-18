/**
 * Square media thumbnail with robust loading.
 *
 * Encapsulates the #19 broken-artwork fixes in one place, used by both the
 * media-browser grid and the settings selected-media preview:
 *   - signs HA proxy URLs (via resolveThumbnailUrl) so they don't 403 / trip
 *     mixed-content blocking;
 *   - holds a fixed 1:1 box so a non-square or slow-loading image can't
 *     collapse the tile into a sliver;
 *   - falls back to an icon placeholder when there's no artwork or the image
 *     fails to load.
 *
 * Size by setting `width` on the element from the host context; the 1:1
 * aspect-ratio keeps it square.
 */
import {
  LitElement,
  css,
  html,
  type PropertyValues,
  type TemplateResult,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { resolveThumbnailUrl } from "./media-image";
import type { HomeAssistant } from "./types";

@customElement("wake-alarm-thumb")
export class WakeAlarmThumb extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property({ attribute: false }) public thumbnail?: string | null;
  @property() public icon = "mdi:music";

  @state() private _src?: string;
  @state() private _failed = false;

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("thumbnail") || changed.has("hass")) {
      void this._resolve();
    }
  }

  private async _resolve(): Promise<void> {
    const thumb = this.thumbnail;
    this._failed = false;
    this._src = undefined;
    if (!thumb || !this.hass) return;
    const url = await resolveThumbnailUrl(this.hass, thumb);
    // A newer thumbnail may have been assigned while we awaited signing.
    if (this.thumbnail === thumb) this._src = url;
  }

  protected render(): TemplateResult {
    if (this._src && !this._failed) {
      return html`<img
        src=${this._src}
        alt=""
        loading="lazy"
        @error=${this._onError}
      />`;
    }
    return html`<div class="placeholder">
      <ha-icon icon=${this.icon}></ha-icon>
    </div>`;
  }

  private _onError = (): void => {
    this._failed = true;
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
      aspect-ratio: 1 / 1;
      border-radius: 6px;
      overflow: hidden;
      background: var(--card-background-color);
    }
    img,
    .placeholder {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--secondary-text-color);
    }
  `;
}
