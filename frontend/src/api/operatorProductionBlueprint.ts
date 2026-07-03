/**
 * Operator production blueprint — read-only plan + reality visibility per order.
 */
import { getAPIBaseURL } from "@/lib/config";

const operatorBase = () => `${getAPIBaseURL()}/api/v1/operator`;

export interface ProductionBlueprintSummary {
  total_tasks: number;
  done: number;
  in_progress: number;
  blocked: number;
  todo: number;
  unassigned: number;
  progress_percent: number;
}

export interface MaterialPlanningSummary {
  project_critical_count: number;
  suggest_replenishment_count: number;
  checklist_count: number;
  has_procurement_sensitive_items: boolean;
}

export interface MaterialPlanningItem {
  code: string;
  name: string;
  category: string;
  quantity_estimate?: number | null;
  unit: string;
  confidence: string;
  source: string;
  required_for_task_ids: string[];
  planning_policy: string;
  procurement_policy: string;
  readiness_impact: string;
  display_note: string;
  procurement_status?: string;
  procurement_label?: string;
  planning_action?: string;
  affects_start?: boolean;
  employee_safe_label?: string;
  operator_note?: string;
}

export interface ProcurementSummary {
  critical_materials_not_checked: number;
  awaiting_advance_items: number;
  suggest_replenishment_items: number;
  blocking_items_count: number;
  blocking_material_codes: string[];
}

export interface ProductionPlanningSummary {
  eligible_tasks: number;
  waiting_predecessor_tasks: number;
  waiting_material_tasks: number;
  waiting_file_tasks?: number;
  waiting_template_tasks?: number;
  waiting_document_tasks?: number;
  waiting_workshop_info_tasks?: number;
  manual_blocked_tasks: number;
  critical_materials_not_checked: number;
  awaiting_advance_items: number;
  suggest_replenishment_items: number;
  suggested_next_action: string;
}

export interface ProductionBlueprintActiveWorker {
  employee_id: number;
  employee_name: string;
  task_id: string;
  task_name: string;
  started_at?: string | null;
}

export interface ProductionBlueprintTask {
  task_id: string;
  name: string;
  status: "done" | "blocked" | "in_progress" | "todo" | "unassigned";
  status_display: string;
  process_type: string;
  process_id?: string;
  machine_type: string;
  preparation_domain?: string;
  assigned_employee_id?: number | null;
  assigned_employee_name?: string | null;
  active_worker_id?: number | null;
  active_worker_name?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  blocked_at?: string | null;
  block_reason?: string | null;
  documents_count: number;
  has_instructions: boolean;
  has_open_clarification: boolean;
  readiness_status?: string;
  readiness_label?: string;
  is_startable?: boolean;
  readiness_reasons?: Array<{
    code?: string;
    label?: string;
    message?: string;
    missing_item?: string;
  }>;
  blocking_reasons?: Array<{
    code?: string;
    label?: string;
    message?: string;
    missing_item?: string;
  }>;
  blocking_tasks?: Array<{ task_id: string; name: string }>;
  blocking_task_ids?: string[];
  dependency_warning?: string | null;
  material_warning?: string | null;
  blocking_materials?: Array<{
    code?: string;
    name?: string;
    status?: string;
    label?: string;
  }>;
  material_planning_items?: MaterialPlanningItem[];
}

export interface MountingTemplateSummary {
  material_type: "none" | "paper" | "forex";
  material_code?: string | null;
  material_name?: string | null;
  unit?: string;
  registry_rate_display?: string | null;
  area_m2?: number | null;
  forex_material_code?: string;
  paper_material_code?: string;
}

export interface PreparationOwnership {
  instrumentation: {
    prepared_by_user_id?: string | null;
    prepared_by_user_name?: string | null;
    source_field: string;
  };
  cnc: {
    registry_operation_hint?: string;
    task_count: number;
  };
  mounting_template: MountingTemplateSummary;
}

export interface PreparationGroupTask {
  task_id: string;
  name: string;
  status: string;
  status_display: string;
  preparation_domain?: string;
  assigned_employee_id?: number | null;
  assigned_employee_name?: string | null;
  process_id?: string;
  machine_type?: string;
  documents_count?: number;
  has_instructions?: boolean;
}

export interface ProductionBlueprintDTO {
  order_id: number;
  order_label: string;
  order_code?: string;
  product_template?: string | null;
  prepared_by_user_id?: string | null;
  prepared_by_user_name?: string | null;
  preparation_ownership?: PreparationOwnership;
  preparation_groups?: Record<string, PreparationGroupTask[]>;
  material_planning_summary?: MaterialPlanningSummary;
  procurement_summary?: ProcurementSummary;
  production_planning_summary?: ProductionPlanningSummary;
  material_procurement_statuses?: Record<string, unknown>;
  summary: ProductionBlueprintSummary;
  active_workers: ProductionBlueprintActiveWorker[];
  next_tasks: Array<{ task_id: string; name: string }>;
  tasks: ProductionBlueprintTask[];
  operational_readiness_status?: string;
  operational_tasks_count?: number;
  operational_readiness_blockers?: string[];
  operational_readiness_next_action?: string | null;
  operational_tasks_materialized?: boolean;
  plan_format?: string;
  execution_tasks_created?: boolean;
}

export async function fetchOrderProductionBlueprint(
  orderId: number
): Promise<ProductionBlueprintDTO> {
  const response = await fetch(
    `${operatorBase()}/orders/${orderId}/production-blueprint`,
    { credentials: "include" }
  );
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
        : "production_blueprint_fetch_failed"
    );
  }
  return response.json() as Promise<ProductionBlueprintDTO>;
}

export async function patchMaterialProcurementStatus(
  orderId: number,
  materialCode: string,
  payload: {
    status: string;
    note?: string;
    affected_task_ids?: string[];
  },
): Promise<unknown> {
  const response = await fetch(
    `${operatorBase()}/orders/${orderId}/material-procurement/${encodeURIComponent(materialCode)}`,
    {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
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
        : "material_procurement_patch_failed",
    );
  }
  return response.json();
}
