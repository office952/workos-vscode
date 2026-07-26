/**
 * Shared Day/Night chrome recipes for forms, tabs, and honesty banners.
 * Prefer these over night-only slate/blue-900 opacity stacks on light surfaces.
 */

export const chromeForm = {
  label:
    "mb-1 block text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary",
  helper: "text-[11px] text-wo-text-muted",
  input:
    "rounded border border-wo-border-subtle bg-wo-surface-input px-3 py-2 text-[13px] text-wo-text-primary placeholder:text-wo-text-muted outline-none focus:border-primary focus:ring-1 focus:ring-[hsl(var(--wo-focus-ring))] disabled:cursor-not-allowed disabled:bg-wo-surface-inset disabled:text-wo-text-muted disabled:opacity-70",
} as const;

export const chromeTab = {
  active:
    "border border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-600/50 dark:bg-blue-600/20 dark:text-blue-300",
  inactive:
    "border border-transparent text-wo-text-secondary hover:bg-wo-hover hover:text-wo-text-primary",
  pillActive:
    "border border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-600/50 dark:bg-blue-600/20 dark:text-blue-300",
  pillInactive:
    "border border-wo-border-strong bg-transparent text-wo-text-secondary hover:border-wo-border-strong hover:bg-wo-hover hover:text-wo-text-primary",
  catalogActive:
    "border border-cyan-300 bg-cyan-50 text-cyan-800 dark:border-cyan-700/50 dark:bg-cyan-900/30 dark:text-cyan-200",
  catalogInactive:
    "border border-wo-border-strong bg-transparent text-wo-text-secondary hover:bg-wo-hover hover:text-wo-text-primary",
} as const;

export const chromeBanner = {
  info: "border border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800/40 dark:bg-blue-900/25 dark:text-blue-200",
  warning:
    "border border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800/40 dark:bg-amber-900/25 dark:text-amber-200",
  error:
    "border border-red-200 bg-red-50 text-red-800 dark:border-red-800/40 dark:bg-red-900/25 dark:text-red-200",
  neutral:
    "border border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary",
} as const;
