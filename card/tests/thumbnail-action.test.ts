import { describe, expect, it } from "vitest";
import { shouldResign, thumbnailAction } from "../src/media-image";

describe("thumbnailAction", () => {
  it("resolves new artwork", () => {
    expect(thumbnailAction("/api/a.jpg", undefined)).toBe("resolve");
    expect(thumbnailAction("/api/b.jpg", "/api/a.jpg")).toBe("resolve");
  });

  it("is a no-op when the thumbnail is unchanged (the #19 flicker fix)", () => {
    // This is the case that fires on every hass state update.
    expect(thumbnailAction("/api/a.jpg", "/api/a.jpg")).toBe("none");
  });

  it("is a no-op when there is no artwork and none was resolved", () => {
    expect(thumbnailAction(undefined, undefined)).toBe("none");
    expect(thumbnailAction(null, undefined)).toBe("none");
    expect(thumbnailAction("", undefined)).toBe("none");
  });

  it("clears a stale image when artwork is removed", () => {
    expect(thumbnailAction(undefined, "/api/a.jpg")).toBe("clear");
    expect(thumbnailAction(null, "/api/a.jpg")).toBe("clear");
  });
});

describe("shouldResign", () => {
  const signed = "/api/a.jpg?authSig=old";

  it("retries an expired signed URL once", () => {
    // Signed when the list rendered, loaded lazily > 30 s later: 401.
    expect(shouldResign("/api/a.jpg", signed, undefined)).toBe(true);
    expect(shouldResign("/api/a.jpg", "/api/a.jpg?x=1&authSig=old", undefined)).toBe(
      true,
    );
  });

  it("gives up after one retry, so broken artwork falls back to the icon", () => {
    expect(shouldResign("/api/a.jpg", signed, "/api/a.jpg")).toBe(false);
  });

  it("still retries a different thumbnail on a reused tile", () => {
    expect(shouldResign("/api/b.jpg", "/api/b.jpg?authSig=old", "/api/a.jpg")).toBe(
      true,
    );
  });

  it("doesn't retry an unsigned URL, which can't have expired", () => {
    const cdn = "https://cdn.example/a.jpg";
    expect(shouldResign(cdn, cdn, undefined)).toBe(false);
    // Signing failed and resolveThumbnailUrl fell back to the bare path.
    expect(shouldResign("/api/a.jpg", "/api/a.jpg", undefined)).toBe(false);
  });

  it("doesn't retry without artwork", () => {
    expect(shouldResign(undefined, signed, undefined)).toBe(false);
    expect(shouldResign("/api/a.jpg", undefined, undefined)).toBe(false);
  });
});
