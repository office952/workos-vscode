/**
 * ProfitabilityAnalysis API — read-only (Slice 10.4).
 * GET /api/v1/profitability-analysis/order/{order_id}
 */
import { getAPIBaseURL } from "@/lib/config";

const getAPIBase = () => `${getAPIBaseURL()}/api/v1`;

export type ProfitabilityStatus =
  | "estimated_only"
  | "actuals_partial"
  | "actuals_available"
  | "missing_snapshot"
  | "unsupported_legacy_order";

export type RevenueSource =
  | "order_snapshot_v2"
  | "order.total_amount"
  | "missing";

export interface ProfitabilityVariance {
  cost_delta: number | null;
  minutes_delta: number | null;
}

export interface ProfitabilityAnalysisResponse {
  order_id: number;
  order_code: string;
  snapshot_version: number | null;
  has_snapshot_v2: boolean;
  revenue_source: RevenueSource;
  accepted_commercial_total: number | null;
  accepted_currency: string | null;
  estimated_internal_total: number | null;
  has_execution_reality: boolean;
  actual_total_cost: number | null;
  actual_labor_minutes: number | null;
  actual_materials_total: number | null;
  estimated_margin_amount: number | null;
  estimated_margin_percent: number | null;
  actual_margin_amount: number | null;
  actual_margin_percent: number | null;
  variance_estimated_vs_actual: ProfitabilityVariance | null;
  profitability_status: ProfitabilityStatus;
  warnings: string[];
  retroactive_change_allowed: boolean;
  write_back_performed: boolean;
  known_actual_cost?: number | null;
  known_actual_margin?: number | null;
  known_actual_margin_percent?: number | null;
  cost_coverage_status?:
    | "COMPLETE"
    | "PARTIAL"
    | "INCOMPLETE"
    | "NOT_AVAILABLE";
  included_cost_components?: string[];
  excluded_cost_components?: string[];
  missing_actual_components?: string[];
  material_valuation_method?: string | null;
  profitability_wording?: string[];
}

export class ProfitabilityAnalysisNotFoundError extends Error {
  readonly orderId: number;

  constructor(orderId: number) {
    super(`order_not_found:${orderId}`);
    this.name = "ProfitabilityAnalysisNotFoundError";
    this.orderId = orderId;
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchProfitabilityAnalysis(
  orderId: number,
): Promise<ProfitabilityAnalysisResponse> {
  if (!Number.isInteger(orderId) || orderId <= 0) {
    throw new Error("order_id_invalid");
  }
  const url = `${getAPIBase()}/profitability-analysis/order/${orderId}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
    credentials: "include",
  });
  if (res.status === 404) {
    throw new ProfitabilityAnalysisNotFoundError(orderId);
  }
  if (!res.ok) {
    throw new Error(
      `GET /profitability-analysis/order/${orderId} failed: ${res.status}`,
    );
  }
  return res.json() as Promise<ProfitabilityAnalysisResponse>;
}

export const PROFITABILITY_STATUS_LABELS: Record<ProfitabilityStatus, string> = {
  estimated_only: "Estimated only",
  actuals_partial: "Actuals partial",
  actuals_available: "Actuals available",
  missing_snapshot: "Snapshot missing",
  unsupported_legacy_order: "Legacy order (unsupported V2)",
};

export const PROFITABILITY_WARNING_LABELS: Record<string, string> = {
  execution_reality_missing: "Execution reality not recorded",
  estimated_internal_total_missing: "Estimated internal total missing",
  actual_costing_not_available: "Actual costing not available",
  legacy_order_without_snapshot_v2: "Legacy order without snapshot V2",
  actual_material_cost_missing: "Actual material cost missing",
  hr_labor_cost_missing: "HR labor cost missing",
  order_mutability_guard_batch_watch: "Batch order PUT not guarded",
  material_cost_uses_catalog_unit_cost_at_read:
    "Material cost uses inventory catalog unit_cost at read",
  known_margin_materials_only_not_final_profit:
    "Known margin is materials-only — not final profit",
};
