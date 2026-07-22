/**
 * Product Price Breakdown V1 — read-model over CPP + EIC (no second calculator).
 */

import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

export type PriceBreakdownLineGroup =
  | "material"
  | "machine"
  | "labor"
  | "service"
  | "ai_decision"
  | "adjustment"
  | "commercial"
  | "internal";

export interface PriceBreakdownLine {
  line_id: string;
  line_group: PriceBreakdownLineGroup;
  resource_code: string;
  display_name: string;
  quantity_key?: string | null;
  formula_display: string;
  quantity?: number | null;
  unit?: string | null;
  base_value?: number | null;
  currency?: string | null;
  source_type: string;
  source_id?: string | null;
  minimum?: number | null;
  waste?: number | null;
  adjustment?: number | null;
  internal_cost?: number | null;
  commercial_value?: number | null;
  cpp_line?: string | null;
  eic_rule?: string | null;
  configurable: boolean;
  warning?: string | null;
  confidence?: string | null;
  rationale_ro?: string | null;
  ai_decision_id?: string | null;
}

export interface PriceBreakdownGroupTotal {
  line_group: PriceBreakdownLineGroup;
  line_count: number;
  internal_subtotal?: number | null;
  commercial_subtotal?: number | null;
  currency?: string | null;
}

export interface PriceBreakdownTotals {
  material_internal?: number | null;
  machine_internal?: number | null;
  labor_internal?: number | null;
  service_internal?: number | null;
  consumables_internal?: number | null;
  overhead_internal?: number | null;
  ai_contribution_note_ro?: string | null;
  internal_total?: number | null;
  commercial_subtotal?: number | null;
  commercial_total?: number | null;
  currency: string;
  cpp_total_matches: boolean;
  eic_total_matches: boolean;
  no_duplicate_commercial_codes: boolean;
  no_duplicate_internal_codes: boolean;
}

export interface ProductPriceBreakdownResponse {
  schema_version: string;
  template_code: string;
  configuration_id: string;
  fixture_id?: string | null;
  currency: string;
  ownership_note_ro: string;
  publication_status?: string | null;
  operational_readiness?: string | null;
  uses_ai_defaults: boolean;
  configuration_summary: Record<string, unknown>;
  lines: PriceBreakdownLine[];
  group_totals: PriceBreakdownGroupTotal[];
  totals: PriceBreakdownTotals;
  ai_decisions: Array<Record<string, unknown>>;
  calibration_hooks: Array<{
    line_code?: string | null;
    estimated_minutes?: number | null;
    purpose?: string | null;
    excluded_from_total: boolean;
    note_ro: string;
  }>;
  cpp_status?: string | null;
  eic_status?: string | null;
  warnings: string[];
  blockers: string[];
  eic_provenance: Array<Record<string, unknown>>;
  cpp_provenance: Array<Record<string, unknown>>;
  acm_treatments_blocked?: boolean | null;
}

export const productPriceBreakdownApi = {
  postBreakdown: async (
    templateCode: string,
    body?: {
      workspace_id?: string | null;
      quote_input?: Record<string, unknown> | null;
      currency?: string;
      fixture_id?: string | null;
    },
  ): Promise<ProductPriceBreakdownResponse> => {
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/product-system/templates/${encodeURIComponent(templateCode)}/price-breakdown`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body ?? {}),
      },
    );
    if (!res.ok) {
      const detail = await formatApiErrorResponse(
        res,
        `price breakdown failed: HTTP ${res.status}`,
      );
      throw new Error(detail);
    }
    return res.json();
  },
};
