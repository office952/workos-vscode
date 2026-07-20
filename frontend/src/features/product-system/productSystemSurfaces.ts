/**
 * Product System content surfaces — WorkOS tokens, fewer nested dark levels.
 * Shell stays on app chrome; PS content uses at most ~2 surface depths.
 */

/** Primary content panel (level 1) — lighter than historic #0B1220 / #0D1321 stacks. */
export const PS_SURFACE_PANEL =
  "rounded-xl border border-slate-700/50 bg-[#111827]/70";

/** Nested inset inside a panel (level 2 max) — no third dark box. */
export const PS_SURFACE_INSET =
  "rounded-lg border border-slate-700/40 bg-[#1A2236]/35";

/** Quiet diagnostic / secondary chrome. */
export const PS_SURFACE_QUIET = "rounded-lg border border-slate-800/60 bg-slate-900/30";
