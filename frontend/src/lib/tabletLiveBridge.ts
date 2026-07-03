/**
 * Tablet live bridge — maps operator/execution tasks to tablet UI model.
 * Demo data stays in workstationRouting; live flow uses this module.
 */
import type { OperationResourceMapping } from "@/api/operationalRegistry";
import { resolveMappingFromList } from "@/features/operational-registry/operationResolution";
import type { OperatorTask, TaskStatus } from "@/lib/mockData";
import {
  getRoutingForOperation,
  type TabletTask,
  type TabletTaskStatus,
} from "@/lib/workstationRouting";

/** Workcenter codes associated with each tablet station (registry-aligned). */
export const STATION_WORKCENTER_CODES: Record<string, string[]> = {
  print: ["WC_PRINT"],
  cutter_plotter: ["WC_CUT"],
  cnc: ["WC_CNC_ROUTING", "WC_LASER_CUTTING"],
  modelare_litere: ["WC_LETTER_FORMING"],
  led_electric: ["WC_LED_ASSEMBLY"],
  lacatuserie_sudura: ["WC_METAL_FAB"],
  asamblare_lipire: ["WC_ASSEMBLY"],
  montaj_autocolant: ["WC_VINYL_APPLICATION"],
};

const LIVE_TO_TABLET_STATUS: Record<TaskStatus, TabletTaskStatus> = {
  created: "in_coada",
  assigned: "pregatit",
  in_progress: "in_lucru",
  paused: "in_lucru",
  blocked: "blocat",
  done: "finalizat",
  cancelled: "in_coada",
};

export function mapLiveStatusToTabletStatus(liveStatus: TaskStatus): TabletTaskStatus {
  return LIVE_TO_TABLET_STATUS[liveStatus] ?? "in_coada";
}

export function normalizeOperationCode(code: string): string {
  return code.toLowerCase().replace(/[-\s]/g, "_");
}

export function extractOrderIdFromJob(jobId: string): number {
  const match = jobId.match(/JOB-(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

export function resolveStationForTask(
  task: Pick<OperatorTask, "operationCode" | "machineName" | "processId">,
  mappings: OperationResourceMapping[]
): { stationId: string | null; mappingConfirmed: boolean } {
  const op = normalizeOperationCode(task.operationCode || "");
  const routing = getRoutingForOperation(op, task.processId);
  if (routing) {
    return { stationId: routing.workstationId, mappingConfirmed: true };
  }

  const registryMapping = resolveMappingFromList(op, mappings).mapping;
  if (registryMapping?.allowed_workcenter_codes?.length) {
    for (const [stationId, codes] of Object.entries(STATION_WORKCENTER_CODES)) {
      if (registryMapping.allowed_workcenter_codes.some((wc) => codes.includes(wc))) {
        return { stationId, mappingConfirmed: true };
      }
    }
  }

  return { stationId: null, mappingConfirmed: false };
}

export function taskBelongsToStation(
  task: Pick<OperatorTask, "operationCode" | "machineName" | "processId">,
  stationId: string,
  mappings: OperationResourceMapping[]
): { include: boolean; mappingConfirmed: boolean } {
  const op = normalizeOperationCode(task.operationCode || "");
  const routing = getRoutingForOperation(op, task.processId);
  if (routing?.workstationId === stationId) {
    return { include: true, mappingConfirmed: true };
  }

  const registryMapping = resolveMappingFromList(op, mappings).mapping;
  const stationWcs = STATION_WORKCENTER_CODES[stationId] ?? [];
  if (registryMapping?.allowed_workcenter_codes?.length && stationWcs.length) {
    const overlap = registryMapping.allowed_workcenter_codes.some((wc) => stationWcs.includes(wc));
    if (overlap) return { include: true, mappingConfirmed: true };
  }

  if (!routing && !registryMapping) {
    return { include: true, mappingConfirmed: false };
  }

  if (!routing && registryMapping && !registryMapping.allowed_workcenter_codes?.length) {
    return { include: true, mappingConfirmed: false };
  }

  return { include: false, mappingConfirmed: false };
}

export function mapOperatorTaskToTabletTask(
  task: OperatorTask,
  mappings: OperationResourceMapping[],
  stationId: string
): TabletTask {
  const op = normalizeOperationCode(task.operationCode || "");
  const routing = getRoutingForOperation(op, task.processId);
  const { mappingConfirmed } = taskBelongsToStation(task, stationId, mappings);
  const orderIdNum = extractOrderIdFromJob(task.jobId);

  return {
    id: task.id,
    orderId: String(orderIdNum || task.jobId),
    orderCode: task.jobId.replace("JOB-", "ORD-"),
    client: task.client,
    product: task.product,
    operationType: task.operationCode,
    operationName: task.operationName,
    workstationId: stationId,
    requiredSkill: routing?.requiredSkill ?? "—",
    skillLabel: routing?.skillLabel ?? "—",
    status: mapLiveStatusToTabletStatus(task.status),
    priority: "normal",
    deadline: task.plannedDurationMin ? `${task.plannedDurationMin} min plan` : "—",
    assignedOperator: task.employeeName || task.assignee || undefined,
    dimensions: task.material ? `${task.material}${task.finish ? ` · ${task.finish}` : ""}` : "—",
    material: task.material || "—",
    color: task.finish || "—",
    quantity: 1,
    observations: task.intakeCode ? `Cerere: ${task.intakeCode}` : task.quoteCode ? `Ofertă: ${task.quoteCode}` : "",
    attachments: [],
    routingExplanation: mappingConfirmed
      ? `Operație ${task.operationCode} → stație ${stationId}`
      : `Mapping neconfirmat pentru ${task.operationCode} — afișat cu atenție`,
    isLive: true,
    mappingConfirmed,
    liveStatus: task.status,
    employeeId: task.employeeId ?? null,
    employeeName: task.employeeName ?? null,
    machineName: task.machineName,
    orderIdNum,
    layerId: task.layerId,
    instructions: task.instructions,
  };
}

export function filterLiveTasksForStation(
  tasks: OperatorTask[],
  stationId: string,
  mappings: OperationResourceMapping[]
): TabletTask[] {
  return tasks
    .filter((t) => taskBelongsToStation(t, stationId, mappings).include)
    .map((t) => mapOperatorTaskToTabletTask(t, mappings, stationId));
}

export interface TabletStationCounts {
  queue: number;
  inProgress: number;
  blocked: number;
  completedToday: number;
}

export function computeTabletStationCounts(stationTasks: TabletTask[]): TabletStationCounts {
  return {
    queue: stationTasks.filter((t) => t.status === "in_coada" || t.status === "pregatit").length,
    inProgress: stationTasks.filter((t) => t.status === "in_lucru").length,
    blocked: stationTasks.filter((t) => t.status === "blocat").length,
    completedToday: stationTasks.filter((t) => t.status === "finalizat" || t.status === "predat").length,
  };
}
