import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";

export const SHOP_FLOOR_GENERIC_STEPS = [
  "Deschide taskul și urmează instrucțiunile operatorului.",
  "Dacă lipsește ceva, marchează blocaj.",
  "Finalizează când lucrarea este gata.",
] as const;

export function formatWorkContextLine(task: EmployeeMobileTaskDTO | null): {
  title: string;
  subtitle: string | null;
} {
  if (!task) {
    return { title: "Nicio lucrare activă", subtitle: null };
  }
  const title = (task.product || task.title || "Lucrare în curs").trim();
  const subtitle = [task.client, task.order_code ? `Comanda ${task.order_code}` : null]
    .filter(Boolean)
    .join(" · ");
  return { title, subtitle: subtitle || null };
}

export function formatOrderClientLine(
  orderLabel?: string | null,
  clientLabel?: string | null,
  orderCode?: string | null,
  client?: string | null,
): string {
  const order = (orderLabel || orderCode || "").trim();
  const clientName = (clientLabel || client || "").trim();
  if (order && clientName) return `${order} · ${clientName}`;
  return order || clientName || "";
}

export function simplifyStatusLabel(input: {
  readinessStatus?: string | null;
  readinessLabel?: string | null;
  statusDisplay?: string | null;
  status?: string | null;
}): string {
  const readiness = String(input.readinessStatus || "");
  if (readiness === "waiting_predecessor") return "Așteaptă task anterior";
  if (readiness === "waiting_material") return "Așteaptă material";
  if (readiness === "in_progress" || input.status === "in_progress") return "În lucru";
  if (input.status === "blocked") return "Blocat";
  if (readiness === "eligible" || input.status === "assigned") return "Pregătit de lucru";
  if (input.readinessLabel) return String(input.readinessLabel);
  if (input.statusDisplay) return String(input.statusDisplay);
  return "Alocat";
}

export function buildWhyItMattersLine(input: {
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
  personalTask?: EmployeeMobileTaskDTO | null;
}): string | null {
  const blueprint = input.blueprintTask;
  const personal = input.personalTask;
  const readiness = blueprint?.readiness_status ?? personal?.readiness_status;

  if (readiness === "waiting_predecessor") {
    const blocker = (blueprint?.blocking_tasks ?? personal?.blocking_tasks ?? [])[0];
    if (blocker?.name) return `Așteaptă: ${blocker.name}`;
    return "Așteaptă finalizarea unui task anterior.";
  }
  if (readiness === "waiting_material") {
    const hint = blueprint?.material_hints?.[0];
    if (hint?.label) return hint.label;
    if (blueprint?.material_status_label) return String(blueprint.material_status_label);
    return "Așteaptă material înainte de start.";
  }
  if (blueprint?.dependency_warning || personal?.dependency_warning) {
    return String(blueprint?.dependency_warning || personal?.dependency_warning);
  }
  if (personal?.blocked_reason) {
    return `Blocat: ${personal.blocked_reason}`;
  }
  const criticalHint = blueprint?.material_hints?.find(
    (hint) => hint.category === "project_critical",
  );
  if (criticalHint?.label && criticalHint.label !== "Verifică material") {
    return criticalHint.label;
  }
  return null;
}

export function pickUpcomingMineTasks(
  blueprintTasks: EmployeeMobileOrderBlueprintTask[],
  currentTaskId: string | null,
  limit = 2,
): EmployeeMobileOrderBlueprintTask[] {
  const upcoming: EmployeeMobileOrderBlueprintTask[] = [];
  for (const task of blueprintTasks) {
    if (!task.is_mine) continue;
    if (task.task_id === currentTaskId) continue;
    if (task.readiness_status === "done") continue;
    const status = task.status_display;
    if (status === "Finalizat") continue;
    upcoming.push(task);
    if (upcoming.length >= limit) break;
  }
  return upcoming;
}

export function resolveShopFloorFocusTask(input: {
  personalTasks: EmployeeMobileTaskDTO[];
  blueprintTasks?: EmployeeMobileOrderBlueprintTask[];
  currentTaskId?: string | null;
}): {
  personal: EmployeeMobileTaskDTO | null;
  blueprint: EmployeeMobileOrderBlueprintTask | null;
} {
  const personalById = new Map(input.personalTasks.map((task) => [task.task_id, task]));
  const blueprintById = new Map(
    (input.blueprintTasks ?? []).map((task) => [task.task_id, task]),
  );

  if (input.currentTaskId) {
    return {
      personal: personalById.get(input.currentTaskId) ?? null,
      blueprint: blueprintById.get(input.currentTaskId) ?? null,
    };
  }

  const inProgress = input.personalTasks.find((task) => task.status === "in_progress");
  if (inProgress) {
    return {
      personal: inProgress,
      blueprint: blueprintById.get(inProgress.task_id) ?? null,
    };
  }

  const blocked = input.personalTasks.find((task) => task.status === "blocked");
  if (blocked) {
    return {
      personal: blocked,
      blueprint: blueprintById.get(blocked.task_id) ?? null,
    };
  }

  const assigned = input.personalTasks.find((task) => task.status === "assigned");
  if (assigned) {
    return {
      personal: assigned,
      blueprint: blueprintById.get(assigned.task_id) ?? null,
    };
  }

  return { personal: null, blueprint: null };
}

export type HomeBriefLineKind = "continue" | "waiting" | "upcoming";

export type HomeBriefWaitingType = "waiting_predecessor" | "waiting_material" | "blocked";

export interface HomeBriefLine {
  kind: HomeBriefLineKind;
  label: "Continui" | "Așteaptă" | "Urmează";
  text: string;
  taskId?: string;
  orderId?: number;
  waitingType?: HomeBriefWaitingType;
}

function resolveTaskDisplayName(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): string {
  return (task.title || blueprintTask?.name || task.task_id).trim();
}

export function buildWaitingBriefText(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): string | null {
  const title = resolveTaskDisplayName(task, blueprintTask);
  const readiness = blueprintTask?.readiness_status ?? task.readiness_status;

  if (task.status === "blocked") {
    if (task.blocked_reason) {
      return `${title} — ${task.blocked_reason}`;
    }
    return `${title} — blocat`;
  }

  if (readiness === "waiting_predecessor") {
    const blocker = (blueprintTask?.blocking_tasks ?? task.blocking_tasks ?? [])[0];
    if (blocker?.name) {
      return `${title} așteaptă ${blocker.name}`;
    }
    return `${title} așteaptă task anterior`;
  }

  if (readiness === "waiting_material") {
    const hint = blueprintTask?.material_hints?.[0];
    if (hint?.name) {
      return `${title} așteaptă ${hint.name}`;
    }
    return `${title} așteaptă material`;
  }

  return null;
}

function isWaitingTask(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): boolean {
  if (task.status === "blocked") return true;
  const readiness = blueprintTask?.readiness_status ?? task.readiness_status;
  return readiness === "waiting_predecessor" || readiness === "waiting_material";
}

function waitingTypeForTask(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): HomeBriefWaitingType | undefined {
  if (task.status === "blocked") return "blocked";
  const readiness = blueprintTask?.readiness_status ?? task.readiness_status;
  if (readiness === "waiting_predecessor") return "waiting_predecessor";
  if (readiness === "waiting_material") return "waiting_material";
  return undefined;
}

export function buildHomeBriefLines(input: {
  personalTasks: EmployeeMobileTaskDTO[];
  blueprintTasks?: EmployeeMobileOrderBlueprintTask[];
  heroTask?: EmployeeMobileTaskDTO | null;
  primaryOrderId?: number | null;
  currentTaskId?: string | null;
}): HomeBriefLine[] {
  const lines: HomeBriefLine[] = [];
  const primaryOrderId = input.primaryOrderId ?? null;
  const blueprintById = new Map(
    (input.blueprintTasks ?? []).map((task) => [task.task_id, task]),
  );

  const scopedTasks =
    primaryOrderId != null
      ? input.personalTasks.filter((task) => task.order_id === primaryOrderId)
      : input.personalTasks;

  const hero = input.heroTask ?? null;
  const heroBlueprint = hero ? blueprintById.get(hero.task_id) : null;

  if (hero && hero.status === "in_progress") {
    lines.push({
      kind: "continue",
      label: "Continui",
      text: resolveTaskDisplayName(hero, heroBlueprint),
      taskId: hero.task_id,
      orderId: hero.order_id,
    });
  }

  let waitingTask: EmployeeMobileTaskDTO | null = null;
  let waitingBlueprint: EmployeeMobileOrderBlueprintTask | null = null;

  for (const task of scopedTasks) {
    if (hero?.task_id === task.task_id && hero.status === "in_progress") continue;
    const blueprintTask = blueprintById.get(task.task_id) ?? null;
    if (!isWaitingTask(task, blueprintTask)) continue;
    waitingTask = task;
    waitingBlueprint = blueprintTask;
    break;
  }

  if (waitingTask) {
    const text = buildWaitingBriefText(waitingTask, waitingBlueprint);
    if (text) {
      lines.push({
        kind: "waiting",
        label: "Așteaptă",
        text,
        taskId: waitingTask.task_id,
        orderId: waitingTask.order_id,
        waitingType: waitingTypeForTask(waitingTask, waitingBlueprint),
      });
    }
  }

  const upcomingCandidates = pickUpcomingMineTasks(
    input.blueprintTasks ?? [],
    input.currentTaskId ?? hero?.task_id ?? null,
    5,
  );

  for (const blueprintUpcoming of upcomingCandidates) {
    const personal = scopedTasks.find((task) => task.task_id === blueprintUpcoming.task_id);
    if (!personal) continue;
    if (waitingTask?.task_id === personal.task_id) continue;
    if (hero?.task_id === personal.task_id && hero.status === "in_progress") continue;
    if (isWaitingTask(personal, blueprintUpcoming)) continue;

    lines.push({
      kind: "upcoming",
      label: "Urmează",
      text: resolveTaskDisplayName(personal, blueprintUpcoming),
      taskId: personal.task_id,
      orderId: personal.order_id,
    });
    break;
  }

  if (!lines.some((line) => line.kind === "upcoming")) {
    for (const task of scopedTasks) {
      if (hero?.task_id === task.task_id && hero.status === "in_progress") continue;
      if (waitingTask?.task_id === task.task_id) continue;
      const blueprintTask = blueprintById.get(task.task_id) ?? null;
      if (isWaitingTask(task, blueprintTask)) continue;
      if (task.status !== "assigned") continue;
      lines.push({
        kind: "upcoming",
        label: "Urmează",
        text: resolveTaskDisplayName(task, blueprintTask),
        taskId: task.task_id,
        orderId: task.order_id,
      });
      break;
    }
  }

  return lines;
}

export function buildRecommendationReason(input: {
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
  personalTask?: EmployeeMobileTaskDTO | null;
}): string | null {
  const why = buildWhyItMattersLine(input);
  if (why) return why;

  const personal = input.personalTask;
  if (!personal) return null;
  if (personal.status === "in_progress") return "Taskul tău activ acum.";
  if (personal.status === "blocked") return "Task blocat — verifică motivul.";
  if (personal.status === "assigned" && personal.is_startable) return "Poți începe acest task.";
  if (personal.status === "assigned") return "Task alocat — verifică dacă poți începe.";
  return null;
}

export type OperationalTaskBucket = "in_progress" | "can_start" | "waiting" | "upcoming" | "later";

const OPERATIONAL_BUCKET_ORDER: Record<OperationalTaskBucket, number> = {
  in_progress: 0,
  can_start: 1,
  waiting: 2,
  upcoming: 3,
  later: 4,
};

export function getOperationalTaskBucket(task: EmployeeMobileTaskDTO): OperationalTaskBucket {
  if (task.status === "in_progress") return "in_progress";
  if (task.status === "blocked") return "waiting";
  const readiness = task.readiness_status;
  if (readiness === "waiting_predecessor" || readiness === "waiting_material") return "waiting";
  if (task.status === "assigned" && task.is_startable === true) return "can_start";
  if (task.status === "assigned") return "upcoming";
  return "later";
}

export function sortTasksOperational(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {
  return [...tasks].sort((left, right) => {
    const leftBucket = OPERATIONAL_BUCKET_ORDER[getOperationalTaskBucket(left)];
    const rightBucket = OPERATIONAL_BUCKET_ORDER[getOperationalTaskBucket(right)];
    if (leftBucket !== rightBucket) return leftBucket - rightBucket;
    return resolveTaskDisplayName(left).localeCompare(resolveTaskDisplayName(right), "ro");
  });
}

export function getOperationalStatusLabel(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): string {
  const bucket = getOperationalTaskBucket(task);
  if (bucket === "can_start") return "Poate începe";
  if (bucket === "upcoming") return "Urmează";
  if (bucket === "later") return "Mai târziu";
  return simplifyStatusLabel({
    readinessStatus: blueprintTask?.readiness_status ?? task.readiness_status,
    readinessLabel: blueprintTask?.readiness_label ?? task.readiness_label,
    statusDisplay: blueprintTask?.status_display,
    status: task.status,
  });
}

export function buildTaskCardExplanation(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): string | null {
  return buildWhyItMattersLine({ personalTask: task, blueprintTask });
}

export function collectBeforeYouStartLines(input: {
  task: EmployeeMobileTaskDTO;
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
}): string[] {
  const lines: string[] = [];
  const warning = input.blueprintTask?.dependency_warning ?? input.task.dependency_warning;
  if (warning) lines.push(String(warning));

  const reasons = input.blueprintTask?.readiness_reasons ?? input.task.readiness_reasons ?? [];
  for (const reason of reasons) {
    const message = reason.message?.trim();
    if (message) lines.push(message);
  }

  const hint = input.blueprintTask?.material_hints?.[0];
  if (hint?.display_note) {
    lines.push(String(hint.display_note));
  } else if (hint?.label && hint.label !== "Verifică material") {
    lines.push(`${hint.name}: ${hint.label}`);
  }

  return lines;
}

export function formatInstructionsAsLines(text: string): string[] {
  const trimmed = text.trim();
  if (!trimmed) return [];
  const lines = trimmed
    .split(/\r?\n/)
    .map((line) => line.replace(/^[\s\-•*]+/, "").trim())
    .filter(Boolean);
  return lines.length > 1 ? lines : [trimmed];
}

export const BLOCK_REASON_CATEGORIES = [
  { id: "material", label: "Material" },
  { id: "instruction", label: "Instrucțiune" },
  { id: "technical", label: "Problemă tehnică" },
  { id: "colleague", label: "Aștept coleg" },
  { id: "other", label: "Alt motiv" },
] as const;

export type BlockReasonCategoryId = (typeof BLOCK_REASON_CATEGORIES)[number]["id"];

export function composeBlockedReason(
  categoryId: BlockReasonCategoryId,
  detail?: string | null,
): string {
  const category =
    BLOCK_REASON_CATEGORIES.find((item) => item.id === categoryId)?.label ?? "Alt motiv";
  const trimmed = detail?.trim();
  if (trimmed) return `[${category}] ${trimmed}`;
  return `[${category}]`;
}
