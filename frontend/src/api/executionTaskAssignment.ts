import { getAPIBaseURL } from "@/lib/config";

export interface AssignExecutionTaskResult {
  plan_id: number;
  order_id: number;
  order_code: string;
  task_id: string;
  assigned_employee_id: number;
  assigned_employee_name: string;
  task: Record<string, unknown>;
}

export interface UpdateExecutionTaskInstructionsResult {
  plan_id: number;
  order_id: number;
  order_code: string;
  task_id: string;
  instructions: string;
  task: Record<string, unknown>;
}

export async function assignExecutionPlanTask(
  orderId: number,
  taskId: string,
  assignedEmployeeId: number,
): Promise<AssignExecutionTaskResult> {
  const response = await fetch(
    `${getAPIBaseURL()}/api/v1/execution/plan/${orderId}/tasks/${encodeURIComponent(taskId)}/assign`,
    {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assigned_employee_id: assignedEmployeeId }),
    },
  );
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const detail = await response.json();
      if (detail?.detail?.error) message = String(detail.detail.error);
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }
  return response.json();
}

export async function updateExecutionPlanTaskInstructions(
  orderId: number,
  taskId: string,
  instructions: string,
): Promise<UpdateExecutionTaskInstructionsResult> {
  const response = await fetch(
    `${getAPIBaseURL()}/api/v1/execution/plan/${orderId}/tasks/${encodeURIComponent(taskId)}/instructions`,
    {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instructions }),
    },
  );
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const detail = await response.json();
      if (detail?.detail?.error) message = String(detail.detail.error);
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }
  return response.json();
}
