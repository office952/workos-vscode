/**
 * Canonical operator execution task truth (W6-T01).
 * GET /api/v1/operator/orders/{orderId}/task-truth
 */
import { getAPIBaseURL } from "@/lib/config";

export const OPERATOR_TASK_TRUTH_VERSION = "operator_task_truth/v1";

export type ReadinessAuthority =
  | "FROZEN_ORDER_SNAPSHOT_V2"
  | "LEGACY_ORDER_INPUT"
  | "LEGACY_READ_MODEL_EXPLICIT"
  | "BLOCKED_MISSING_ORDER_SNAPSHOT_V2";

export type IdentitySource =
  | "frozen_task_identity/v1"
  | "legacy_plan_task"
  | "not_proven";

export interface TaskIdentityTruth {
  task_id: string;
  deterministic_task_key?: string | null;
  display_label: string;
  identity_classification?: string | null;
  source_graph_node_id?: string | null;
  source_component_instance_id?: string | null;
  component_role?: string | null;
  component_label?: string | null;
  component_template_code?: string | null;
  source_operation_code?: string | null;
  source_task_rule_code?: string | null;
  parent_graph_node_id?: string | null;
  task_scope?: string | null;
  logo_segment_key?: string | null;
  identity_source: IdentitySource;
}

export interface TaskRuntimeTruth {
  current_status: string;
  assigned_employee_id?: number | null;
  assigned_employee_name?: string | null;
  is_startable: boolean;
  is_completeable: boolean;
  is_blocked: boolean;
  readiness_status?: string | null;
  readiness_label?: string | null;
  readiness_reasons: Array<Record<string, unknown>>;
  blocking_reasons: Array<Record<string, unknown>>;
  blocking_task_ids: string[];
  blocking_tasks: Array<Record<string, unknown>>;
  production_release_blocked: boolean;
  production_release_status: string;
  production_release_scope: string;
  blocking_owner_decision_codes: string[];
  last_started_at?: string | null;
  last_ended_at?: string | null;
}

export interface TaskAuthorityTruth {
  frozen_source?: string | null;
  operational_source: string;
  readiness_source: string;
  production_release_source: string;
  legacy_fallback_active: boolean;
}

export interface OperatorTaskTruthTask {
  identity: TaskIdentityTruth;
  runtime: TaskRuntimeTruth;
  authority: TaskAuthorityTruth;
}

export interface OwnerDecisionSummaryItem {
  code: string;
  label: string;
  category: string;
  blocking: boolean;
  frozen_status: string;
  operational_status: string;
  scope: string;
  required_action?: string | null;
  acknowledgement_sufficient: boolean;
  requires_resolution: boolean;
  can_resolve: boolean;
  resolved_at?: string | null;
  resolved_by_user_name?: string | null;
  has_resolution_note: boolean;
}

export interface RoleCapabilities {
  can_resolve_owner_decisions: boolean;
  can_view_internal_cost: boolean;
  can_view_owner_decision_notes: boolean;
}

export interface InternalCostSummary {
  visibility: "available" | "restricted";
  status?: string | null;
  estimated_total_internal_cost?: number | null;
  accepted_commercial_total?: number | null;
  execution_blocked?: boolean | null;
}

export interface OperatorTaskTruthResponse {
  contract_version: string;
  order_id: number;
  order_code?: string | null;
  execution_plan_id?: number | null;
  order_snapshot_v2_id?: number | null;
  quote_snapshot_v2_id?: number | null;
  task_identity_version?: string | null;
  readiness_authority: ReadinessAuthority;
  production_release_policy: string;
  production_release_status: string;
  production_release_blocked: boolean;
  owner_decisions_summary: OwnerDecisionSummaryItem[];
  role_capabilities: RoleCapabilities;
  internal_cost_summary?: InternalCostSummary | null;
  tasks: OperatorTaskTruthTask[];
  generated_at: string;
  legacy_order: boolean;
}

const operatorBase = () => `${getAPIBaseURL()}/api/v1/operator`;

export async function fetchOperatorTaskTruth(
  orderId: number,
): Promise<OperatorTaskTruthResponse> {
  const res = await fetch(`${operatorBase()}/orders/${orderId}/task-truth`, {
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      (err as { detail?: { message?: string } })?.detail?.message ||
        `task-truth ${res.status}`,
    );
  }
  return res.json() as Promise<OperatorTaskTruthResponse>;
}

/** Client must not derive startability — use runtime.is_startable from API only. */
export function taskTruthStartableFromBackend(task: OperatorTaskTruthTask): boolean {
  return task.runtime.is_startable === true;
}
