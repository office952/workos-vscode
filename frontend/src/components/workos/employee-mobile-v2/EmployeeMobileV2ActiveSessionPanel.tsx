import { useEffect, useMemo, useState } from "react";
import { Clock3 } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildActiveSessionSummary,
  computePresentationElapsedMinutes,
  formatPresentationElapsed,
  shouldShowActiveSessionPanel,
} from "@/lib/employeeMobileV2ActiveSessionPresentation";
import { emV2Surface } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2ActiveSessionPanel({
  task,
  testIdPrefix = "employee-mobile-v2-active-session",
}: {
  task: EmployeeMobileTaskDTO;
  testIdPrefix?: string;
}) {
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!shouldShowActiveSessionPanel(task) || task.status === "done") return undefined;
    const id = window.setInterval(() => setTick((value) => value + 1), 30_000);
    return () => window.clearInterval(id);
  }, [task]);

  const summary = useMemo(() => buildActiveSessionSummary(task), [task]);
  const elapsedMinutes = useMemo(
    () => computePresentationElapsedMinutes(task.started_at),
    [task.started_at, tick],
  );
  const elapsedLabel = formatPresentationElapsed(elapsedMinutes);

  if (!shouldShowActiveSessionPanel(task)) return null;

  return (
    <section
      className={cn(emV2Surface.panel, "p-4 mt-4")}
      data-testid={testIdPrefix}
      data-elapsed-classification={summary.elapsedClassification}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sky-500/10 text-sky-300">
          <Clock3 className="h-4 w-4" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500">
            Sesiune activă
          </p>
          <p className="mt-1 text-sm font-medium text-slate-100" data-testid={`${testIdPrefix}-status`}>
            {summary.statusLabel}
          </p>
          {summary.startedAtLabel ? (
            <p className="mt-1 text-[13px] text-slate-400" data-testid={`${testIdPrefix}-started-at`}>
              Început: {summary.startedAtLabel}
            </p>
          ) : null}
          {elapsedLabel && task.status !== "done" ? (
            <p className="mt-1 text-[13px] text-sky-300/90" data-testid={`${testIdPrefix}-elapsed`}>
              Timp orientativ: {elapsedLabel}
            </p>
          ) : null}
          {summary.completedAtLabel ? (
            <p className="mt-1 text-[13px] text-emerald-300/90" data-testid={`${testIdPrefix}-completed-at`}>
              Finalizat: {summary.completedAtLabel}
            </p>
          ) : null}
          {task.status !== "done" ? (
            <p className="mt-2 text-[11px] text-slate-500 leading-snug" data-testid={`${testIdPrefix}-elapsed-disclaimer`}>
              {summary.elapsedDisclaimer}
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
