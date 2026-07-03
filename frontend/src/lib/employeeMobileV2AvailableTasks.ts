import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

export interface AvailableTasksPartition {
  startable: EmployeeMobileTaskDTO[];
  waiting: EmployeeMobileTaskDTO[];
}

function planSequenceOf(task: EmployeeMobileTaskDTO): number {
  const seq = (task as EmployeeMobileTaskDTO & { plan_sequence?: number }).plan_sequence;
  if (typeof seq === "number" && Number.isFinite(seq)) return seq;
  const match = /^T-(\d+)$/i.exec(String(task.task_id || ""));
  if (match) return Number.parseInt(match[1], 10);
  return 9999;
}

export function sortAvailableTasksByPlan(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO[] {
  return [...tasks].sort((a, b) => {
    const seqDiff = planSequenceOf(a) - planSequenceOf(b);
    if (seqDiff !== 0) return seqDiff;
    if (a.order_id !== b.order_id) return a.order_id - b.order_id;
    return String(a.title || a.task_id).localeCompare(String(b.title || b.task_id), "ro");
  });
}

export function isAvailableTaskStartable(task: EmployeeMobileTaskDTO): boolean {
  return task.is_startable === true;
}

export function partitionAvailableTasks(tasks: EmployeeMobileTaskDTO[]): AvailableTasksPartition {
  const sorted = sortAvailableTasksByPlan(tasks);
  const startable: EmployeeMobileTaskDTO[] = [];
  const waiting: EmployeeMobileTaskDTO[] = [];
  for (const task of sorted) {
    if (isAvailableTaskStartable(task)) {
      startable.push(task);
    } else {
      waiting.push(task);
    }
  }
  return { startable, waiting };
}

/** User-facing waiting reason — Romanian only, no English slugs. */
export function resolveAvailableTaskWaitingLabel(task: EmployeeMobileTaskDTO): string {
  const status = String(task.readiness_status || "").toLowerCase();
  if (status === "waiting_predecessor") return "Așteaptă task anterior";
  if (status === "waiting_file" || status === "waiting_template_decision") {
    return "Așteaptă fișierul/vectorul";
  }
  if (status === "waiting_material") return "Așteaptă material";
  if (status === "blocked" || task.status === "blocked") return "Blocat";

  const label = String(task.readiness_label || "").trim();
  if (label && !/^unassigned$/i.test(label) && !/^neatribuit$/i.test(label)) {
    return label;
  }

  const firstBlock = task.blocking_tasks?.[0]?.name || task.blocking_task_ids?.[0];
  if (firstBlock) return `Așteaptă task anterior`;

  return "Taskul nu este încă pregătit";
}

export function countStartableAvailableTasks(tasks: EmployeeMobileTaskDTO[]): number {
  return tasks.filter(isAvailableTaskStartable).length;
}
