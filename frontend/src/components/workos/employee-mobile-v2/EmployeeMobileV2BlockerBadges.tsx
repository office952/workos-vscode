import type { EmV2TaskBlockerPresentation } from "@/lib/employeeMobileV2BlockerPresentation";
import { primaryStateTone } from "@/lib/employeeMobileV2BlockerPresentation";
import { cn } from "@/lib/utils";

const toneClass: Record<ReturnType<typeof primaryStateTone>, string> = {
  ready: "border-emerald-500/40 bg-emerald-950/30 text-emerald-200",
  active: "border-sky-500/40 bg-sky-950/30 text-sky-200",
  warning: "border-rose-500/40 bg-rose-950/30 text-rose-200",
  waiting: "border-amber-500/40 bg-amber-950/30 text-amber-200",
  neutral: "border-slate-600/50 bg-slate-900/50 text-slate-300",
};

export default function EmployeeMobileV2BlockerBadges({
  presentation,
  compact = false,
  testIdPrefix = "employee-mobile-v2-blocker",
}: {
  presentation: EmV2TaskBlockerPresentation;
  compact?: boolean;
  testIdPrefix?: string;
}) {
  const tone = primaryStateTone(presentation.primaryState);

  return (
    <div
      className={cn("flex flex-wrap items-center gap-1.5", compact ? "mt-1" : "mt-2")}
      data-testid={`${testIdPrefix}-badges`}
    >
      <span
        className={cn(
          "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium leading-tight",
          toneClass[tone],
        )}
        data-testid={`${testIdPrefix}-readiness-badge`}
      >
        {presentation.primaryLabel}
      </span>
      {presentation.showProductionBadge ? (
        <span
          className="inline-flex items-center rounded-md border border-rose-600/50 bg-rose-950/40 px-2 py-0.5 text-[11px] font-medium text-rose-200"
          data-testid={`${testIdPrefix}-production-badge`}
        >
          {presentation.productionBadgeLabel}
        </span>
      ) : null}
      {!compact && presentation.blockerCount > 0 ? (
        <span
          className="inline-flex items-center rounded-md border border-slate-700 bg-slate-900/60 px-2 py-0.5 text-[11px] text-slate-400"
          data-testid={`${testIdPrefix}-blocker-count`}
        >
          {presentation.blockerCount} blocaj{presentation.blockerCount === 1 ? "" : "e"}
        </span>
      ) : null}
    </div>
  );
}
