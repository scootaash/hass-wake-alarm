/**
 * Minimal media browser for the wake-alarm card.
 *
 * Uses HA's media_player/browse_media WebSocket command directly so we
 * don't depend on <ha-media-player-browse> being lazy-loaded into the
 * dashboard scope (which is HA-version-dependent and the cause of the
 * original "media select doesn't work" bug).
 *
 * Public API:
 *   <wake-alarm-media-browser .hass=${hass} .entityId=${player}>
 *     fires "media-picked" with detail.item = MediaPickedItem when the
 *     user picks a playable child.
 */
import { LitElement, css, html, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import "./media-thumb";
import type { HomeAssistant, MediaPickedItem } from "./types";

interface MediaItem {
  media_content_id: string;
  media_content_type: string;
  title: string;
  thumbnail?: string | null;
  can_play?: boolean;
  can_expand?: boolean;
}

interface BrowseResponse extends MediaItem {
  children?: MediaItem[];
}

interface BreadcrumbEntry {
  contentId?: string;
  contentType?: string;
  title: string;
}

@customElement("wake-alarm-media-browser")
export class WakeAlarmMediaBrowser extends LitElement {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @property() public entityId?: string;

  @state() private _children: MediaItem[] = [];
  @state() private _path: BreadcrumbEntry[] = [];
  @state() private _loading = false;
  @state() private _error?: string;

  protected firstUpdated(): void {
    void this._navigate(undefined, undefined, "Library");
  }

  private async _navigate(
    contentId: string | undefined,
    contentType: string | undefined,
    title: string,
  ): Promise<void> {
    if (!this.hass || !this.entityId) return;
    this._loading = true;
    this._error = undefined;
    try {
      const msg = {
        type: "media_player/browse_media",
        entity_id: this.entityId,
        ...(contentId !== undefined ? { media_content_id: contentId } : {}),
        ...(contentType !== undefined
          ? { media_content_type: contentType }
          : {}),
      };
      const result = await this.hass.callWS<BrowseResponse>(msg);
      this._children = result.children ?? [];
      this._path = [
        ...this._path,
        { contentId, contentType, title: result.title || title },
      ];
    } catch (e) {
      this._error = `${e}`;
    } finally {
      this._loading = false;
    }
  }

  private async _back(): Promise<void> {
    if (this._path.length <= 1) return;
    // Drop the current crumb; navigate to the previous one.
    const next = this._path.slice(0, -1);
    const target = next[next.length - 1]!;
    this._path = next.slice(0, -1);
    await this._navigate(target.contentId, target.contentType, target.title);
  }

  private _onItemClick(item: MediaItem): void {
    if (item.can_expand) {
      void this._navigate(
        item.media_content_id,
        item.media_content_type,
        item.title,
      );
      return;
    }
    if (item.can_play) {
      const detail: MediaPickedItem = {
        media_content_id: item.media_content_id,
        media_content_type: item.media_content_type,
        title: item.title,
        thumbnail: item.thumbnail ?? undefined,
      };
      this.dispatchEvent(
        new CustomEvent("media-picked", {
          detail: { item: detail },
          bubbles: true,
          composed: true,
        }),
      );
    }
  }

  protected render(): TemplateResult {
    const breadcrumb = this._path.map((p) => p.title).join(" › ") || "Library";
    return html`
      <div class="toolbar">
        <button
          class="back"
          ?disabled=${this._path.length <= 1}
          @click=${this._back}
        >
          <ha-icon icon="mdi:arrow-left"></ha-icon>
        </button>
        <div class="crumb" title=${breadcrumb}>${breadcrumb}</div>
      </div>

      ${this._error
        ? html`<div class="error">Failed to browse: ${this._error}</div>`
        : null}
      ${this._loading
        ? html`<div class="loading">Loading…</div>`
        : html`
            <div class="grid">
              ${this._children.length === 0
                ? html`<div class="empty">Nothing to show.</div>`
                : this._children.map((c) => this._renderItem(c))}
            </div>
          `}
    `;
  }

  private _renderItem(item: MediaItem): TemplateResult {
    const playable = !!item.can_play;
    const expandable = !!item.can_expand;
    const cls = `tile ${playable ? "playable" : ""} ${expandable ? "expandable" : ""}`;
    return html`
      <div class=${cls} @click=${() => this._onItemClick(item)} role="button" tabindex="0">
        <wake-alarm-thumb
          .hass=${this.hass}
          .thumbnail=${item.thumbnail}
          icon=${expandable ? "mdi:folder-music" : "mdi:music"}
        ></wake-alarm-thumb>
        <div class="title" title=${item.title}>${item.title}</div>
      </div>
    `;
  }

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 0;
      /* Opaque so the settings view behind the modal doesn't show through. */
      background: var(--card-background-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-bottom: 1px solid var(--divider-color);
    }
    .toolbar .back {
      background: none;
      border: none;
      cursor: pointer;
      color: inherit;
      padding: 4px;
    }
    .toolbar .back[disabled] {
      opacity: 0.4;
      cursor: not-allowed;
    }
    .crumb {
      flex: 1;
      font-size: 0.95rem;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 12px;
      padding: 12px;
      overflow-y: auto;
      flex: 1;
    }
    .tile {
      display: flex;
      flex-direction: column;
      gap: 6px;
      cursor: pointer;
      border-radius: 8px;
      overflow: hidden;
      background: var(--secondary-background-color);
      padding: 8px;
      user-select: none;
    }
    .tile:hover { background: var(--ha-card-background, var(--card-background-color)); }
    .tile .title {
      font-size: 0.85rem;
      line-height: 1.2;
      max-height: 2.4em;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
    .tile.playable { outline: 1px solid rgba(76, 175, 80, 0.3); }
    .empty,
    .loading,
    .error {
      padding: 16px;
      color: var(--secondary-text-color);
    }
    .error { color: var(--error-color, rgb(255, 82, 82)); }
  `;
}
