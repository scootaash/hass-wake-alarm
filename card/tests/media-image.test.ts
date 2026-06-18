import { describe, expect, it, vi } from "vitest";
import { resolveThumbnailUrl } from "../src/media-image";
import type { HomeAssistant } from "../src/types";

/** Minimal hass whose auth/sign_path echoes the path with a fake signature. */
function makeHass(
  sign: (path: string) => Promise<{ path: string }> = (path) =>
    Promise.resolve({ path: `${path}${path.includes("?") ? "&" : "?"}authSig=sig` }),
): { hass: HomeAssistant; calls: string[] } {
  const calls: string[] = [];
  const hass = {
    callWS: vi.fn(async (msg: { type: string; path?: string }) => {
      expect(msg.type).toBe("auth/sign_path");
      calls.push(msg.path!);
      return sign(msg.path!);
    }),
  } as unknown as HomeAssistant;
  return { hass, calls };
}

describe("resolveThumbnailUrl", () => {
  it("signs a relative HA proxy path", async () => {
    const { hass, calls } = makeHass();
    const out = await resolveThumbnailUrl(hass, "/api/media_player_proxy/x.jpg");
    expect(calls).toEqual(["/api/media_player_proxy/x.jpg"]);
    expect(out).toBe("/api/media_player_proxy/x.jpg?authSig=sig");
  });

  it("preserves an existing query string when signing", async () => {
    const { hass } = makeHass();
    const out = await resolveThumbnailUrl(hass, "/api/image/x?width=512");
    expect(out).toBe("/api/image/x?width=512&authSig=sig");
  });

  it("reduces an absolute HA url to its path and signs it (fixes mixed content)", async () => {
    const { hass, calls } = makeHass();
    const out = await resolveThumbnailUrl(
      hass,
      "http://192.168.1.5:8123/api/media_player_proxy/x.jpg?token=abc",
    );
    expect(calls).toEqual(["/api/media_player_proxy/x.jpg?token=abc"]);
    expect(out).toBe("/api/media_player_proxy/x.jpg?token=abc&authSig=sig");
  });

  it("leaves an external (non-/api) absolute url unchanged and does not sign", async () => {
    const { hass, calls } = makeHass();
    const url = "https://i.scdn.co/image/abc123.jpg";
    expect(await resolveThumbnailUrl(hass, url)).toBe(url);
    expect(calls).toEqual([]);
    expect(hass.callWS).not.toHaveBeenCalled();
  });

  it("leaves a data: uri unchanged", async () => {
    const { hass } = makeHass();
    const url = "data:image/png;base64,AAAA";
    expect(await resolveThumbnailUrl(hass, url)).toBe(url);
    expect(hass.callWS).not.toHaveBeenCalled();
  });

  it("falls back to the path when signing fails", async () => {
    const hass = {
      callWS: vi.fn(async () => {
        throw new Error("unauthorized");
      }),
    } as unknown as HomeAssistant;
    const out = await resolveThumbnailUrl(hass, "/api/media_player_proxy/x.jpg");
    expect(out).toBe("/api/media_player_proxy/x.jpg");
  });
});
