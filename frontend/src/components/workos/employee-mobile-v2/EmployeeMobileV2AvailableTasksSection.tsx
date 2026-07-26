import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import EmployeeMobileV2StatusIndicator from "@/components/workos/employee-mobile-v2/EmployeeMobileV2StatusIndicator";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { useEmployeeMobileV2StartAction } from "@/hooks/useEmployeeMobileV2StartAction";
import {
  emV2PrimaryButtonClass,
  emV2Surface,
  buildEmployeeMobileV2TaskPath,
} from "@/lib/employeeMobileV2DesignTokens";
import {
  partitionAvailableTasks,
  resolveAvailableTaskWaitingLabel,
} from "@/lib/employeeMobileV2AvailableTasks";
import {
  resolveTaskComponentLine,
  resolveTaskDisplayTitle,
} from "@/lib/employeeMobileV2TaskTruth";
import { resolveEmployeeMobileV2StatusPresentation } from "@/lib/employeeMobileV2Status";
import { AVAILABLE_START_LABEL, START_PENDING_LABEL } from "@/lib/employeeMobileV2StartAction";
import { cn } from "@/lib/utils";

function AvailableTaskCard({
  task,
  mode,
  isPending,
  onStart,
  onPreview,
}: {
  task: EmployeeMobileTaskDTO;
  mode: "startable" | "waiting";
  isPending: boolean;
  onStart: (task: EmployeeMobileTaskDTO) => void;
  onPreview: (task: EmployeeMobileTaskDTO) => void;
}) {
  const presentation = resolveEmployeeMobileV2StatusPresentation(task);
  const title = resolveTaskDisplayTitle(task);
  const componentLine = resolveTaskComponentLine(task);
  const orderLine = [task.order_code || `Comandă ${task.order_id}`, task.client]
    .filter(Boolean)
    .join(" · ");
  const waitingLabel = resolveAvailableTaskWaitingLabel(task);

  return (
    <li
      className={cn(emV2Surface.row, "p-3")}
      data-testid={`employee-mobile-v2-available-row-${task.task_id}`}
    >
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[15px] font-medium text-slate-100 leading-snug line-clamp-2">
            {title}
          </p>
          {componentLine ? (
            <p className="mt-0.5 text-[12px] text-slate-400 line-clamp-1">{componentLine}</p>
          ) : null}
          {orderLine ? (
            <p className="mt-0.5 text-[12px] text-slate-500 line-clamp-2">{orderLine}</p>
          ) : null}
          {mode === "waiting" ? (
            <p
              className="mt-1 text-[12px] text-amber-200/90 line-clamp-3"
              data-testid={`employee-mobile-v2-available-waiting-reason-${task.task_id}`}
            >
              {waitingLabel}
            </p>
          ) : presentation.detailLine ? (
            <p className="mt-1 text-[12px] text-slate-500 line-clamp-2">{presentation.detailLine}</p>
          ) : null}
        </div>
        {mode === "startable" ? (
          <EmployeeMobileV2StatusIndicator
            presentation={presentation}
            testId={`employee-mobile-v2-available-row-${task.task_id}-status`}
          />
        ) : null}
      </div>
      {mode === "startable" ? (
        <div className="mt-3 grid grid-cols-1 gap-2">
          <button
            type="button"
            className="min-h-[44px] rounded-lg border border-[#243044] px-3 py-2 text-sm font-medium text-slate-200"
            onClick={() => onPreview(task)}
            data-testid={`employee-mobile-v2-available-details-${task.task_id}-${task.order_id}`}
          >
            Vezi detalii
          </button>
          <button
            type="button"
            className={cn(emV2PrimaryButtonClass(), "w-full")}
            disabled={isPending}
            onClick={() => onStart(task)}
            data-testid={`employee-mobile-v2-available-start-${task.task_id}`}
          >
            {isPending ? START_PENDING_LABEL : AVAILABLE_START_LABEL}
          </button>
        </div>
      ) : null}
    </li>
  );
}

export default function EmployeeMobileV2AvailableTasksSection({
  tasks,
  loading,
  error,
  onStarted,
}: {
  tasks: EmployeeMobileTaskDTO[];
  loading: boolean;
  error: string | null;
  onStarted: () => void | Promise<void>;
}) {
  const navigate = useNavigate();
  const { startTask, isPending, error: startError } = useEmployeeMobileV2StartAction();

  const { startable, waiting } = useMemo(() => partitionAvailableTasks(tasks), [tasks]);

  async function handleStart(task: EmployeeMobileTaskDTO) {
    try {
      await startTask(task, async () => {
        await onStarted();
        navigate(buildEmployeeMobileV2TaskPath(task.task_id, task.order_id));
      });
    } catch {
      // error surfaced via hook state
    }
  }

  function handlePreview(task: EmployeeMobileTaskDTO) {
    navigate(buildEmployeeMobileV2TaskPath(task.task_id, task.order_id));
  }

  const hasAny = startable.length > 0 || waiting.length > 0;

  return (
    <section className="mt-6" data-testid="employee-mobile-v2-available-tasks">
      <header className="mb-3">
        <h2 className="text-[17px] font-semibold text-slate-100">Disponibile</h2>
        <p className="mt-1 text-[13px] text-slate-500 leading-snug">
          Taskuri pe care le poți prelua — eligibilitatea vine din backend.
        </p>
      </header>

      {startError ? (
        <p
          className="mb-3 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-[13px] text-rose-200"
          data-testid="employee-mobile-v2-available-start-error"
        >
          {startError}
        </p>
      ) : null}

      {loading ? (
        <EmployeeMobileLoadingState
          message="Se încarcă taskurile disponibile…"
          testId="employee-mobile-v2-available-loading"
        />
      ) : null}

      {!loading && error ? (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-available-error" />
      ) : null}

      {!loading && !error && !hasAny ? (
        <EmployeeMobileEmptyState
          message="Nu există taskuri disponibile acum."
          hint="Când apar taskuri neatribuite pentru rolul tău, le vei vedea aici."
          testId="employee-mobile-v2-available-empty"
        />
      ) : null}

      {!loading && !error && hasAny ? (
        <div className="space-y-5">
          <div data-testid="employee-mobile-v2-available-startable-section">
            <h3 className="text-[15px] font-semibold text-slate-100 mb-2">Poți începe acum</h3>
            {startable.length === 0 ? (
              <p
                className="text-[13px] text-slate-500 leading-snug"
                data-testid="employee-mobile-v2-available-no-startable"
              >
                Nu ai taskuri pe care le poți începe acum.
                {waiting.length > 0 ? " Ai taskuri în așteptare mai jos." : null}
              </p>
            ) : (
              <ul className="space-y-2" data-testid="employee-mobile-v2-available-startable-list">
                {startable.map((task) => (
                  <AvailableTaskCard
                    key={`start-${task.order_id}-${task.task_id}`}
                    task={task}
                    mode="startable"
                    isPending={isPending(task)}
                    onStart={(t) => void handleStart(t)}
                    onPreview={handlePreview}
                  />
                ))}
              </ul>
            )}
          </div>

          {waiting.length > 0 ? (
            <div data-testid="employee-mobile-v2-available-waiting-section">
              <h3 className="text-[15px] font-semibold text-slate-100 mb-2">În așteptare</h3>
              <ul className="space-y-2" data-testid="employee-mobile-v2-available-waiting-list">
                {waiting.map((task) => (
                  <AvailableTaskCard
                    key={`wait-${task.order_id}-${task.task_id}`}
                    task={task}
                    mode="waiting"
                    isPending={false}
                    onStart={() => {}}
                    onPreview={handlePreview}
                  />
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
