/**
 * Flex collaboration API client — Phase 3 human loop.
 * Operator + Employee Mobile V2 surfaces; capabilities come from backend only.
 */
import { getAPIBaseURL } from "@/lib/config";

const operatorBase = () => `${getAPIBaseURL()}/api/v1/operator`;
const mobileBase = () => `${getAPIBaseURL()}/api/v1/employee-mobile`;

export type HelpStatus = "OPEN" | "CANCELLED" | "DECLINED" | "CLOSED";

export interface HelpRequestDTO {
  help_request_id: number;
  order_id: number;
  task_id: string;
  requested_by_employee_id: number;
  targeted_employee_id?: number | null;
  status: HelpStatus;
  reason?: string | null;
  competence_hint?: string | null;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  is_broadcast: boolean;
}

export interface HelperMembershipDTO {
  employee_id: number;
  employee_name?: string | null;
  status: "active" | "inactive";
  role?: "helper";
  joined_at: string;
  left_at?: string | null;
  join_source?: string | null;
  membership_id?: number | null;
}

export interface ActualWorkerDTO {
  employee_id: number;
  employee_name?: string | null;
  session_count: number;
  active_session_count: number;
  has_active_session: boolean;
  individual_work_time_minutes?: number;
  is_optional_principal?: boolean;
}

export interface TaskCollaborationReadDTO {
  task_id: string;
  display_name?: string | null;
  optional_principal?: {
    optional_principal_employee_id?: number | null;
    optional_principal_employee_name?: string | null;
    principal_has_started?: boolean;
  };
  actual_workers?: ActualWorkerDTO[];
  active_workers?: ActualWorkerDTO[];
  helper_memberships?: HelperMembershipDTO[];
  authorized_helper_count?: number;
  open_help_requests?: HelpRequestDTO[];
  has_open_help?: boolean;
  operation_completed?: boolean;
  operation_status?: string | null;
  operation_status_display?: string | null;
  visible_as_principal?: boolean | null;
  visible_as_helper?: boolean | null;
  can_view_help?: boolean | null;
  can_accept_help?: boolean | null;
  can_start_helper_work?: boolean | null;
  can_stop_own_session?: boolean | null;
  can_complete_operation?: boolean | null;
  can_request_help?: boolean | null;
  can_cancel_help?: boolean | null;
}

export interface OrderTaskCollaborationReadDTO {
  contract_version: string;
  order_id: number;
  order_code?: string | null;
  execution_plan_id?: number | null;
  tasks: TaskCollaborationReadDTO[];
  generated_at: string;
  read_model_notes?: string[];
}

export interface HelpActionResponseDTO {
  status: string;
  action: "create" | "accept" | "decline" | "cancel" | "close";
  help_request: HelpRequestDTO;
  membership_already_active?: boolean;
  membership_reactivated?: boolean;
  membership_id?: number | null;
}

export interface HelpRequestCreateBody {
  targeted_employee_id?: number | null;
  reason?: string | null;
  competence_hint?: string | null;
}

export class CollaborationApiError extends Error {
  status: number;
  code: string;
  detail: unknown;

  constructor(status: number, code: string, message: string, detail?: unknown) {
    super(message);
    this.name = "CollaborationApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

async function parseError(response: Response): Promise<never> {
  let detail: unknown = null;
  let code = `http_${response.status}`;
  let message = response.statusText || "Collaboration request failed";
  try {
    const body = await response.json();
    detail = body?.detail ?? body;
    if (typeof detail === "object" && detail && "error" in detail) {
      code = String((detail as { error: string }).error);
      message =
        String((detail as { message?: string }).message || code) || message;
    } else if (typeof detail === "string") {
      message = detail;
      code = detail;
    }
  } catch {
    // keep defaults
  }
  throw new CollaborationApiError(response.status, code, message, detail);
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) await parseError(response);
  return response.json() as Promise<T>;
}

/** Operator: order-wide collaboration read with viewer-scoped capabilities. */
export async function fetchOrderTaskCollaborationRead(
  orderId: number,
  viewerEmployeeId?: number | null,
): Promise<OrderTaskCollaborationReadDTO> {
  const qs =
    viewerEmployeeId != null && viewerEmployeeId > 0
      ? `?viewer_employee_id=${viewerEmployeeId}`
      : "";
  return jsonFetch(
    `${operatorBase()}/orders/${orderId}/task-collaboration-read${qs}`,
  );
}

export async function createOperatorHelpRequest(
  orderId: number,
  taskId: string,
  body: HelpRequestCreateBody = {},
): Promise<HelpActionResponseDTO> {
  return jsonFetch(
    `${operatorBase()}/orders/${orderId}/tasks/${encodeURIComponent(taskId)}/collaboration/help-requests`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export async function cancelOperatorHelpRequest(
  orderId: number,
  helpRequestId: number,
): Promise<HelpActionResponseDTO> {
  return jsonFetch(
    `${operatorBase()}/orders/${orderId}/collaboration/help-requests/${helpRequestId}/cancel`,
    { method: "POST", body: "{}" },
  );
}

export async function listOperatorHelpRequests(
  orderId: number,
  taskId: string,
): Promise<{ order_id: number; task_id?: string | null; help_requests: HelpRequestDTO[] }> {
  return jsonFetch(
    `${operatorBase()}/orders/${orderId}/tasks/${encodeURIComponent(taskId)}/collaboration/help-requests`,
  );
}

/** Mobile V2: ajutor opportunity pool. */
export async function fetchMobileHelpOpportunities(): Promise<
  Array<Record<string, unknown> & { task_id: string; order_id: number }>
> {
  return jsonFetch(`${mobileBase()}/tasks/help-opportunities`);
}

export async function acceptMobileHelpRequest(
  orderId: number,
  helpRequestId: number,
): Promise<HelpActionResponseDTO> {
  return jsonFetch(
    `${mobileBase()}/orders/${orderId}/collaboration/help-requests/${helpRequestId}/accept`,
    { method: "POST", body: "{}" },
  );
}

export async function declineMobileHelpRequest(
  orderId: number,
  helpRequestId: number,
): Promise<HelpActionResponseDTO> {
  return jsonFetch(
    `${mobileBase()}/orders/${orderId}/collaboration/help-requests/${helpRequestId}/decline`,
    { method: "POST", body: "{}" },
  );
}

export async function cancelMobileHelpRequest(
  orderId: number,
  helpRequestId: number,
): Promise<HelpActionResponseDTO> {
  return jsonFetch(
    `${mobileBase()}/orders/${orderId}/collaboration/help-requests/${helpRequestId}/cancel`,
    { method: "POST", body: "{}" },
  );
}

export async function startMobileHelperSession(
  orderId: number,
  taskId: string,
): Promise<unknown> {
  return jsonFetch(
    `${mobileBase()}/orders/${orderId}/tasks/${encodeURIComponent(taskId)}/collaboration/helper-session/start`,
    { method: "POST", body: "{}" },
  );
}

export async function stopMobileHelperSession(
  orderId: number,
  taskId: string,
): Promise<unknown> {
  return jsonFetch(
    `${mobileBase()}/orders/${orderId}/tasks/${encodeURIComponent(taskId)}/collaboration/helper-session/stop`,
    { method: "POST", body: "{}" },
  );
}

export async function createMobileHelpRequest(
  orderId: number,
  taskId: string,
  body: HelpRequestCreateBody = {},
): Promise<HelpActionResponseDTO> {
  return jsonFetch(
    `${mobileBase()}/orders/${orderId}/tasks/${encodeURIComponent(taskId)}/collaboration/help-requests`,
    { method: "POST", body: JSON.stringify(body) },
  );
}
