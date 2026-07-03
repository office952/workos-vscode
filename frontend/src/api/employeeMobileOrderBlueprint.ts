import { getAPIBaseURL } from "@/lib/config";

const mobileBase = () => `${getAPIBaseURL()}/api/v1/employee-mobile`;

export interface EmployeeMobileOrderBlueprintSummary {
  total_tasks: number;
  my_tasks: number;
  my_done: number;
  overall_progress_percent: number;
  my_progress_percent: number;
  blocked: number;
  in_progress: number;
}

export interface EmployeeMobileMaterialHint {
  name: string;
  category: string;
  label: string;
  status?: string;
  display_note?: string;
}

export interface EmployeeMobileOrderBlueprintTask {
  task_id: string;
  name: string;
  status_display: string;
  is_mine: boolean;
  is_current: boolean;
  stage_label: string;
  has_documents: boolean;
  has_instructions: boolean;
  is_eligible_for_me?: boolean;
  can_assist?: boolean;
  eligibility_reason?: string;
  active_helper_count?: number;
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
  material_hints?: EmployeeMobileMaterialHint[];
  material_status_label?: string | null;
}

export interface EmployeeMobileOrderBlueprintDTO {
  order_id: number;
  order_label: string;
  client_label?: string;
  summary: EmployeeMobileOrderBlueprintSummary;
  current_task_id?: string | null;
  tasks: EmployeeMobileOrderBlueprintTask[];
}

export async function fetchEmployeeMobileOrderBlueprint(
  orderId: number,
): Promise<EmployeeMobileOrderBlueprintDTO> {
  const response = await fetch(`${mobileBase()}/orders/${orderId}/my-blueprint`, {
    credentials: "include",
  });
  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      detail = { error: response.statusText || "request_failed" };
    }
    throw new Error(
      typeof detail === "object" &&
        detail !== null &&
        "detail" in detail &&
        typeof (detail as { detail?: { error?: string } }).detail?.error === "string"
        ? (detail as { detail: { error: string } }).detail.error
        : "employee_order_blueprint_fetch_failed",
    );
  }
  return response.json() as Promise<EmployeeMobileOrderBlueprintDTO>;
}

export function buildEmployeeMobileOrderBlueprintPath(orderId: number): string {
  return `/employee-app/tasks/orders/${orderId}/blueprint`;
}
