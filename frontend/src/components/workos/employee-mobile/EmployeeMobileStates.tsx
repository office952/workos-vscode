import { CheckCircle2, ChevronRight, Loader2, type LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

export type EmployeeMobileIconAccent = "emerald" | "blue" | "violet" | "amber" | "slate";

const ICON_ACCENT_STYLES: Record<EmployeeMobileIconAccent, string> = {
  emerald: "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/20",
  blue: "bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/20",
  violet: "bg-violet-500/15 text-violet-400 ring-1 ring-violet-500/20",
  amber: "bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/20",
  slate: "bg-slate-500/10 text-slate-400 ring-1 ring-slate-500/15",
};

export function EmployeeMobileLoadingState({
  message = "Se încarcă datele tale...",
  testId = "employee-mobile-loading",
}: {
  message?: string;
  testId?: string;
}) {
  return (
    <div
      className="flex items-center gap-2 text-[12px] text-slate-400 py-2"
      data-testid={testId}
    >
      <Loader2 className="w-4 h-4 animate-spin shrink-0" aria-hidden />
      {message}
    </div>
  );
}

export function EmployeeMobileEmptyState({
  message,
  hint,
  testId = "employee-mobile-empty",
}: {
  message: string;
  hint?: string;
  testId?: string;
}) {
  return (
    <div className="py-2 space-y-1" data-testid={testId}>
      <p className="text-[12px] text-slate-500">{message}</p>
      {hint ? <p className="text-[11px] text-slate-600">{hint}</p> : null}
    </div>
  );
}

export function EmployeeMobileErrorState({
  message,
  testId = "employee-mobile-error",
}: {
  message: string;
  testId?: string;
}) {
  return (
    <div
      className="rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2 text-[12px] text-red-300"
      data-testid={testId}
    >
      {message}
    </div>
  );
}

export function EmployeeMobileSuccessState({
  message,
  testId = "employee-mobile-success",
}: {
  message: string;
  testId?: string;
}) {
  return (
    <div
      className="rounded-xl border border-emerald-800/40 bg-emerald-950/25 px-3 py-2 flex items-start gap-2"
      data-testid={testId}
    >
      <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" aria-hidden />
      <p className="text-[12px] text-emerald-200">{message}</p>
    </div>
  );
}

type StatusBadgeVariant = "live" | "readonly" | "review" | "neutral" | "warning";

const BADGE_STYLES: Record<StatusBadgeVariant, string> = {
  live: "bg-emerald-900/40 text-emerald-200 border-emerald-700/50",
  readonly: "bg-blue-900/30 text-blue-200 border-blue-800/40",
  review: "bg-violet-900/40 text-violet-200 border-violet-700/50",
  neutral: "bg-slate-700/60 text-slate-300 border-slate-600",
  warning: "bg-amber-900/30 text-amber-300 border-amber-800/40",
};

export function EmployeeMobileStatusBadge({
  label,
  variant = "neutral",
  testId,
}: {
  label: string;
  variant?: StatusBadgeVariant;
  testId?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex px-2 py-0.5 text-[9px] font-semibold rounded-full border uppercase tracking-wide shrink-0",
        BADGE_STYLES[variant],
      )}
      data-testid={testId}
    >
      {label}
    </span>
  );
}

export function EmployeeMobileSectionCard({
  title,
  description,
  to,
  badge,
  footer,
  testId,
  icon: Icon,
  iconAccent = "slate",
  children,
}: {
  title: string;
  description: string;
  to: string;
  badge?: React.ReactNode;
  footer?: React.ReactNode;
  testId?: string;
  icon?: LucideIcon;
  iconAccent?: EmployeeMobileIconAccent;
  children?: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className="group block rounded-2xl border border-[#1E293B] bg-[#111827] p-4 hover:border-blue-700/40 hover:bg-[#131c2e] active:scale-[0.99] transition-all duration-150"
      data-testid={testId}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <div
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
              ICON_ACCENT_STYLES[iconAccent],
            )}
            aria-hidden
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h2 className="text-[14px] font-semibold text-slate-100 leading-snug">{title}</h2>
            {badge}
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">{description}</p>
          {children}
          {footer && <div className="text-[10px] text-slate-500 pt-0.5">{footer}</div>}
        </div>
        <ChevronRight
          className="w-4 h-4 shrink-0 mt-2 text-slate-600 group-hover:text-slate-400 transition-colors"
          aria-hidden
        />
      </div>
    </Link>
  );
}
