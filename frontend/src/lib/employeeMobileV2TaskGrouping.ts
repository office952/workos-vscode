import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

import type { EmV2StatusPresentation } from "@/lib/employeeMobileV2Status";



export type TaskScopeFilter = "active" | "all" | "done";



export const RECENT_DONE_TASKS_LIMIT = 10;



export interface TaskOrderContext {

  orderId: number;

  orderLabel: string;

  client?: string;

  product?: string;

  line: string;

}



export interface OrderTaskGroup {

  orderId: number;

  orderLabel: string;

  client?: string;

  product?: string;

  tasks: EmployeeMobileTaskDTO[];

  doneCount: number;

  totalCount: number;

  inProgressCount: number;

  blockedCount: number;

  canStartCount: number;

  waitingCount: number;

  summaryStatus: string;

  progressLine: string;

  sortWeight: number;

}



export interface TasksPageMiniSummary {

  title: string;

  line: string;

}



type PriorityGroupKey =

  | "now"

  | "can_start"

  | "waiting"

  | "blocked"

  | "upcoming"

  | "done";



function normalizeHaystack(value: string): string {

  return value

    .toLowerCase()

    .normalize("NFD")

    .replace(/\p{M}/gu, "");

}



function isWaitingTask(task: EmployeeMobileTaskDTO): boolean {

  if (task.status === "blocked") return false;

  if (task.status === "in_progress" || task.status === "done") return false;



  const readiness = String(task.readiness_status ?? "");

  if (readiness === "waiting_predecessor" || readiness === "waiting_material") return true;



  const label = String(task.readiness_label ?? "").toLowerCase();

  if (label.includes("așteaptă") || label.includes("asteapta")) return true;



  if (task.dependency_warning) return true;

  if ((task.blocking_tasks?.length ?? 0) > 0) return true;

  if (task.status === "assigned" && task.is_startable === false) return true;



  return false;

}



export function classifyTaskPriority(task: EmployeeMobileTaskDTO): PriorityGroupKey {

  if (task.status === "in_progress") return "now";

  if (task.status === "blocked") return "blocked";

  if (task.status === "done") return "done";

  if (task.status === "assigned" && task.is_startable === true && !isWaitingTask(task)) {

    return "can_start";

  }

  if (isWaitingTask(task)) return "waiting";

  return "upcoming";

}



function shortenDependencyName(name: string): string {

  const trimmed = name.trim();

  if (trimmed.length <= 32) return trimmed;

  return `${trimmed.slice(0, 30)}…`;

}



function normalizeInProgressDependencyWarning(warning: string): string | null {

  const normalized = normalizeHaystack(warning);

  if (

    normalized.includes("inainte de finalizarea dependentelor") ||

    normalized.includes("pornit inainte")

  ) {

    return "Atenție: dependență pornită înainte de finalizare";

  }

  if (warning.length <= 48) return `Notă: ${warning}`;

  return `Notă: ${warning.slice(0, 46)}…`;

}



export function getTaskInProgressNote(task: EmployeeMobileTaskDTO): string | null {

  if (task.status !== "in_progress") return null;



  if (task.dependency_warning?.trim()) {

    return normalizeInProgressDependencyWarning(task.dependency_warning.trim());

  }



  const blocker = task.blocking_tasks?.[0];

  if (blocker?.name?.trim()) {

    return `Notă: dependență cu ${shortenDependencyName(blocker.name)}`;

  }



  const label = task.readiness_label?.trim();

  if (label) {

    const short = label

      .replace(/^Așteaptă:\s*/i, "")

      .replace(/^Asteapta:\s*/i, "")

      .replace(/^Așteaptă\s+/i, "")

      .replace(/^Asteapta\s+/i, "")

      .trim();

    if (short && short !== label) {

      return `Notă: dependență cu ${shortenDependencyName(short)}`;

    }

  }



  return null;

}



export function getTaskWaitingDetailShort(task: EmployeeMobileTaskDTO): string | null {

  const reason = getTaskWaitingReason(task);

  if (!reason) return null;

  if (reason.startsWith("Așteaptă:")) {

    return reason.slice("Așteaptă:".length).trim() || "task anterior";

  }

  return reason;

}



export function getTaskWaitingReason(task: EmployeeMobileTaskDTO): string | null {

  if (task.status === "in_progress") return null;



  const blocker = task.blocking_tasks?.[0];

  if (blocker?.name) return `Așteaptă: ${blocker.name}`;



  if (task.dependency_warning) {

    const warning = task.dependency_warning.trim();

    if (warning.length > 48) return `${warning.slice(0, 46)}…`;

    return warning;

  }



  const readiness = String(task.readiness_status ?? "");

  if (readiness === "waiting_predecessor") return "task anterior";

  if (readiness === "waiting_material") return "material";



  const label = task.readiness_label?.trim();

  if (label) {

    if (label === "Așteaptă task anterior") return "task anterior";

    if (label === "Așteaptă material") return "material";

    if (label.length <= 32) return label;

    return `${label.slice(0, 30)}…`;

  }



  if (task.status === "blocked" && task.blocked_reason) {

    return task.blocked_reason.length > 40

      ? `${task.blocked_reason.slice(0, 38)}…`

      : task.blocked_reason;

  }



  if (isWaitingTask(task)) return "depinde de alt pas";

  return null;

}



export function getTaskOrderContext(task: EmployeeMobileTaskDTO): TaskOrderContext {

  const orderLabel = task.order_code?.trim() || `Comandă #${task.order_id}`;

  const client = task.client?.trim() || undefined;

  const product = task.product?.trim() || undefined;

  const line = [orderLabel, client].filter(Boolean).join(" · ");

  return {

    orderId: task.order_id,

    orderLabel,

    client,

    product,

    line,

  };

}



export function filterActiveMyTasks(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {

  return tasks.filter((task) => task.status !== "done");

}



export function filterRecentDoneTasks(

  tasks: EmployeeMobileTaskDTO[],

  limit = RECENT_DONE_TASKS_LIMIT,

): EmployeeMobileTaskDTO[] {

  return [...tasks]

    .filter((task) => task.status === "done")

    .sort((left, right) => {

      const leftTs = Date.parse(String(left.completed_at ?? "")) || 0;

      const rightTs = Date.parse(String(right.completed_at ?? "")) || 0;

      return rightTs - leftTs;

    })

    .slice(0, limit);

}



function activeTaskSortWeight(task: EmployeeMobileTaskDTO): number {

  switch (task.status) {

    case "in_progress":

      return 0;

    case "blocked":

      return 1;

    case "paused":

      return 2;

    case "assigned":

      return 3;

    default:

      return 4;

  }

}



export function sortActiveMyTasks(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {

  return [...tasks].sort(

    (left, right) =>

      activeTaskSortWeight(left) - activeTaskSortWeight(right) ||

      String(left.order_code ?? left.order_id).localeCompare(

        String(right.order_code ?? right.order_id),

        "ro",

      ) ||

      String(left.title ?? left.task_id).localeCompare(String(right.title ?? right.task_id), "ro"),

  );

}



export function filterTasksByScope(

  tasks: EmployeeMobileTaskDTO[],

  scope: TaskScopeFilter,

): EmployeeMobileTaskDTO[] {

  switch (scope) {

    case "done":

      return tasks.filter((task) => task.status === "done");

    case "all":

      return tasks;

    case "active":

    default:

      return tasks.filter((task) => task.status !== "done");

  }

}



function groupSortWeight(tasks: EmployeeMobileTaskDTO[]): number {

  if (tasks.some((task) => task.status === "in_progress")) return 0;

  if (tasks.some((task) => task.status === "blocked")) return 1;

  if (tasks.some((task) => classifyTaskPriority(task) === "can_start")) return 2;

  if (tasks.some((task) => classifyTaskPriority(task) === "waiting")) return 3;

  return 4;

}



function summarizeOrderGroupStatus(group: Omit<OrderTaskGroup, "summaryStatus" | "progressLine" | "sortWeight">): string {

  if (group.inProgressCount > 0) return "În lucru";

  if (group.blockedCount > 0) return "Blocat";

  if (group.canStartCount > 0) return "Poate începe";

  if (group.waitingCount > 0) return "Așteaptă";

  if (group.doneCount === group.totalCount) return "Finalizat";

  return "Așteaptă";

}



export function groupTasksByOrder(tasks: EmployeeMobileTaskDTO[]): OrderTaskGroup[] {

  const map = new Map<number, OrderTaskGroup>();



  for (const task of tasks) {

    let entry = map.get(task.order_id);

    if (!entry) {

      const ctx = getTaskOrderContext(task);

      entry = {

        orderId: task.order_id,

        orderLabel: ctx.orderLabel,

        client: ctx.client,

        product: ctx.product,

        tasks: [],

        doneCount: 0,

        totalCount: 0,

        inProgressCount: 0,

        blockedCount: 0,

        canStartCount: 0,

        waitingCount: 0,

        summaryStatus: "",

        progressLine: "",

        sortWeight: 0,

      };

      map.set(task.order_id, entry);

    }



    entry.tasks.push(task);

    entry.totalCount += 1;

    if (task.status === "done") entry.doneCount += 1;

    if (task.status === "in_progress") entry.inProgressCount += 1;

    if (task.status === "blocked") entry.blockedCount += 1;

    if (classifyTaskPriority(task) === "can_start") entry.canStartCount += 1;

    if (classifyTaskPriority(task) === "waiting") entry.waitingCount += 1;



    if (!entry.client && task.client) entry.client = task.client;

    if (!entry.product && task.product) entry.product = task.product;

    if (!entry.orderLabel && task.order_code) entry.orderLabel = task.order_code;

  }



  const groups = Array.from(map.values()).map((group) => {

    const parts = [`${group.doneCount}/${group.totalCount} finalizate`];

    if (group.inProgressCount > 0) parts.push(`${group.inProgressCount} în lucru`);

    if (group.blockedCount > 0) parts.push(`${group.blockedCount} blocate`);

    if (group.canStartCount > 0) parts.push(`${group.canStartCount} pot începe`);



    return {

      ...group,

      summaryStatus: summarizeOrderGroupStatus(group),

      progressLine: parts.join(" · "),

      sortWeight: groupSortWeight(group.tasks),

    };

  });



  return groups.sort((left, right) => left.sortWeight - right.sortWeight || left.orderLabel.localeCompare(right.orderLabel, "ro"));

}



export function buildTasksPageMiniSummary(

  tasks: EmployeeMobileTaskDTO[],

  options?: {

    currentStepIndex?: number | null;

    totalSteps?: number | null;

  },

): TasksPageMiniSummary {

  const scoped = filterTasksByScope(tasks, "active");

  const inProgress = scoped.filter((task) => task.status === "in_progress").length;

  const canStart = scoped.filter((task) => classifyTaskPriority(task) === "can_start").length;

  const waiting = scoped.filter((task) => classifyTaskPriority(task) === "waiting").length;

  const blocked = scoped.filter((task) => task.status === "blocked").length;



  const orderGroups = groupTasksByOrder(scoped);

  const singleOrder =

    orderGroups.length === 1

      ? orderGroups[0]

      : orderGroups.length === 0 && scoped.length > 0

        ? groupTasksByOrder(tasks)[0]

        : null;



  if (singleOrder && options?.currentStepIndex != null && options.totalSteps != null) {

    return {

      title: "Azi în producție",

      line: `${singleOrder.orderLabel} · pas ${options.currentStepIndex}/${options.totalSteps}`,

    };

  }



  if (orderGroups.length === 1 && singleOrder) {

    const parts: string[] = [];

    if (inProgress > 0) parts.push(`${inProgress} în lucru`);

    if (canStart > 0) parts.push(`${canStart} pot începe`);

    if (waiting > 0) parts.push(`${waiting} așteaptă`);

    if (blocked > 0) parts.push(`${blocked} blocate`);

    return {

      title: "Azi în producție",

      line: parts.length > 0 ? parts.join(" · ") : singleOrder.progressLine,

    };

  }



  if (orderGroups.length > 1) {

    return {

      title: "Azi în producție",

      line: `${orderGroups.length} comenzi active · ${scoped.length} taskuri ale tale`,

    };

  }



  const parts: string[] = [];

  if (inProgress > 0) parts.push(`${inProgress} în lucru`);

  if (canStart > 0) parts.push(`${canStart} pot începe`);

  if (waiting > 0) parts.push(`${waiting} așteaptă`);

  if (blocked > 0) parts.push(`${blocked} blocate`);



  return {

    title: "Azi în producție",

    line: parts.length > 0 ? parts.join(" · ") : "Niciun task activ acum",

  };

}



export function suppressDuplicateWaitingDetail(

  presentation: EmV2StatusPresentation,

  contextLine: string | null,

): EmV2StatusPresentation {

  if (!presentation.detailLine || !contextLine) return presentation;

  if (presentation.shortLabel !== "Așteaptă") return presentation;



  const normalizedContext = normalizeHaystack(contextLine);

  const normalizedDetail = normalizeHaystack(presentation.detailLine);

  if (

    normalizedContext.includes("asteapta") ||

    normalizedContext.includes(normalizedDetail) ||

    normalizedDetail.includes("task anterior") && normalizedContext.includes("asteapta")

  ) {

    return { ...presentation, detailLine: null };

  }

  return presentation;

}



export function buildTaskRowContextLine(task: EmployeeMobileTaskDTO): string | null {

  const orderCtx = getTaskOrderContext(task);



  if (task.status === "in_progress") {

    const note = getTaskInProgressNote(task);

    return note ?? task.product?.trim() ?? orderCtx.client ?? null;

  }



  const waitingReason = getTaskWaitingReason(task);

  if (waitingReason) return waitingReason;

  if (task.product) return task.product;

  return orderCtx.client ?? null;

}

