/**
 * Employee-mobile task clarification requests — production info asks, not block.
 */
import { getAPIBaseURL } from "@/lib/config";

const mobileBase = () => `${getAPIBaseURL()}/api/v1/employee-mobile`;
const operatorBase = () => `${getAPIBaseURL()}/api/v1/operator`;

export interface TaskClarificationRequestDTO {
  id: number;
  order_id: number;
  task_id: string;
  employee_id: number;
  employee_name?: string;
  message: string;
  status: "open" | "resolved" | "cancelled";
  created_at?: string | null;
  resolved_at?: string | null;
  resolved_by_user_id?: string | null;
  target_user_id?: string | null;
  target_user_name?: string | null;
  routed_to_responsible?: boolean;
}

async function parseError(response: Response): Promise<never> {
  let detail: unknown = null;
  try {
    detail = await response.json();
  } catch {
    detail = { error: response.statusText || "request_failed" };
  }
  const nested =
    typeof detail === "object" &&
    detail !== null &&
    "detail" in detail &&
    typeof (detail as { detail?: unknown }).detail === "object"
      ? (detail as { detail: Record<string, unknown> }).detail
      : null;
  const message =
    nested && typeof nested.error === "string"
      ? nested.error
      : `Request failed (${response.status})`;
  const error = new Error(message) as Error & { status?: number; payload?: unknown };
  error.status = response.status;
  error.payload = nested ?? detail;
  throw error;
}

export async function createEmployeeMobileTaskClarification(
  taskId: string,
  orderId: number,
  message: string,
): Promise<TaskClarificationRequestDTO> {
  const response = await fetch(
    `${mobileBase()}/tasks/${encodeURIComponent(taskId)}/clarification-requests`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId, message: message.trim() }),
    },
  );
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function listOperatorClarificationRequests(
  status: string = "open",
): Promise<TaskClarificationRequestDTO[]> {
  const response = await fetch(
    `${operatorBase()}/clarification-requests?status=${encodeURIComponent(status)}`,
    { credentials: "include" },
  );
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function resolveOperatorClarificationRequest(
  requestId: number,
): Promise<TaskClarificationRequestDTO> {
  const response = await fetch(
    `${operatorBase()}/clarification-requests/${requestId}/resolve`,
    {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    },
  );
  if (!response.ok) await parseError(response);
  return response.json();
}

export function hasOpenClarificationRequest(
  task: { clarification_request?: TaskClarificationRequestDTO | null },
): boolean {
  return task.clarification_request?.status === "open";
}
