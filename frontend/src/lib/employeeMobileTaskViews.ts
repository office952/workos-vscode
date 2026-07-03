import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  groupTasksByOrder,
  isActiveEmployeeMobileTask,
  pickBlockedTasks,
  pickHeroTask,
  pickInstallationTasks,
  pickTodayTasks,
  pickUpcomingTasks,
  type OrderTaskSummary,
} from "@/lib/employeeMobileTaskSummary";

export type EmployeeMobileTaskView =
  | "today"
  | "pipeline"
  | "all"
  | "assigned"
  | "in_progress"
  | "blocked"
  | "done"
  | "orders"
  | "installations"
  | "upcoming";

export const EMPLOYEE_MOBILE_TASK_VIEWS: EmployeeMobileTaskView[] = [
  "today",
  "pipeline",
  "all",
  "assigned",
  "in_progress",
  "blocked",
  "done",
  "orders",
  "installations",
  "upcoming",
];

export const EMPLOYEE_MOBILE_TASK_VIEW_LABELS: Record<EmployeeMobileTaskView, string> = {
  today: "Azi",
  pipeline: "Tot fluxul",
  all: "Ale mele",
  assigned: "De făcut",
  in_progress: "În lucru",
  blocked: "Blocate",
  done: "Finalizate",
  orders: "Comenzi",
  installations: "Montaje",
  upcoming: "Urmează",
};

export const EMPLOYEE_MOBILE_TASK_VIEW_DESCRIPTIONS: Record<EmployeeMobileTaskView, string> = {
  today: "Ce ai de făcut acum — pas cu pas.",
  pipeline: "Tot fluxul comenzii — toate pașii în ordine.",
  all: "Toate taskurile tale atribuite.",
  assigned: "Taskuri pregătite pentru începere.",
  in_progress: "Taskuri pe care lucrezi acum.",
  blocked: "Taskuri oprite — verifică motivul blocării.",
  done: "Taskuri finalizate recent.",
  orders: "Lucrările unde ai taskuri active.",
  installations: "Montaje detectate din datele reale ale taskurilor.",
  upcoming: "Posibil următor — în funcție de ordine și disponibilitate.",
};

export function parseEmployeeMobileTaskView(raw: string | null): EmployeeMobileTaskView {
  if (raw && EMPLOYEE_MOBILE_TASK_VIEWS.includes(raw as EmployeeMobileTaskView)) {
    return raw as EmployeeMobileTaskView;
  }
  return "today";
}

export function buildEmployeeMobileTasksPath(
  view: EmployeeMobileTaskView = "today",
  orderId?: number | null,
): string {
  const params = new URLSearchParams();
  if (view !== "today") params.set("view", view);
  if (orderId != null && Number.isFinite(orderId)) params.set("orderId", String(orderId));
  const query = params.toString();
  return query ? `/employee-app/tasks?${query}` : "/employee-app/tasks";
}

export function buildEmployeeMobileTaskDetailPath(
  task: Pick<EmployeeMobileTaskDTO, "task_id" | "order_id">,
  view: EmployeeMobileTaskView = "today",
): string {
  const params = new URLSearchParams();
  if (view !== "today") params.set("view", view);
  params.set("taskId", task.task_id);
  params.set("orderId", String(task.order_id));
  return `/employee-app/tasks?${params.toString()}`;
}

/** Tasks the operator can act on today — excludes waiting predecessors. */
export function filterTodayActionableTasks(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {
  return tasks.filter((task) => {
    if (!isActiveEmployeeMobileTask(task)) return false;
    if (task.status === "in_progress" || task.status === "blocked") return true;
    if (task.status === "assigned" && task.is_startable === true) return true;
    return false;
  });
}

export function summarizeEmployeeMobileTaskCounts(tasks: EmployeeMobileTaskDTO[]) {
  let assigned = 0;
  let inProgress = 0;
  let blocked = 0;
  let done = 0;
  for (const task of tasks) {
    if (task.status === "assigned") assigned += 1;
    else if (task.status === "in_progress") inProgress += 1;
    else if (task.status === "blocked") blocked += 1;
    else if (task.status === "done") done += 1;
  }
  const active = assigned + inProgress + blocked;
  return { active, assigned, inProgress, blocked, done, total: tasks.length };
}

export function filterTasksForView(
  tasks: EmployeeMobileTaskDTO[],
  view: EmployeeMobileTaskView,
  orderId?: number | null,
): EmployeeMobileTaskDTO[] {
  const hero = pickHeroTask(tasks).task;

  switch (view) {
    case "today":
    case "pipeline":
      return [];
    case "assigned":
      return tasks.filter((task) => task.status === "assigned");
    case "in_progress":
      return tasks.filter((task) => task.status === "in_progress");
    case "blocked":
      return pickBlockedTasks(tasks);
    case "done":
      return tasks
        .filter((task) => task.status === "done")
        .sort((a, b) => String(b.completed_at).localeCompare(String(a.completed_at)));
    case "installations":
      return pickInstallationTasks(tasks);
    case "upcoming":
      return pickUpcomingTasks(tasks, hero);
    case "all":
      return tasks.filter(
        (task) => isActiveEmployeeMobileTask(task) || task.status === "done",
      );
    case "orders":
      if (orderId != null) {
        return tasks.filter((task) => task.order_id === orderId);
      }
      return tasks.filter(isActiveEmployeeMobileTask);
    default:
      return tasks;
  }
}

export function listOrdersForTasksView(tasks: EmployeeMobileTaskDTO[]): OrderTaskSummary[] {
  return groupTasksByOrder(tasks);
}

export function countTodayTasks(tasks: EmployeeMobileTaskDTO[]): number {
  return pickTodayTasks(tasks, 100).length;
}

export function countUpcomingTasks(tasks: EmployeeMobileTaskDTO[]): number {
  return pickUpcomingTasks(tasks, pickHeroTask(tasks).task).length;
}

export function countInstallationTasks(tasks: EmployeeMobileTaskDTO[]): number {
  return pickInstallationTasks(tasks).length;
}

export function countActiveOrders(tasks: EmployeeMobileTaskDTO[]): number {
  return listOrdersForTasksView(tasks).length;
}
