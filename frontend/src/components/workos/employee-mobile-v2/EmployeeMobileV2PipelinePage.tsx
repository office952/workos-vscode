import { useCallback, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  fetchEmployeeMobileOrderBlueprint,
  type EmployeeMobileOrderBlueprintDTO,
} from "@/api/employeeMobileOrderBlueprint";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import EmployeeMobileV2PipelineTimeline from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PipelineTimeline";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import {
  buildPersonalTasksById,
  pickPrimaryOrderId,
  resolvePipelineCurrentTaskId,
} from "@/lib/employeeMobilePipelineEligibility";
import { useState } from "react";

export default function EmployeeMobileV2PipelinePage() {
  const navigate = useNavigate();
  const { tasks, loading: tasksLoading, error: tasksError } = useEmployeeMobileV2Tasks();
  const primaryOrderId = useMemo(() => pickPrimaryOrderId(tasks), [tasks]);
  const [blueprint, setBlueprint] = useState<EmployeeMobileOrderBlueprintDTO | null>(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  const loadPipeline = useCallback(async () => {
    if (primaryOrderId == null) {
      setBlueprint(null);
      return;
    }
    setPipelineLoading(true);
    setPipelineError(null);
    try {
      const data = await fetchEmployeeMobileOrderBlueprint(primaryOrderId);
      setBlueprint(Array.isArray(data.tasks) ? data : null);
    } catch (err) {
      setBlueprint(null);
      setPipelineError(err instanceof Error ? err.message : "Nu am putut încărca lucrarea.");
    } finally {
      setPipelineLoading(false);
    }
  }, [primaryOrderId]);

  useEffect(() => {
    void loadPipeline();
  }, [loadPipeline]);

  const subtitle = useMemo(() => {
    if (!blueprint) return undefined;
    const personalById = buildPersonalTasksById(tasks);
    const currentTaskId = resolvePipelineCurrentTaskId(blueprint.tasks, personalById);
    const currentStepIndex =
      currentTaskId != null
        ? blueprint.tasks.findIndex((row) => row.task_id === currentTaskId) + 1
        : null;
    return [
      blueprint.order_label,
      blueprint.client_label,
      currentStepIndex != null && currentStepIndex > 0
        ? `pas ${currentStepIndex}/${blueprint.tasks.length}`
        : `${blueprint.tasks.length} pași`,
    ]
      .filter(Boolean)
      .join(" · ");
  }, [blueprint, tasks]);

  return (
    <div data-testid="employee-mobile-v2-pipeline">
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2"
        title="Lucrarea curentă"
        subtitle={subtitle}
        testId="employee-mobile-v2-pipeline-header"
      />

      {tasksLoading || pipelineLoading ? (
        <EmployeeMobileLoadingState
          message="Se încarcă lucrarea…"
          testId="employee-mobile-v2-pipeline-loading"
        />
      ) : null}

      {!tasksLoading && tasksError ? (
        <EmployeeMobileErrorState message={tasksError} testId="employee-mobile-v2-pipeline-tasks-error" />
      ) : null}

      {!pipelineLoading && pipelineError ? (
        <EmployeeMobileErrorState message={pipelineError} testId="employee-mobile-v2-pipeline-error" />
      ) : null}

      {!tasksLoading && !pipelineLoading && !tasksError && primaryOrderId == null ? (
        <EmployeeMobileEmptyState
          message="Nu există o lucrare curentă în taskurile tale."
          hint="Când ai taskuri active pe o comandă, vei vedea pașii aici."
          testId="employee-mobile-v2-pipeline-empty"
        />
      ) : null}

      {!pipelineLoading && blueprint ? (
        <EmployeeMobileV2PipelineTimeline
          blueprint={blueprint}
          personalTasks={tasks}
          onOpenTask={(task) =>
            navigate(`/employee-app-v2/tasks/${encodeURIComponent(task.task_id)}?orderId=${task.order_id}`)
          }
          listHeading="Timeline"
          listTestId="employee-mobile-v2-pipeline-timeline"
        />
      ) : null}
    </div>
  );
}
