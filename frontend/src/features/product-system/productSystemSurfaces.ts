/**
 * Product System content surfaces — aliases to WorkOS semantic tokens.
 * Shell stays on app chrome; PS content uses at most 2 surface depths.
 *
 * Canonical: bg-wo-surface-raised / inset / input + border-wo-border-*.
 * Follows html.light / html.dark via CSS vars in index.css (R4 Day honesty).
 * Shared map: docs/qa/.../PRODUCT_SYSTEM_P1_SHARED_VISUAL_MAP.md
 *
 * Tailwind needs full literal class strings at build time.
 * Do not invent a separate PS palette.
 */

/** Opaque content panel (L1) — matches Settings / Quotes cards. */
export const PS_SURFACE_PANEL =
  "rounded-lg border border-wo-border-subtle bg-wo-surface-raised";

/** Nested support inside a panel (L2 max) — inset wash. */
export const PS_SURFACE_INSET =
  "rounded-md border border-wo-border-strong bg-wo-surface-inset";

/** Row / list item inside a panel — border only; no third dark well. */
export const PS_SURFACE_ROW =
  "rounded-md border border-wo-border-strong bg-transparent";

/** Form control fill — WorkOS input. */
export const PS_SURFACE_INPUT =
  "rounded border border-wo-border-strong bg-wo-surface-input text-wo-text-primary outline-none focus:border-blue-500/50";

/** Quiet diagnostic / secondary chrome — not a deeper black stack. */
export const PS_SURFACE_QUIET =
  "rounded-md border border-wo-border-subtle bg-wo-surface-inset";
