/**
 * Employee-mobile self-only execution tasks — no client employee_id authority.
 */
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/employee-mobile/tasks`;

export type EmployeeMobileTaskStatus =
  | "assigned"
  | "in_progress"
  | "blocked"
  | "paused"
  | "done";

export interface EmployeeMobileTaskDTO {
  contract_version?: string;
  task_id: string;
  order_id: number;
  order_code?: string;
  title?: string;
  display_label?: string;
  description?: string;
  instructions?: string;
  status: EmployeeMobileTaskStatus;
  process_type?: string;
  machine_type?: string;
  estimated_time_minutes?: number;
  assigned_employee_id?: number | null;
  employee_id?: number | null;
  employee_name?: string | null;
  client?: string;
  product?: string;
  quote_code?: string;
  intake_code?: string;
  order_status?: string;
  started_at?: string | null;
  completed_at?: string | null;
  blocked_at?: string | null;
  blocked_reason?: string | null;
  deterministic_task_key?: string | null;
  component_label?: string | null;
  component_role?: string | null;
  operation_label?: string | null;
  logo_segment_label?: string | null;
  identity_source?: "frozen_task_identity/v1" | "legacy_plan_task" | "not_proven" | string;
  identity_classification?: string | null;
  execution_plan_id?: number | null;
  legacy_mode?: boolean;
  legacy_fallback_active?: boolean;
  task_identity_version?: string | null;
  readiness_authority?: string | null;
  release_authority?: string | null;
  execution_source?: string | null;
  production_release_blocked?: boolean;
  production_blocker_summary?: string | null;
  is_assigned_to_current_employee?: boolean;
  is_available_for_claim?: boolean;
  can_claim?: boolean;
  can_start?: boolean;
  can_start_from_available?: boolean;
  can_complete?: boolean;
  /** Phase 3 collaboration capabilities — backend truth only. */
  visible_as_principal?: boolean;
  visible_as_helper?: boolean;
  can_view_help?: boolean;
  can_accept_help?: boolean;
  can_start_helper_work?: boolean;
  can_stop_own_session?: boolean;
  can_complete_operation?: boolean;
  can_request_help?: boolean;
  can_cancel_help?: boolean;
  assignment_source?: string | null;
  documents?: Array<{
    id?: string;
    name?: string;
    type?: string;
    url?: string;
    source?: string;
    label?: string;
    [key: string]: unknown;
  }>;
  clarification_request?: {
    id: number;
    order_id: number;
    task_id: string;
    employee_id: number;
    message?: string;
    status?: string;
    created_at?: string | null;
  } | null;
  readiness_status?: string;
  readiness_label?: string;
  is_startable?: boolean;
  readiness_reasons?: Array<{
    code?: string;
    task_id?: string;
    task_name?: string;
    message?: string;
  }>;
  blocking_task_ids?: string[];
  blocking_tasks?: Array<{ task_id: string; name: string }>;
  dependency_warning?: string | null;
  material_warning?: string | null;
  active_helper_count?: number;
  preparation_domain?: string | null;
  eligibility_reason?: string | null;
  claimable?: boolean;
  access_mode?: "owned" | "available_preview" | string;
  preview_only?: boolean;
  /** Plan order index for sorting available tasks (from backend). */
  plan_sequence?: number;
}

export interface EmployeeMobileTaskTruthResponse {
  contract_version: string;
  employee_id: number;
  employee_display_name?: string;
  generated_at: string;
  source?: string;
  legacy_mode?: boolean;
  summary?: {
    total_tasks: number;
    assigned_count: number;
    available_count: number;
    startable_count: number;
    blocked_count: number;
  };
  capabilities?: {
    can_claim_available?: boolean;
    can_resolve_owner_decisions?: boolean;
    can_view_internal_cost?: boolean;
  };
  tasks: EmployeeMobileTaskDTO[];
}

export async function fetchEmployeeMobileTaskTruth(): Promise<EmployeeMobileTaskTruthResponse> {
  const response = await fetch(`${base()}/truth`, { credentials: "include" });
  if (!response.ok) await parseError(response);
  return response.json();
}

export interface EmployeeMobileClaimResult {
  status: string;
  action: string;
  task_id: string;
  order_id: number;
  assigned_employee_id: number;
  assigned_employee_name?: string | null;
  already_claimed?: boolean;
}

export type EmployeeMobileTaskError = Error & { code?: string };

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
      ? ((detail as { detail: Record<string, unknown> }).detail ?? null)
      : null;
  const message =
    nested && typeof nested.message === "string"
      ? nested.message
      : nested && typeof nested.error === "string"
        ? nested.error
        : `Request failed (${response.status})`;
  const error = new Error(message) as EmployeeMobileTaskError;
  if (nested && typeof nested.error === "string") {
    error.code = nested.error;
  } else if (nested && typeof nested.code === "string") {
    error.code = nested.code;
  }
  throw error;
}

export async function listEmployeeMobileTasks(): Promise<EmployeeMobileTaskDTO[]> {
  const response = await fetch(base(), { credentials: "include" });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function listAvailableEmployeeMobileTasks(): Promise<EmployeeMobileTaskDTO[]> {
  const response = await fetch(`${base()}/available`, { credentials: "include" });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function fetchEmployeeMobileTaskByOrder(
  orderId: number,
  taskId: string,
): Promise<EmployeeMobileTaskDTO> {
  const response = await fetch(
    `${getAPIBaseURL()}/api/v1/employee-mobile/orders/${orderId}/tasks/${encodeURIComponent(taskId)}`,
    { credentials: "include" },
  );
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function claimEmployeeMobileTask(
  taskId: string,
  orderId: number,
): Promise<EmployeeMobileClaimResult> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/claim`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function startEmployeeMobileTaskFromAvailable(
  taskId: string,
  orderId: number,
): Promise<unknown> {
  const response = await fetch(
    `${base()}/${encodeURIComponent(taskId)}/start-from-available`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId }),
    },
  );
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function startEmployeeMobileTask(
  taskId: string,
  orderId: number,
): Promise<unknown> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/start`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function blockEmployeeMobileTask(
  taskId: string,
  orderId: number,
  reason?: string,
): Promise<unknown> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/block`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId, reason: reason?.trim() || undefined }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function completeEmployeeMobileTask(
  taskId: string,
  orderId: number,
): Promise<unknown> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/complete`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function unblockEmployeeMobileTask(
  taskId: string,
  orderId: number,
): Promise<unknown> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/unblock`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function pauseEmployeeMobileTask(
  taskId: string,
  orderId: number,
): Promise<unknown> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/pause`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export async function resumeEmployeeMobileTask(
  taskId: string,
  orderId: number,
): Promise<unknown> {
  const response = await fetch(`${base()}/${encodeURIComponent(taskId)}/resume`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId }),
  });
  if (!response.ok) await parseError(response);
  return response.json();
}

export function countActiveEmployeeMobileTasks(tasks: EmployeeMobileTaskDTO[]): {
  total: number;
  assigned: number;
  inProgress: number;
  blocked: number;
} {
  let assigned = 0;
  let inProgress = 0;
  let blocked = 0;
  for (const task of tasks) {
    if (task.status === "assigned") assigned += 1;
    else if (task.status === "in_progress") inProgress += 1;
    else if (task.status === "blocked") blocked += 1;
  }
  return {
    total: assigned + inProgress + blocked,
    assigned,
    inProgress,
    blocked,
  };
}

export const EMPLOYEE_MOBILE_TASK_STATUS_LABELS: Record<EmployeeMobileTaskStatus, string> = {
  assigned: "De făcut",
  in_progress: "În lucru",
  blocked: "Blocat",
  paused: "Întrerupt temporar",
  done: "Finalizat",
};

export const EMPLOYEE_MOBILE_TASK_GROUP_LABELS = {
  assigned: "De făcut",
  in_progress: "În lucru",
  blocked: "Blocate",
  done: "Finalizate recent",
} as const;

export const EMPLOYEE_MOBILE_CLAIM_ERROR_LABELS: Record<string, string> = {
  task_already_assigned: "Taskul este deja preluat de alt coleg",
  employee_not_eligible: "Nu ești eligibil pentru acest task",
  task_not_claimable: "Nu am putut prelua taskul",
  task_has_active_session: "Taskul este deja preluat de alt coleg",
};

export function mapEmployeeMobileClaimError(message: string): string {
  const normalized = message.trim();
  if (EMPLOYEE_MOBILE_CLAIM_ERROR_LABELS[normalized]) {
    return EMPLOYEE_MOBILE_CLAIM_ERROR_LABELS[normalized];
  }
  if (normalized.includes("deja preluat") || normalized.includes("alt coleg")) {
    return "Taskul este deja preluat de alt coleg";
  }
  if (normalized.includes("eligibil")) {
    return "Nu ești eligibil pentru acest task";
  }
  return normalized || "Nu am putut prelua taskul";
}

export function mapEmployeeMobileStartFromAvailableError(err: unknown): string {
  const error = err as EmployeeMobileTaskError;
  const code = error.code ?? "";
  if (code === "task_not_ready") {
    return error.message || "Taskul nu este încă pregătit";
  }
  if (code === "task_already_assigned") {
    return "Taskul este deja preluat de alt coleg";
  }
  if (code === "employee_not_eligible") {
    return "Nu ești eligibil pentru acest task";
  }
  if (code === "task_has_active_session") {
    return "Taskul este deja preluat de alt coleg";
  }
  const message = error instanceof Error ? error.message : "";
  if (message.includes("eligibil")) {
    return "Nu ești eligibil pentru acest task";
  }
  return message || "Nu am putut începe lucrul";
}
