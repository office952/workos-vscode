import { useMemo, useState, type ReactNode } from "react";
import { operatorStatusSemanticRo } from "@/lib/intakeV6/intakeV6OperatorVocabulary";

export type IntakeV6SystemChecksSeverity = "ok" | "warning" | "critical";

export interface IntakeV6SystemChecksSummary {
  mentionCount: number;
  severity: IntakeV6SystemChecksSeverity;
  label: string;
  badgeLabel: string;
}

export function resolveIntakeV6SystemChecksSummary(args: {
  warningCount?: number | null;
  criticalCount?: number | null;
}): IntakeV6SystemChecksSummary {
  const warningCount = Math.max(0, args.warningCount ?? 0);
  const criticalCount = Math.max(0, args.criticalCount ?? 0);
  const mentionCount = warningCount + criticalCount;
  const severity: IntakeV6SystemChecksSeverity =
    criticalCount > 0 ? "critical" : mentionCount > 0 ? "warning" : "ok";

  const badgeLabel =
    severity === "ok"
      ? operatorStatusSemanticRo("ready")
      : severity === "critical"
        ? operatorStatusSemanticRo("blocker")
        : operatorStatusSemanticRo("warning");

  return {
    mentionCount,
    severity,
    label:
      mentionCount === 0
        ? `Verificări sistem: ${operatorStatusSemanticRo("ready")}`
        : `Verificări sistem: ${mentionCount} mențiuni de rezolvat`,
    badgeLabel,
  };
}

function badgeClass(severity: IntakeV6SystemChecksSeverity): string {
  if (severity === "critical") {
    return "border-red-500/30 bg-red-500/10 text-red-200";
  }
  if (severity === "warning") {
    return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  }
  return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
}

export default function IntakeV6SystemChecksPanel({
  warningCount = 0,
  criticalCount = 0,
  children,
  testId = "intake-v6-system-checks",
  className = "mt-4",
}: {
  warningCount?: number;
  criticalCount?: number;
  children: ReactNode;
  testId?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const summary = useMemo(
    () => resolveIntakeV6SystemChecksSummary({ warningCount, criticalCount }),
    [warningCount, criticalCount],
  );

  return (
    <div
      className={`rounded border border-[#2A3548] bg-[#0A0F1A]/40 ${className}`.trim()}
      data-testid={testId}
      data-system-checks-severity={summary.severity}
      data-system-checks-mentions={summary.mentionCount}
    >
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        onClick={() => setOpen((value) => !value)}
        data-testid={`${testId}-toggle`}
        aria-expanded={open}
      >
        <div className="min-w-0">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-300">
            {summary.label}
          </p>
          <p className="mt-0.5 text-[10px] text-slate-500">
            Contracte, linkage, trace și diagnostice pentru audit / dezvoltare.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${badgeClass(summary.severity)}`}>
            {summary.badgeLabel}
          </span>
          <span className="text-slate-500">{open ? "▾" : "▸"}</span>
        </div>
      </button>
      {open ? (
        <div className="border-t border-[#2A3548] px-4 py-3" data-testid={`${testId}-content`}>
          {children}
        </div>
      ) : null}
    </div>
  );
}