import { cn } from "@/lib/utils";
import type { EmV2ModuleAccent } from "@/lib/employeeMobileV2DesignTokens";

/** Centralized Atoms-inspired motion + surface effects for Employee Mobile v2 only. */
export const v2Motion = {
  /** Fade + slight lift on page container (one per screen). */
  pageEnter: "animate-em-v2-fade-slide-up motion-reduce:animate-none",
  /** Standard tap feedback for buttons and links. */
  tapTarget:
    "transition-transform duration-150 ease-out active:scale-[0.98] motion-reduce:transition-none motion-reduce:active:scale-100",
  /** Interactive cards and list rows. */
  cardInteractive:
    "transition-[transform,border-color] duration-150 ease-out active:scale-[0.98] motion-reduce:transition-none motion-reduce:active:scale-100",
  /** Module grid tiles — slightly stronger press like Atoms. */
  moduleTile:
    "transition-[transform,border-color] duration-150 ease-out active:scale-[0.96] motion-reduce:transition-none motion-reduce:active:scale-100",
} as const;

const ICON_GLOW: Partial<Record<EmV2ModuleAccent, string>> = {
  blue: "shadow-[0_0_14px_rgba(59,130,246,0.12)]",
  violet: "shadow-[0_0_14px_rgba(139,92,246,0.12)]",
  amber: "shadow-[0_0_14px_rgba(245,158,11,0.1)]",
  red: "shadow-[0_0_14px_rgba(239,68,68,0.1)]",
  emerald: "shadow-[0_0_14px_rgba(16,185,129,0.1)]",
};

export const v2Effects = {
  /** Live indicator beside ACUM label — opacity pulse, not scale. */
  activeDot:
    "h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400 animate-em-v2-pulse-dot motion-reduce:animate-none",
  /** Bottom nav + sticky footers. */
  stickySurface:
    "border-t border-[#1E293B] bg-[#111827]/92 backdrop-blur-xl shadow-[0_-4px_24px_rgba(0,0,0,0.35)]",
  stickyActionBar:
    "border-t border-[#1E293B] bg-[#0B1120]/95 backdrop-blur-md shadow-[0_-2px_16px_rgba(0,0,0,0.28)]",
  bottomNavItem:
    "relative flex flex-col items-center gap-1 rounded-[14px] px-5 py-2 min-h-[52px] justify-center transition-colors duration-150",
  bottomNavActive: "bg-blue-500/12",
  bottomNavInactive: "text-slate-500",
  bottomNavIndicator:
    "absolute top-1.5 left-1/2 h-0.5 w-5 -translate-x-1/2 rounded-full bg-blue-400 motion-reduce:opacity-100",
  documentRow: cn(emV2SurfaceRow(), v2Motion.cardInteractive),
  personalRow: cn(emV2SurfaceRow(), v2Motion.cardInteractive),
} as const;

function emV2SurfaceRow(): string {
  return "rounded-[10px] border border-[#1E293B] bg-[#111827]";
}

export function v2IconGlowClass(accent: EmV2ModuleAccent = "slate"): string {
  return ICON_GLOW[accent] ?? "";
}

export function v2InteractiveRowClass(extra?: string): string {
  return cn(emV2SurfaceRow(), v2Motion.cardInteractive, extra);
}
