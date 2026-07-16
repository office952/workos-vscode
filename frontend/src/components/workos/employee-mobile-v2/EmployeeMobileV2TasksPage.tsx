import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchEmployeeMobileOrderBlueprint,
  type EmployeeMobileOrderBlueprintDTO,
} from "@/api/employeeMobileOrderBlueprint";
import { useEmployeeMobileV2TaskTruthContext } from "@/contexts/EmployeeMobileV2TaskTruthContext";
import EmployeeMobileV2AvailableTasksSection from "@/components/workos/employee-mobile-v2/EmployeeMobileV2AvailableTasksSection";
import EmployeeMobileV2HelpOpportunitiesSection from "@/components/workos/employee-mobile-v2/EmployeeMobileV2HelpOpportunitiesSection";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import { isFlexCollabUiEnabled } from "@/lib/flexCollabUiFlag";
import { EmployeeMobileV2TasksMiniSummary } from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskGroup";
import EmployeeMobileV2TaskRow from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskRow";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { emV2SectionLabelClass } from "@/lib/employeeMobileV2DesignTokens";
import {
  buildPersonalTasksById,
  resolvePipelineCurrentTaskId,
} from "@/lib/employeeMobilePipelineEligibility";
import {
  buildTasksPageMiniSummary,
  filterActiveMyTasks,
  filterRecentDoneTasks,
  sortActiveMyTasks,
} from "@/lib/employeeMobileV2TaskGrouping";
import { cn } from "@/lib/utils";

function TaskTruthErrorState({
  message,
  errorCode,
  employeeLinkMissing,
  contractError,
}: {
  message: string;
  errorCode: string | null;
  employeeLinkMissing: boolean;
  contractError: boolean;
}) {
  const hint = employeeLinkMissing
    ? "Legătura cont–angajat se face din birou."
    : contractError
      ? "Datele taskurilor nu respectă contractul V2."
      : "Reîncearcă sau contactează biroul dacă problema persistă.";

  return (
    <div data-testid="employee-mobile-v2-tasks-error">
      <EmployeeMobileErrorState message={message} testId="employee-mobile-v2-tasks-error-message" />
      <p className="mt-2 px-1 text-[12px] text-slate-500 leading-snug">{hint}</p>
      {errorCode ? (
        <details className="mt-2 px-1 text-[11px] text-slate-600">
          <summary className="cursor-pointer">Detalii diagnostic</summary>
          <p className="mt-1 font-mono break-all">{errorCode}</p>
        </details>
      ) : null}
    </div>
  );
}

export default function EmployeeMobileV2TasksPage() {
  const {
    view,
    loading,
    error,
    errorCode,
    employeeLinkMissing,
    contractError,
    reload,
  } = useEmployeeMobileV2TaskTruthContext();
  const [blueprint, setBlueprint] = useState<EmployeeMobileOrderBlueprintDTO | null>(null);

  const tasks = view?.assignedTasks ?? [];
  const availableTasks = view?.availableTasks ?? [];
  const inProgressTasks = view?.inProgressTasks ?? [];

  const activeMyTasks = useMemo(
    () => sortActiveMyTasks(filterActiveMyTasks(tasks)),
    [tasks],
  );
  const assignedNotInProgress = useMemo(
    () => activeMyTasks.filter((task) => task.status !== "in_progress"),
    [activeMyTasks],
  );
  const recentDoneTasks = useMemo(() => filterRecentDoneTasks(tasks), [tasks]);

  const primaryOrderId = useMemo(() => {
    const activeOrderIds = new Set(activeMyTasks.map((task) => task.order_id));
    if (activeOrderIds.size === 1) {
      return [...activeOrderIds][0];
    }
    const counts = new Map<number, number>();
    for (const task of activeMyTasks) {
      counts.set(task.order_id, (counts.get(task.order_id) ?? 0) + 1);
    }
    let best: number | null = null;
    let bestCount = 0;
    for (const [orderId, count] of counts) {
      if (count > bestCount) {
        best = orderId;
        bestCount = count;
      }
    }
    return best;
  }, [activeMyTasks]);

  const loadBlueprint = useCallback(async () => {
    if (primaryOrderId == null) {
      setBlueprint(null);
      return;
    }
    try {
      const data = await fetchEmployeeMobileOrderBlueprint(primaryOrderId);
      setBlueprint(Array.isArray(data.tasks) ? data : null);
    } catch {
      setBlueprint(null);
    }
  }, [primaryOrderId]);

  useEffect(() => {
    void loadBlueprint();
  }, [loadBlueprint]);

  const blueprintById = useMemo(
    () => new Map((blueprint?.tasks ?? []).map((task) => [task.task_id, task])),
    [blueprint?.tasks],
  );

  const currentStep = useMemo(() => {
    if (!blueprint) return { index: null as number | null, total: null as number | null };
    const personalById = buildPersonalTasksById(tasks);
    const currentTaskId = resolvePipelineCurrentTaskId(blueprint.tasks, personalById);
    const index =
      currentTaskId != null
        ? blueprint.tasks.findIndex((row) => row.task_id === currentTaskId) + 1
        : null;
    return { index: index && index > 0 ? index : null, total: blueprint.tasks.length };
  }, [blueprint, tasks]);

  const miniSummary = useMemo(
    () =>
      buildTasksPageMiniSummary(tasks, {
        currentStepIndex: currentStep.index,
        totalSteps: currentStep.total,
      }),
    [tasks, currentStep.index, currentStep.total],
  );

  const hasAssignedContent =
    inProgressTasks.length > 0 || assignedNotInProgress.length > 0 || recentDoneTasks.length > 0;

  return (
    <div data-testid="employee-mobile-v2-tasks">
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2"
        title="Taskurile mele"
        testId="employee-mobile-v2-tasks-header"
      />

      {!loading && !error ? (
        <EmployeeMobileV2TasksMiniSummary title={miniSummary.title} line={miniSummary.line} />
      ) : null}

      {loading ? (
        <EmployeeMobileLoadingState
          message="Se încarcă taskurile…"
          testId="employee-mobile-v2-tasks-loading"
        />
      ) : null}

      {!loading && error ? (
        <TaskTruthErrorState
          message={error}
          errorCode={errorCode}
          employeeLinkMissing={employeeLinkMissing}
          contractError={contractError}
        />
      ) : null}

      {!loading && !error && !hasAssignedContent && availableTasks.length === 0 ? (
        <EmployeeMobileEmptyState
          message="Nu ai sarcini acum."
          hint="Când îți sunt atribuite sau disponibile taskuri, le vei vedea aici."
          testId="employee-mobile-v2-tasks-empty"
        />
      ) : null}

      {!loading && !error && inProgressTasks.length > 0 ? (
        <section className="mb-5" data-testid="employee-mobile-v2-in-progress-section">
          <h3 className={cn(emV2SectionLabelClass(), "mb-2")}>În lucru</h3>
          <div className="space-y-2" data-testid="employee-mobile-v2-in-progress-list">
            {inProgressTasks.map((task) => (
              <EmployeeMobileV2TaskRow
                key={`progress-${task.order_id}-${task.task_id}`}
                task={task}
                blueprintTask={blueprintById.get(task.task_id) ?? null}
                highlighted
                testIdPrefix="employee-mobile-v2-in-progress-row"
              />
            ))}
          </div>
        </section>
      ) : null}

      {!loading && !error && assignedNotInProgress.length > 0 ? (
        <section className="mb-5" data-testid="employee-mobile-v2-assigned-section">
          <h3 className={cn(emV2SectionLabelClass(), "mb-2")}>Sarcinile mele</h3>
          <div className="space-y-2" data-testid="employee-mobile-v2-tasks-list">
            {assignedNotInProgress.map((task) => (
              <EmployeeMobileV2TaskRow
                key={`${task.order_id}-${task.task_id}`}
                task={task}
                blueprintTask={blueprintById.get(task.task_id) ?? null}
                testIdPrefix="employee-mobile-v2-task-row"
              />
            ))}
          </div>
        </section>
      ) : null}

      {isFlexCollabUiEnabled() ? (
        <div className="mb-5">
          <EmployeeMobileV2HelpOpportunitiesSection onAccepted={reload} />
        </div>
      ) : null}

      <EmployeeMobileV2AvailableTasksSection
        tasks={availableTasks}
        loading={loading}
        error={error}
        onStarted={reload}
      />

      {!loading && !error && recentDoneTasks.length > 0 ? (
        <section className="mt-5" data-testid="employee-mobile-v2-recent-done-section">
          <h3 className={cn(emV2SectionLabelClass(), "mb-2")}>Finalizate</h3>
          <div className="space-y-2" data-testid="employee-mobile-v2-recent-done-list">
            {recentDoneTasks.map((task) => (
              <EmployeeMobileV2TaskRow
                key={`done-${task.order_id}-${task.task_id}`}
                task={task}
                blueprintTask={blueprintById.get(task.task_id) ?? null}
                testIdPrefix="employee-mobile-v2-recent-done-row"
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
