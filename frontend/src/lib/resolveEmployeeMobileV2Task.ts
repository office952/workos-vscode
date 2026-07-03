import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

export const EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE =
  "Taskul nu este disponibil pentru acest angajat sau nu mai poate fi accesat.";

export function resolveEmployeeMobileV2Task({
  taskId,
  orderId,
  myTasks,
  availableTasks,
}: {
  taskId: string | undefined;
  orderId: number | null;
  myTasks: EmployeeMobileTaskDTO[];
  availableTasks: EmployeeMobileTaskDTO[];
}): EmployeeMobileTaskDTO | null {
  if (!taskId) return null;

  const matchesTaskId = (task: EmployeeMobileTaskDTO) => task.task_id === taskId;

  if (orderId != null) {
    const owned = myTasks.find((task) => matchesTaskId(task) && task.order_id === orderId);
    if (owned) return owned;
    const available = availableTasks.find(
      (task) => matchesTaskId(task) && task.order_id === orderId,
    );
    return available ?? null;
  }

  return (
    myTasks.find((task) => matchesTaskId(task)) ??
    availableTasks.find((task) => matchesTaskId(task)) ??
    null
  );
}

export function isEmployeeMobileV2TaskPreview(task: EmployeeMobileTaskDTO | null): boolean {
  if (!task) return false;
  if (task.preview_only === true) return true;
  return task.claimable === true && task.access_mode === "available_preview";
}
