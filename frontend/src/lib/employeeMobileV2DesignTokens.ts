import { cn } from "@/lib/utils";
import { v2IconGlowClass, v2Motion } from "@/lib/employeeMobileV2Effects";
import type { PipelineRowVisualState } from "@/lib/employeeMobileV2Status";
export const emV2Surface = {
  page: "bg-[#0B1120]",
  panel: "rounded-2xl border border-[#1E293B] bg-[#111827]",
  row: "rounded-[10px] border border-[#1E293B] bg-[#111827]",
} as const;

export const emV2ScrollPad =
  "pb-[calc(5rem+env(safe-area-inset-bottom,0px))]";

/** Pipeline: legend + CTA clearance above fixed bottom nav. */
export const emV2PipelineScrollPad =
  "pb-[calc(6.5rem+env(safe-area-inset-bottom,0px))]";

export const emV2ShellPad =
  "px-4 pt-3 pb-[calc(5rem+env(safe-area-inset-bottom,0px))]";

/** Task detail: bottom nav + sticky action stack clearance. */
export const emV2TaskDetailScrollPad =
  "pb-[calc(11rem+env(safe-area-inset-bottom,0px))]";

export type EmV2ModuleAccent = "blue" | "violet" | "amber" | "red" | "slate" | "emerald";

const MODULE_ICON_BG: Record<EmV2ModuleAccent, string> = {
  blue: "bg-blue-500/12 text-blue-400",
  violet: "bg-violet-500/12 text-violet-400",
  amber: "bg-amber-500/12 text-amber-400",
  red: "bg-red-500/12 text-red-400",
  slate: "bg-slate-500/10 text-slate-400",
  emerald: "bg-emerald-500/12 text-emerald-400",
};

export function emV2ModuleIconClass(accent: EmV2ModuleAccent = "slate"): string {
  return cn(
    "flex h-10 w-10 items-center justify-center rounded-xl",
    MODULE_ICON_BG[accent],
    v2IconGlowClass(accent),
  );
}

export const emV2Controls = {
  segmentedTabs:
    "flex w-full min-h-[44px] items-stretch rounded-lg border border-[#1E293B] bg-[#0B1120] p-0.5",
  segmentedTab:
    "flex flex-1 min-h-[44px] items-center justify-center rounded-md px-2 text-[13px] font-medium text-slate-400 transition-colors",
  segmentedTabActive: "bg-[#1A2332] text-slate-100 shadow-sm",
  segmentedTabLink: "text-slate-400 hover:text-slate-200",
  segmentedOverflow:
    "flex shrink-0 min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-slate-400 hover:bg-[#1A2332] hover:text-slate-200",
  statusIndicator: "flex shrink-0 flex-col items-end gap-0.5 text-right max-w-[42%]",
  statusIconRow: "inline-flex items-center gap-1 text-[12px] font-medium leading-none",
  statusDetail: "text-[11px] text-slate-500 leading-tight line-clamp-1",
  pipelineLegend:
    "flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-xl border border-[#1E293B]/60 bg-[#0B1120]/50 px-3 py-2",
  pipelineLegendLabel: "text-[11px] font-medium text-slate-500",
  pipelineLegendItem: "inline-flex items-center gap-1.5 text-[11px] text-slate-400",
  pipelineVerticalRow:
    "relative flex w-full items-stretch gap-2 border-b border-[#1E293B]/80 px-2.5 py-2.5 text-left min-h-[56px] last:border-b-0 transition-colors",
  pipelineVerticalRowCurrent: "bg-emerald-500/[0.05]",
  pipelineVerticalRowBlocked: "bg-rose-500/[0.05]",
  pipelineVerticalRowCompleted: "bg-emerald-950/25",
  pipelineVerticalRowWaiting: "",
  pipelineVerticalRowAltPost: "opacity-70",
  pipelineVerticalAxis: "flex w-7 shrink-0 flex-col items-center self-stretch py-0.5",
  pipelineVerticalLine: "w-px flex-1 min-h-[4px] bg-slate-700/45",
  pipelineVerticalLineHidden: "opacity-0",
  pipelineAxisMarkerBase:
    "relative z-[1] flex shrink-0 items-center justify-center rounded-full border",
  pipelineAxisMarkerCurrent:
    "h-6 w-6 border-emerald-500/55 bg-emerald-500/12 text-emerald-400 shadow-[0_0_0_3px_rgba(16,185,129,0.08)]",
  pipelineCurrentMarkerPulseRing:
    "pointer-events-none absolute inset-0 rounded-full border border-emerald-500/30 bg-emerald-500/[0.08] motion-safe:animate-ping motion-safe:[animation-duration:2.25s] motion-safe:[animation-timing-function:ease-in-out] motion-reduce:hidden",
  pipelineAxisMarkerCompleted:
    "h-5 w-5 border-emerald-600/45 bg-emerald-950/50 text-emerald-500/85",
  pipelineAxisMarkerBlocked:
    "h-5 w-5 border-rose-500/50 bg-rose-950/35 text-rose-400",
  pipelineAxisMarkerWaiting:
    "h-5 w-5 border-amber-500/35 bg-amber-950/15 text-amber-500/80",
  pipelineAxisMarkerUpcoming:
    "h-5 w-5 border-blue-500/35 bg-slate-900/80 text-blue-400/80",
  pipelineAxisMarkerAltPost: "h-4 w-4 border-transparent bg-transparent text-slate-600",
  pipelineAxisMarkerNeutral: "h-3.5 w-3.5 border-slate-600/80 bg-slate-800 text-slate-500",
  pipelineAxisMarkerLegend:
    "h-4 w-4 shrink-0 border text-[0px]",
  pipelineStepLabel: "text-[11px] font-semibold leading-none tracking-wide",
  pipelineStepLabelCurrent: "text-emerald-400",
  pipelineStepLabelCompleted: "text-emerald-500/80",
  pipelineStepLabelBlocked: "text-rose-400/90",
  pipelineStepLabelWaiting: "text-slate-500",
  pipelineStepLabelUpcoming: "text-blue-400/75",
  pipelineStepLabelAltPost: "text-slate-600",
  pipelineStepLabelNeutral: "text-slate-500",
  pipelineAltPostBadge:
    "ml-1.5 inline-flex rounded px-1 py-px text-[9px] font-medium uppercase tracking-wide text-slate-600 ring-1 ring-slate-700/60",
  pipelineTitleCurrent: "text-slate-100",
  pipelineTitleNeutral: "text-slate-100",
  pipelineTitleWaiting: "text-slate-100",
  pipelineTitleBlocked: "text-rose-100/95",
  pipelineTitleCompleted: "text-slate-400",
  pipelineTitleAltPost: "text-slate-500",
  pipelineSubtextDefault: "text-slate-500",
  pipelineSubtextCompleted: "text-slate-500",
  pipelineSubtextAltPost: "text-slate-600",
  pipelineSubtextBlocked: "text-rose-300/80",
  pipelineSubtextWaiting: "text-amber-400/70",
  pipelineChevronNeutral: "h-4 w-4 shrink-0 self-center text-slate-500",
  pipelineChevronCurrent: "h-4 w-4 shrink-0 self-center text-emerald-400/80",
  pipelineRowHoverTappable: "hover:bg-[#1A2332]/35",
  actionGroup: "flex flex-col gap-2",
  actionSecondaryRow: "flex items-center justify-between gap-3 min-h-[44px]",
  primaryAction:
    "inline-flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 text-[15px] font-semibold text-white hover:bg-blue-500 transition-[transform,background-color] duration-150 ease-out active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
  secondaryAction:
    "inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg px-2 text-[13px] font-medium text-slate-400 hover:text-slate-200 transition-colors active:scale-[0.98]",
  textAction:
    "inline-flex min-h-[44px] items-center gap-1.5 text-[13px] font-medium text-slate-400 hover:text-blue-300 transition-colors",
  destructiveTextAction:
    "inline-flex min-h-[44px] items-center gap-1.5 text-[13px] font-medium text-amber-400/90 hover:text-amber-300 transition-colors",
  attentionLine:
    "inline-flex items-center gap-1.5 text-[11px] leading-snug text-amber-300/85",
  attentionDot: "absolute top-3 right-3 h-2 w-2 rounded-full bg-blue-500 ring-2 ring-[#111827]",
} as const;

export function pipelineVerticalRowStateClass(state: PipelineRowVisualState): string {
  const map: Record<PipelineRowVisualState, string> = {
    current: emV2Controls.pipelineVerticalRowCurrent,
    blocked: emV2Controls.pipelineVerticalRowBlocked,
    completed: emV2Controls.pipelineVerticalRowCompleted,
    waiting: emV2Controls.pipelineVerticalRowWaiting,
    upcoming: "",
    "alt-post": emV2Controls.pipelineVerticalRowAltPost,
    neutral: "",
  };
  return map[state];
}

export function pipelineAxisMarkerClass(state: PipelineRowVisualState): string {
  const map: Record<PipelineRowVisualState, string> = {
    current: emV2Controls.pipelineAxisMarkerCurrent,
    blocked: emV2Controls.pipelineAxisMarkerBlocked,
    completed: emV2Controls.pipelineAxisMarkerCompleted,
    waiting: emV2Controls.pipelineAxisMarkerWaiting,
    upcoming: emV2Controls.pipelineAxisMarkerUpcoming,
    "alt-post": emV2Controls.pipelineAxisMarkerAltPost,
    neutral: emV2Controls.pipelineAxisMarkerNeutral,
  };
  return cn(emV2Controls.pipelineAxisMarkerBase, map[state]);
}

export function pipelineStepLabelClass(state: PipelineRowVisualState): string {
  const map: Record<PipelineRowVisualState, string> = {
    current: emV2Controls.pipelineStepLabelCurrent,
    blocked: emV2Controls.pipelineStepLabelBlocked,
    completed: emV2Controls.pipelineStepLabelCompleted,
    waiting: emV2Controls.pipelineStepLabelWaiting,
    upcoming: emV2Controls.pipelineStepLabelUpcoming,
    "alt-post": emV2Controls.pipelineStepLabelAltPost,
    neutral: emV2Controls.pipelineStepLabelNeutral,
  };
  return cn(emV2Controls.pipelineStepLabel, map[state]);
}

export function pipelineAxisMarkerLegendClass(state: PipelineRowVisualState): string {
  return cn(
    emV2Controls.pipelineAxisMarkerLegend,
    pipelineAxisMarkerClass(state),
  );
}

export function emV2PrimaryButtonClass(): string {
  return cn(emV2Controls.primaryAction, "min-h-[48px]");
}

export function emV2SecondaryButtonClass(): string {
  return cn(
    "inline-flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg",
    "border border-[#1E293B] bg-[#1A2332] text-sm font-medium text-slate-200",
    "hover:border-[#2A3A4E] transition-[transform,border-color,background-color] duration-150 ease-out",
    v2Motion.tapTarget,
  );
}

export function emV2ChipClass(
  tone: "neutral" | "active" | "ready" | "warning" | "waiting" = "neutral",
): string {
  const tones = {
    neutral: "text-slate-400",
    active: "text-emerald-400",
    ready: "text-blue-400",
    warning: "text-amber-400",
    waiting: "text-slate-400",
  };
  return cn("shrink-0 text-[12px] font-medium leading-none", tones[tone]);
}

export function emV2StatusToneClass(
  tone: "neutral" | "active" | "ready" | "warning" | "waiting" = "neutral",
): string {
  const tones = {
    neutral: "text-slate-400",
    active: "text-emerald-400",
    ready: "text-blue-400",
    warning: "text-amber-400",
    waiting: "text-slate-400",
  };
  return tones[tone];
}

export function emV2SectionLabelClass(): string {
  return "text-[12px] font-semibold uppercase tracking-wide text-slate-500";
}

export function emV2TaskRowClass(highlighted = false): string {
  return cn(
    "flex w-full min-h-[64px] items-center gap-3 rounded-[10px] border px-4 py-3.5 text-left",
    v2Motion.cardInteractive,
    highlighted
      ? "border-emerald-500/30 bg-emerald-500/[0.04]"
      : "border-[#1E293B] bg-[#111827] hover:border-[#2A3A4E]",
  );
}

export function buildEmployeeMobileV2TaskPath(
  taskId: string,
  orderId?: number | null,
): string {
  const base = `/employee-app-v2/tasks/${encodeURIComponent(taskId)}`;
  if (orderId != null && Number.isFinite(orderId)) {
    return `${base}?orderId=${orderId}`;
  }
  return base;
}
