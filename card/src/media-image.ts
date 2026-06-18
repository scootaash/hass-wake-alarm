/**
 * Resolve a media thumbnail URL into something an <img> can actually load.
 *
 * Music Assistant (and other media providers) return artwork as Home Assistant
 * proxy paths like "/api/media_player_proxy/...". Those require an auth
 * signature to load in an <img> tag (which can't send the auth header) —
 * otherwise HA returns 403 (the broken artwork in #19). Signing via
 * auth/sign_path also yields an origin-relative URL, so it resolves against the
 * current (https) dashboard origin instead of a bare http://<ip>, which fixes
 * the mixed-content blocking reported for artist artwork.
 *
 * Handling:
 *   - "/api/..." (relative)            → sign, return signed path
 *   - "http(s)://host/api/..." (HA)    → reduce to path, sign, return signed
 *   - "http(s)://cdn/..." (external)   → return unchanged
 *   - "data:..." / anything else       → return unchanged
 * If signing fails, fall back to the (origin-relative) path so the <img>'s
 * own error handling can take over.
 */
import type { HomeAssistant } from "./types";

export async function resolveThumbnailUrl(
  hass: HomeAssistant,
  thumbnail: string,
): Promise<string> {
  let path = thumbnail;

  if (/^https?:\/\//i.test(thumbnail)) {
    // Absolute URL: only HA's own /api/ paths can (and need to) be signed;
    // external artwork (Spotify CDN, etc.) is used as-is.
    let parsed: URL;
    try {
      parsed = new URL(thumbnail);
    } catch {
      return thumbnail;
    }
    if (!parsed.pathname.startsWith("/api/")) {
      return thumbnail;
    }
    path = parsed.pathname + parsed.search;
  } else if (!thumbnail.startsWith("/")) {
    // data: URI or some other inline/relative form — leave it alone.
    return thumbnail;
  }

  try {
    const signed = await hass.callWS<{ path: string }>({
      type: "auth/sign_path",
      path,
    });
    return signed.path;
  } catch {
    return path;
  }
}
