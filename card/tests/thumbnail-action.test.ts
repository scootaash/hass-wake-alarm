import { describe, expect, it } from "vitest";
import { thumbnailAction } from "../src/media-image";

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
