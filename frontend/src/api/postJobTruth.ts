/**
 * Post-job truth API — cohesive read model for Execution detail.
 * GET /api/v1/execution/{order_id}/post-job-truth
 * Frontend must not compute canonical totals — render backend truth only.
 */
import { getAPIBaseURL } from "@/lib/config";

const getAPIBase = () => `${getAPIBaseURL()}/api/v1`;

export type DataPresence =
  | "present"
  | "missing"
  | "not_captured"
  | "not_applicable"
  | "excluded"
  | "still_active"
  | "zero"
  | "partial"
  | "complete";

export type CostCoverageStatus =
  | "COMPLETE"
  | "PARTIAL"
  | "INCOMPLETE"
  | "NOT_AVAILABLE";

export interface PresenceValue {
  value: number | string | boolean | null;
  presence: DataPresence;
  unit?: string | null;
  source?: string | null;
  note?: string | null;
}

export interface PostJobTruthResponse {
  contract_version: "post_job_truth_v1";
  order_id: number;
  order_code: string;
  baseline: {
    revenue_net: PresenceValue;
    planned_internal_cost: PresenceValue;
    currency: string | null;
    revenue_source: string;
    has_snapshot_v2: boolean;
    snapshot_version: number | null;
  };
  labor: {
    closed_minutes_total: PresenceValue;
    open_session_count: number;
    session_count: number;
    planned_minutes_total: PresenceValue;
    variance_minutes: PresenceValue;
    sessions: Array<{
      session_id: string;
      task_id: string | null;
      employee_id: number | null;
      employee_name: string | null;
      role: string | null;
      actual_minutes: number | null;
      status: string;
      completeness: DataPresence;
    }>;
    monetary_cost: PresenceValue;
    completeness: DataPresence;
  };
  materials: {
    lines: Array<{
      material_id: number | null;
      material_name: string | null;
      actual_deducted_quantity: PresenceValue;
      actual_known_internal_cost: PresenceValue;
      source: string;
      completeness: DataPresence;
      valuation_method: string | null;
    }>;
    observed_row_count: number;
    deducted_movement_count: number;
    known_actual_cost_total: PresenceValue;
    valuation_method: string | null;
    completeness: DataPresence;
  };
  machines: {
    items: Array<{
      task_id: string | null;
      planned_machine_type: string | null;
      status: DataPresence;
      note: string | null;
    }>;
    completeness: DataPresence;
    note: string | null;
  };
  quantity: {
    tasks_planned: PresenceValue;
    tasks_completed: PresenceValue;
    progress_percent: PresenceValue;
    completed_quantity: PresenceValue;
    completeness: DataPresence;
  };
  reconciliation: {
    variances: Array<{
      dimension: string;
      planned_value: number | string | null;
      actual_value: number | string | null;
      absolute_variance: number | null;
      percentage_variance: number | null;
      unit: string | null;
      status: DataPresence;
      explanation_code: string;
    }>;
    operations: Array<{
      task_id: string;
      task_name: string | null;
      planned_status: string | null;
      planned_minutes: PresenceValue;
      actual_minutes: PresenceValue;
      variance_minutes: PresenceValue;
      planned_quantity: PresenceValue;
      actual_quantity: PresenceValue;
      quantity_variance: PresenceValue;
      actual_status: string | null;
      reconciliation_state:
        | "matched"
        | "partial"
        | "missing_actual"
        | "variance";
      completeness: DataPresence;
    }>;
    summary: {
      matched_count: number;
      partial_count: number;
      missing_actual_count: number;
      variance_count: number;
      operations_total: number;
    };
  };
  profitability: {
    revenue_net: PresenceValue;
    planned_internal_cost: PresenceValue;
    known_actual_cost: PresenceValue;
    known_actual_margin: PresenceValue;
    known_actual_margin_percent: PresenceValue;
    cost_coverage_status: CostCoverageStatus;
    profitability_status: CostCoverageStatus;
    included_cost_components: string[];
    excluded_cost_components: string[];
    missing_actual_components: string[];
    wording: string[];
    false_final_profit_forbidden: boolean;
  };
  missing_data: Array<{
    code: string;
    dimension: string;
    message: string;
    blocking_for_complete_profitability: boolean;
  }>;
  sources: Record<string, unknown>;
  retroactive_change_allowed: boolean;
  write_back_performed: boolean;
}

export class PostJobTruthNotFoundError extends Error {
  readonly orderId: number;
  constructor(orderId: number) {
    super(`order_not_found:${orderId}`);
    this.name = "PostJobTruthNotFoundError";
    this.orderId = orderId;
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchPostJobTruth(
  orderId: number,
): Promise<PostJobTruthResponse> {
  if (!Number.isInteger(orderId) || orderId <= 0) {
    throw new Error("order_id_invalid");
  }
  const url = `${getAPIBase()}/execution/${orderId}/post-job-truth`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
    credentials: "include",
  });
  if (res.status === 404) {
    throw new PostJobTruthNotFoundError(orderId);
  }
  if (!res.ok) {
    throw new Error(
      `GET /execution/${orderId}/post-job-truth failed: ${res.status}`,
    );
  }
  return res.json() as Promise<PostJobTruthResponse>;
}

/** Romanian operator labels for presence — values still come from backend. */
export function formatPresenceValueRo(
  pv: PresenceValue | null | undefined,
  opts?: { money?: boolean; currency?: string | null },
): string {
  if (!pv) return "—";
  const labels: Record<string, string> = {
    missing: "lipsă",
    not_captured: "neînregistrat",
    excluded: "exclus",
    not_applicable: "nu se aplică",
    still_active: "încă activ",
    partial: "parțial",
    zero: "0",
    present: "prezent",
    complete: "complet",
  };
  if (
    pv.presence === "missing" ||
    pv.presence === "not_captured" ||
    pv.presence === "excluded" ||
    pv.presence === "not_applicable"
  ) {
    return labels[pv.presence] ?? pv.presence;
  }
  if (pv.presence === "still_active") {
    return pv.value == null ? labels.still_active : String(pv.value);
  }
  if (pv.presence === "partial" && (pv.value === null || pv.value === undefined)) {
    return labels.partial;
  }
  if (pv.value === null || pv.value === undefined) {
    return labels[pv.presence] ?? pv.presence;
  }
  if (opts?.money && typeof pv.value === "number") {
    const unit = opts.currency?.trim() || pv.unit || "RON";
    return `${pv.value.toFixed(2)} ${unit}`;
  }
  if (typeof pv.value === "number" && pv.unit) {
    return `${pv.value} ${pv.unit}`;
  }
  return String(pv.value);
}

export function formatPresenceValue(
  pv: PresenceValue | null | undefined,
  opts?: { money?: boolean; currency?: string | null },
): string {
  if (!pv) return "—";
  if (
    pv.presence === "missing" ||
    pv.presence === "not_captured" ||
    pv.presence === "excluded" ||
    pv.presence === "not_applicable"
  ) {
    const labels: Record<string, string> = {
      missing: "missing",
      not_captured: "not captured",
      excluded: "excluded",
      not_applicable: "n/a",
    };
    return labels[pv.presence] ?? pv.presence;
  }
  if (pv.presence === "still_active") {
    return pv.value == null ? "still active" : String(pv.value);
  }
  if (pv.value === null || pv.value === undefined) {
    return pv.presence;
  }
  if (opts?.money && typeof pv.value === "number") {
    const unit = opts.currency?.trim() || pv.unit || "RON";
    return `${pv.value.toFixed(2)} ${unit}`;
  }
  if (typeof pv.value === "number" && pv.unit) {
    return `${pv.value} ${pv.unit}`;
  }
  return String(pv.value);
}
