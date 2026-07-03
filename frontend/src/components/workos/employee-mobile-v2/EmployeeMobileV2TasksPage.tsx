import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchEmployeeMobileOrderBlueprint,
  type EmployeeMobileOrderBlueprintDTO,
} from "@/api/employeeMobileOrderBlueprint";
import { useEmployeeMobileV2AvailableTasks } from "@/hooks/useEmployeeMobileV2AvailableTasks";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import EmployeeMobileV2AvailableTasksSection from "@/components/workos/employee-mobile-v2/EmployeeMobileV2AvailableTasksSection";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
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

export default function EmployeeMobileV2TasksPage() {
  const { tasks, loading, error, reload: reloadMyTasks } = useEmployeeMobileV2Tasks();
  const {
    tasks: availableTasks,
    loading: availableLoading,
    error: availableError,
    reload: reloadAvailableTasks,
  } = useEmployeeMobileV2AvailableTasks();
  const [blueprint, setBlueprint] = useState<EmployeeMobileOrderBlueprintDTO | null>(null);

  const activeMyTasks = useMemo(
    () => sortActiveMyTasks(filterActiveMyTasks(tasks)),
    [tasks],
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

  const reloadAfterClaim = useCallback(async () => {
    await Promise.all([reloadMyTasks(), reloadAvailableTasks()]);
  }, [reloadMyTasks, reloadAvailableTasks]);

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
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-tasks-error" />
      ) : null}

      {!loading && !error && activeMyTasks.length === 0 ? (
        <EmployeeMobileEmptyState
          message="Nu ai taskuri active acum."
          hint="Când îți sunt atribuite taskuri, le vei vedea aici."
          testId="employee-mobile-v2-tasks-empty"
        />
      ) : null}

      {!loading && !error && activeMyTasks.length > 0 ? (
        <div className="mb-5 space-y-2" data-testid="employee-mobile-v2-tasks-list">
          {activeMyTasks.map((task) => (
            <EmployeeMobileV2TaskRow
              key={`${task.order_id}-${task.task_id}`}
              task={task}
              blueprintTask={blueprintById.get(task.task_id) ?? null}
              highlighted={task.status === "in_progress"}
              testIdPrefix="employee-mobile-v2-task-row"
            />
          ))}
        </div>
      ) : null}

      <EmployeeMobileV2AvailableTasksSection
        tasks={availableTasks}
        loading={availableLoading}
        error={availableError}
        onStarted={reloadAfterClaim}
      />

      {!loading && !error && recentDoneTasks.length > 0 ? (
        <section className="mt-5" data-testid="employee-mobile-v2-recent-done-section">
          <h3 className={cn(emV2SectionLabelClass(), "mb-2")}>Finalizate recent</h3>
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
