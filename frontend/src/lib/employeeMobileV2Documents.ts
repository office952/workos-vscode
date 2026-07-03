import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileTaskDocument } from "@/lib/employeeMobileTaskDocuments";
import { normalizeTaskDocuments } from "@/lib/employeeMobileTaskDocuments";
import { pickPrimaryOrderId } from "@/lib/employeeMobilePipelineEligibility";
import { pickHeroTask } from "@/lib/employeeMobileTaskSummary";

export interface AggregatedTaskDocument extends EmployeeMobileTaskDocument {
  taskId: string;
  taskTitle?: string;
}

export function collectDocumentsForOrder(
  tasks: EmployeeMobileTaskDTO[],
  orderId: number | null,
): AggregatedTaskDocument[] {
  const scoped = orderId != null ? tasks.filter((task) => task.order_id === orderId) : tasks;
  const seen = new Set<string>();
  const docs: AggregatedTaskDocument[] = [];

  for (const task of scoped) {
    for (const doc of normalizeTaskDocuments(task.documents)) {
      const key = doc.url || doc.id || `${task.task_id}-${doc.name}`;
      if (seen.has(key)) continue;
      seen.add(key);
      docs.push({
        ...doc,
        taskId: task.task_id,
        taskTitle: task.title,
      });
    }
  }

  return docs;
}

export function resolveDocumentsOrderId(
  tasks: EmployeeMobileTaskDTO[],
  orderIdParam: number | null,
): number | null {
  if (orderIdParam != null && tasks.some((task) => task.order_id === orderIdParam)) {
    return orderIdParam;
  }
  const hero = pickHeroTask(tasks).task;
  if (hero?.order_id != null) return hero.order_id;
  return pickPrimaryOrderId(tasks);
}
