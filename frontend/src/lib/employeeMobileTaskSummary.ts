import type { EmployeeMobileTaskDTO, EmployeeMobileTaskStatus } from "@/api/employeeMobileTasks";

const ACTIVE_STATUSES: EmployeeMobileTaskStatus[] = ["assigned", "in_progress", "blocked"];

const INSTALLATION_KEYWORDS = [
  "montaj",
  "installation",
  "install",
  "field_install",
  "field installation",
  "teren",
  "la beneficiar",
];

export type HeroTaskMode = "working" | "blocked" | "next" | "empty";

export interface HeroTaskSelection {
  task: EmployeeMobileTaskDTO | null;
  mode: HeroTaskMode;
}

export interface OrderTaskSummary {
  orderId: number;
  orderCode?: string;
  client?: string;
  product?: string;
  tasks: EmployeeMobileTaskDTO[];
  activeCount: number;
  doneCount: number;
}

export function isActiveEmployeeMobileTask(task: EmployeeMobileTaskDTO): boolean {
  return ACTIVE_STATUSES.includes(task.status);
}

export function pickHeroTask(tasks: EmployeeMobileTaskDTO[]): HeroTaskSelection {
  const active = tasks.filter(isActiveEmployeeMobileTask);
  const inProgress = active.find((task) => task.status === "in_progress");
  if (inProgress) return { task: inProgress, mode: "working" };

  const blocked = active.find((task) => task.status === "blocked");
  if (blocked) return { task: blocked, mode: "blocked" };

  const assigned = active.find((task) => task.status === "assigned");
  if (assigned) return { task: assigned, mode: "next" };

  return { task: null, mode: "empty" };
}

export function pickTodayTasks(tasks: EmployeeMobileTaskDTO[], limit = 5): EmployeeMobileTaskDTO[] {
  return tasks.filter(isActiveEmployeeMobileTask).slice(0, limit);
}

export function pickBlockedTasks(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {
  return tasks.filter((task) => task.status === "blocked");
}

export function pickUpcomingTasks(
  tasks: EmployeeMobileTaskDTO[],
  heroTask: EmployeeMobileTaskDTO | null,
): EmployeeMobileTaskDTO[] {
  return tasks.filter((task) => {
    if (task.status !== "assigned") return false;
    if (!heroTask) return true;
    return !(task.task_id === heroTask.task_id && task.order_id === heroTask.order_id);
  });
}

export function groupTasksByOrder(tasks: EmployeeMobileTaskDTO[]): OrderTaskSummary[] {
  const map = new Map<number, OrderTaskSummary>();

  for (const task of tasks) {
    let entry = map.get(task.order_id);
    if (!entry) {
      entry = {
        orderId: task.order_id,
        orderCode: task.order_code,
        client: task.client,
        product: task.product,
        tasks: [],
        activeCount: 0,
        doneCount: 0,
      };
      map.set(task.order_id, entry);
    }

    entry.tasks.push(task);
    if (isActiveEmployeeMobileTask(task)) entry.activeCount += 1;
    else if (task.status === "done") entry.doneCount += 1;

    if (!entry.orderCode && task.order_code) entry.orderCode = task.order_code;
    if (!entry.client && task.client) entry.client = task.client;
    if (!entry.product && task.product) entry.product = task.product;
  }

  return Array.from(map.values())
    .filter((entry) => entry.activeCount > 0)
    .sort((a, b) => b.activeCount - a.activeCount || a.orderId - b.orderId);
}

export function formatOrderLabel(summary: OrderTaskSummary): string {
  if (summary.orderCode) return summary.orderCode;
  if (summary.client) return `Comandă #${summary.orderId} · ${summary.client}`;
  return `Comandă #${summary.orderId}`;
}

export function isInstallationTask(task: EmployeeMobileTaskDTO): boolean {
  const haystack = [task.process_type, task.machine_type, task.title, task.description]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (!haystack) return false;
  return INSTALLATION_KEYWORDS.some((keyword) => haystack.includes(keyword));
}

export function pickInstallationTasks(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {
  return tasks.filter((task) => isActiveEmployeeMobileTask(task) && isInstallationTask(task));
}

export const HERO_SECTION_TITLES: Record<HeroTaskMode, string> = {
  working: "Lucrezi acum",
  blocked: "Ai un blocaj",
  next: "Următorul task",
  empty: "Nu ai taskuri active",
};
