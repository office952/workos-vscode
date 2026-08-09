import { useMemo } from "react";
import { CheckCircle2, PlayCircle } from "lucide-react";
import type { ExecutionPlanResponse, ExecutionRealityResponse } from "@/api/execution";
import { MachineRunContextChip } from "@/components/machine-run/MachineRunContextChip";
import { useActiveMachineRunByTasks } from "@/hooks/useActiveMachineRunByTasks";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import { candidateSelectionKey } from "@/lib/machineRunUi";

export function WorkPanel({
  plan,
  reality,
  busyTaskId,
  onStart,
  onComplete,
  allowSessionActions = true,
}: {
  plan: ExecutionPlanResponse | null;
  reality: ExecutionRealityResponse | null;
  busyTaskId: string | null;
  onStart: (taskId: string) => void;
  onComplete: (taskId: string) => void;
  /** When false, planned/draft tasks are listed read-only — no Start/Finalize. */
  allowSessionActions?: boolean;
}) {
  const { can } = useCurrentPermissions();
  const canReadMachineRun = can("execution.machine_run.read");

  const lookupRefs = useMemo(
    () =>
      plan
        ? plan.tasks.map((task) => ({
            execution_plan_id: plan.id,
            task_key: task.task_id,
          }))
        : [],
    [plan],
  );

  const { byKey } = useActiveMachineRunByTasks(
    lookupRefs,
    Boolean(plan && canReadMachineRun),
  );

  if (!plan) return null;
  return (
    <section className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-work-panel">
      <h2 className="text-sm font-semibold text-wo-text-primary">Lucru în execuție</h2>
      {!allowSessionActions ? (
        <p className="mt-1 text-[11px] text-amber-200" data-testid="execution-work-panel-sessions-blocked">
          {plan.operational_tasks_materialized || (plan.operational_tasks_count ?? 0) > 0
            ? "Sesiunile rămân blocate (FROZEN) — materializarea nu autorizează Start/Stop. Lista de mai jos este read-only."
            : "Sesiunile sunt blocate: taskurile operaționale nu sunt materializate (sau sessions rămân FROZEN). Lista de mai jos este read-only."}
        </p>
      ) : (
        <p className="mt-1 text-[11px] text-wo-text-muted">Înregistrările sunt confirmate prin backend înainte de reîncărcare.</p>
      )}
      <div
        className="mt-3 space-y-2"
        data-testid="execution-work-panel-machine-run-lookups"
        data-task-count={plan.tasks.length}
        data-lookup-count={canReadMachineRun ? plan.tasks.length : 0}
      >
        {plan.tasks.map((task) => {
          const last = reality?.tasks.filter((item) => item.task_id === task.task_id).at(-1);
          const status = !last ? "nepornit" : last.ended_at ? "finalizat" : "în curs";
          const busy = busyTaskId === task.task_id;
          const membership = byKey.get(
            candidateSelectionKey(plan.id, task.task_id),
          );
          return (
            <div
              key={task.task_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-wo-border-subtle bg-wo-surface-raised px-3 py-2"
            >
              <div className="min-w-0 space-y-1">
                <p className="text-[12px] font-semibold text-wo-text-primary">{task.display_name ?? task.name}</p>
                <p className="text-[10px] text-wo-text-muted">
                  {status} ·{" "}
                  {task.estimated_time_minutes == null
                    ? "durată neconfirmată"
                    : `${task.estimated_time_minutes.toFixed(1)} min planificate`}
                </p>
                <MachineRunContextChip
                  membership={membership}
                  testId={`execution-machine-run-chip-${task.task_id}`}
                />
              </div>
              {allowSessionActions ? (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => onStart(task.task_id)}
                    disabled={busy || status !== "nepornit"}
                    className="inline-flex items-center gap-1 rounded bg-blue-600 px-2 py-1 text-[11px] font-semibold text-white disabled:opacity-50"
                  >
                    <PlayCircle className="h-3 w-3" /> Start
                  </button>
                  <button
                    type="button"
                    onClick={() => onComplete(task.task_id)}
                    disabled={busy || status !== "în curs"}
                    className="inline-flex items-center gap-1 rounded bg-emerald-600 px-2 py-1 text-[11px] font-semibold text-white disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-3 w-3" /> Finalizează
                  </button>
                </div>
              ) : (
                <span className="text-[10px] text-wo-text-muted">read-only</span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
