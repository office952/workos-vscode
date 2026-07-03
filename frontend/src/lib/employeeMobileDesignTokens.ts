import { cn } from "@/lib/utils";

/** Shared Employee Mobile surface + action tokens. */
export const emSurface = {
  panel: "rounded-xl border border-[#243044] bg-[#0A1020]/80",
  row: "border-b border-[#243044]/80 last:border-b-0",
  muted: "text-slate-400",
  body: "text-slate-200",
} as const;

/** Scrollable page padding above bottom nav + sticky footer. */
export const emMobileScrollPadClass =
  "pb-[calc(7.5rem+env(safe-area-inset-bottom,0px))]";

/** Sticky footer stack above bottom nav. */
export const emStickyFooterClass =
  "fixed bottom-[calc(3.5rem+env(safe-area-inset-bottom,0px))] inset-x-0 z-30 border-t border-[#243044] bg-[#0A1020]/95 backdrop-blur-md px-4 py-3 space-y-2 max-w-lg mx-auto";

export type EmChipTone = "neutral" | "active" | "ready" | "warning";

const CHIP_TONES: Record<EmChipTone, string> = {
  neutral: "bg-slate-700/50 text-slate-300 ring-slate-600/40",
  active: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  ready: "bg-blue-500/15 text-blue-300 ring-blue-500/30",
  warning: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
};

export function emChipClass(tone: EmChipTone = "neutral"): string {
  return cn(
    "shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 leading-none",
    CHIP_TONES[tone],
  );
}

export function emPrimaryButtonClass(compact = false): string {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 font-semibold text-white hover:bg-emerald-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
    compact ? "min-h-[48px] px-4 py-2.5 text-base w-full" : "min-h-[48px] px-4 py-3 text-base w-full",
  );
}

export function emSecondaryLinkClass(): string {
  return "inline-flex min-h-[44px] items-center gap-1.5 px-1 text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors";
}

export function emOutlineAccentClass(): string {
  return "inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl border border-blue-600/50 bg-blue-950/20 px-4 py-2.5 text-base font-semibold text-blue-200 hover:border-blue-500/60 hover:bg-blue-950/40 transition-colors";
}

export function emModuleBadgeClass(): string {
  return "absolute -top-1 -right-1 min-w-[18px] rounded-full bg-slate-600 px-1 text-[11px] font-bold leading-[18px] text-slate-100 text-center";
}

export function emTaskTabClass(active: boolean): string {
  return cn(
    "shrink-0 rounded-full px-4 py-2.5 min-h-[44px] text-sm font-medium border transition-colors",
    active
      ? "bg-emerald-600/20 border-emerald-600/40 text-emerald-200"
      : "bg-[#0A1020]/60 border-[#243044] text-slate-400 hover:text-slate-200",
  );
}
