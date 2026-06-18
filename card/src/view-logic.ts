/**
 * Small pure view-logic helpers with no Lit / DOM dependency, so they can be
 * unit-tested in the plain-node vitest environment (mirrors the integration's
 * `_pure.py`). Keep anything that touches `customElements` / rendering out.
 */

/**
 * Whether the media-only controls (the Media picker section, "Test music" and
 * "Test urgent notification" buttons) should be shown.
 *
 * False for a lights-only alarm (no media players configured, #22 / #46):
 * those controls are dead — `test_music` no-ops server-side and `test_urgent`
 * has no real speaker to name — so hiding them avoids confusing the user.
 */
export function showsMediaControls(players: readonly string[] | undefined): boolean {
  return !!players && players.length > 0;
}
