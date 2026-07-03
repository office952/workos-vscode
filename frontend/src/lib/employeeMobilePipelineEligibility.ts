import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";

export type PipelineMarker =
  | "acum"
  | "urmeaza"
  | "in_lucru"
  | "finalizat"
  | "blocat"
  | "alt_post"
  | "neatribuit"
  | "asteapta";

export interface PipelineTaskPresentation {
  taskNumber: number;
  mineLabel: string | null;
  marker: PipelineMarker | null;
  markerLabel: string | null;
  isCurrent: boolean;
  isUpcoming: boolean;
  hasOpenClarification: boolean;
  blockingTasks: Array<{ task_id: string; name: string }>;
  dependencyWarning: string | null;
  showStartButton: boolean;
}

export function buildPersonalTasksById(
  tasks: EmployeeMobileTaskDTO[],
): Map<string, EmployeeMobileTaskDTO> {
  const map = new Map<string, EmployeeMobileTaskDTO>();
  for (const task of tasks) {
    map.set(task.task_id, task);
  }
  return map;
}

export function pickPrimaryOrderId(tasks: EmployeeMobileTaskDTO[]): number | null {
  if (tasks.length === 0) return null;
  const counts = new Map<number, number>();
  for (const task of tasks) {
    if (task.status === "done") continue;
    counts.set(task.order_id, (counts.get(task.order_id) ?? 0) + 1);
  }
  if (counts.size === 0) return tasks[0].order_id;
  let bestId = tasks[0].order_id;
  let bestCount = -1;
  for (const [orderId, count] of counts) {
    if (count > bestCount) {
      bestCount = count;
      bestId = orderId;
    }
  }
  return bestId;
}

export function resolvePipelineCurrentTaskId(
  blueprintTasks: EmployeeMobileOrderBlueprintTask[],
  personalById: Map<string, EmployeeMobileTaskDTO>,
): string | null {
  const inProgress = blueprintTasks.find(
    (task) =>
      task.is_mine &&
      (task.readiness_status === "in_progress" ||
        personalById.get(task.task_id)?.status === "in_progress"),
  );
  if (inProgress) return inProgress.task_id;

  for (const task of blueprintTasks) {
    if (!task.is_mine) continue;
    if (task.is_startable) return task.task_id;
    const status = personalById.get(task.task_id)?.status;
    if (status === "assigned" && task.readiness_status === "eligible") {
      return task.task_id;
    }
  }
  return null;
}

export function buildPipelineTaskPresentation(
  blueprintTask: EmployeeMobileOrderBlueprintTask,
  index: number,
  currentTaskId: string | null,
  personalById: Map<string, EmployeeMobileTaskDTO>,
): PipelineTaskPresentation {
  const personal = personalById.get(blueprintTask.task_id);
  const status = personal?.status;
  const taskNumber = index + 1;
  const isCurrent = currentTaskId === blueprintTask.task_id;
  const hasOpenClarification = personal?.clarification_request?.status === "open";
  const blockingTasks = (blueprintTask.blocking_tasks ?? []).map((item) => ({
    task_id: String(item.task_id),
    name: String(item.name ?? item.task_id),
  }));
  const dependencyWarning =
    blueprintTask.dependency_warning ?? personal?.dependency_warning ?? null;
  const readinessStatus = blueprintTask.readiness_status ?? personal?.readiness_status;
  const isStartable = blueprintTask.is_startable ?? personal?.is_startable ?? false;

  const baseExtras = {
    blockingTasks,
    dependencyWarning,
    showStartButton: false,
  };

  if (!blueprintTask.is_mine) {
    if (blueprintTask.status_display === "Neatribuit") {
      return {
        taskNumber,
        mineLabel: null,
        marker: "neatribuit",
        markerLabel: "Alt post",
        isCurrent: false,
        isUpcoming: false,
        hasOpenClarification: false,
        ...baseExtras,
      };
    }
    if (blueprintTask.status_display === "În lucru") {
      return {
        taskNumber,
        mineLabel: null,
        marker: "alt_post",
        markerLabel: "În lucru la alt post",
        isCurrent: false,
        isUpcoming: false,
        hasOpenClarification: false,
        ...baseExtras,
      };
    }
    if (blueprintTask.status_display === "Finalizat") {
      return {
        taskNumber,
        mineLabel: null,
        marker: "finalizat",
        markerLabel: "Finalizat",
        isCurrent: false,
        isUpcoming: false,
        hasOpenClarification: false,
        ...baseExtras,
      };
    }
    if (blueprintTask.status_display === "Blocat") {
      return {
        taskNumber,
        mineLabel: null,
        marker: "blocat",
        markerLabel: "Blocat",
        isCurrent: false,
        isUpcoming: false,
        hasOpenClarification: false,
        ...baseExtras,
      };
    }
    return {
      taskNumber,
      mineLabel: null,
      marker: "alt_post",
      markerLabel: "Alt post",
      isCurrent: false,
      isUpcoming: false,
      hasOpenClarification: false,
      ...baseExtras,
    };
  }

  if (status === "done") {
    return {
      taskNumber,
      mineLabel: "Finalizat",
      marker: "finalizat",
      markerLabel: null,
      isCurrent: false,
      isUpcoming: false,
      hasOpenClarification: false,
      ...baseExtras,
    };
  }

  if (status === "blocked") {
    return {
      taskNumber,
      mineLabel: "Blocat",
      marker: "blocat",
      markerLabel: null,
      isCurrent: false,
      isUpcoming: false,
      hasOpenClarification,
      ...baseExtras,
    };
  }

  if (status === "in_progress" || readinessStatus === "in_progress") {
    return {
      taskNumber,
      mineLabel: "În lucru",
      marker: "acum",
      markerLabel: "Acum",
      isCurrent: true,
      isUpcoming: false,
      hasOpenClarification,
      ...baseExtras,
    };
  }

  if (readinessStatus === "waiting_predecessor") {
    return {
      taskNumber,
      mineLabel: "Alocat mie",
      marker: "asteapta",
      markerLabel: blueprintTask.readiness_label || "Așteaptă task anterior",
      isCurrent: false,
      isUpcoming: false,
      hasOpenClarification,
      ...baseExtras,
    };
  }

  if (readinessStatus === "waiting_material") {
    return {
      taskNumber,
      mineLabel: "Alocat mie",
      marker: "asteapta",
      markerLabel: blueprintTask.readiness_label || "Așteaptă material",
      isCurrent: false,
      isUpcoming: false,
      hasOpenClarification,
      ...baseExtras,
    };
  }

  if (isCurrent && isStartable) {
    return {
      taskNumber,
      mineLabel: "Alocat mie",
      marker: "acum",
      markerLabel: "Acum",
      isCurrent: true,
      isUpcoming: false,
      hasOpenClarification,
      showStartButton: true,
      blockingTasks,
      dependencyWarning,
    };
  }

  if (isStartable) {
    return {
      taskNumber,
      mineLabel: "Alocat mie",
      marker: "urmeaza",
      markerLabel: "Urmează",
      isCurrent: false,
      isUpcoming: true,
      hasOpenClarification,
      ...baseExtras,
    };
  }

  return {
    taskNumber,
    mineLabel: "Alocat mie",
    marker: "urmeaza",
    markerLabel: "Urmează",
    isCurrent: false,
    isUpcoming: true,
    hasOpenClarification,
    ...baseExtras,
  };
}
