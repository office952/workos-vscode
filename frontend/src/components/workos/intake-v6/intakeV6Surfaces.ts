/**
 * Intake V6 content surfaces — aliases to WorkOS semantic tokens (R7).
 * Canonical: bg-wo-surface-raised / inset / input + border-wo-border-*.
 * Follows html.light / html.dark via CSS vars in index.css.
 */

/** Opaque content panel */
export const IV6_SURFACE_PANEL =
  "rounded-[10px] border border-wo-border-strong bg-wo-surface-raised";

/** Nested inset wash */
export const IV6_SURFACE_INSET =
  "rounded-md border border-wo-border-strong bg-wo-surface-inset";

/** Form control fill */
export const IV6_SURFACE_INPUT =
  "rounded border border-wo-border-strong bg-wo-surface-input text-wo-text-secondary outline-none focus:border-blue-500/50";

/** Quiet chrome / secondary strip */
export const IV6_SURFACE_QUIET =
  "rounded-md border border-wo-border-subtle bg-wo-surface-inset";
