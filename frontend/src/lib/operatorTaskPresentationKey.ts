import type { OperatorTask } from "@/lib/mockData";

/**
 * Stable React / UI-state presentation key for operator task rows.
 *
 * Backend task_id may legitimately repeat across orders (same operation node
 * on different jobs). Domain identity for API calls remains (orderId, task_id);
 * this key is presentation-only and must not invent or merge records.
 */
export function operatorTaskPresentationKey(task: Pick<OperatorTask, "jobId" | "id">): string {
  return `${task.jobId}::${task.id}`;
}
