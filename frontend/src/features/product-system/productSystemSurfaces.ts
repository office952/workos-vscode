/**
 * Product System content surfaces — aliases to WorkOS tokens.
 * Shell stays on app chrome; PS content uses at most 2 surface depths.
 *
 * Canonical tokens: frontend/src/components/workos/design-system/tokens.ts
 *   surface #111827 · surfaceRaised #1A2236 · input #0B1220
 *   borders subtle #1E293B · strong #2A3548
 * Shared map: docs/qa/.../PRODUCT_SYSTEM_P1_SHARED_VISUAL_MAP.md
 *
 * Tailwind needs full literal class strings at build time — hexes below
 * equal WorkOS tokens. Do not invent a separate PS palette.
 */

/** Opaque content panel (L1) — matches Settings / Quotes cards. */
export const PS_SURFACE_PANEL =
  "rounded-lg border border-[#1E293B] bg-[#111827]";

/** Nested support inside a panel (L2 max) — WorkOS raised wash. */
export const PS_SURFACE_INSET =
  "rounded-md border border-[#2A3548]/60 bg-[#1A2236]/40";

/** Row / list item inside a panel — border only; no third dark well. */
export const PS_SURFACE_ROW =
  "rounded-md border border-[#2A3548]/55 bg-transparent";

/** Form control fill — WorkOS input. */
export const PS_SURFACE_INPUT =
  "rounded border border-[#2A3548] bg-[#0B1220] text-slate-200 outline-none focus:border-blue-500/50";

/** Quiet diagnostic / secondary chrome — not a deeper black stack. */
export const PS_SURFACE_QUIET =
  "rounded-md border border-slate-800/70 bg-slate-900/25";
