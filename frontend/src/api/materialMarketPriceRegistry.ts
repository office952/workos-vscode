/**
 * Material Market Price Registry V1 — Inventory purchase truth (read-only).
 */

import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

export type MaterialSourceType =
  | "MEASURED_LANDED_COST"
  | "PURCHASE_INVOICE"
  | "SUPPLIER_OFFER"
  | "OWNER_CONFIRMED"
  | "SUPPLIER_CATALOG"
  | "TEMPORARY_AI_FALLBACK"
  | "LEGACY"
  | "MISSING";

export type MaterialFreshness =
  | "CURRENT"
  | "REVIEW_SOON"
  | "STALE"
  | "EXPIRED"
  | "UNKNOWN_DATE";

export interface MaterialPriceNormalization {
  raw_unit?: string | null;
  raw_price?: number | null;
  currency?: string | null;
  normalized_unit?: string | null;
  normalized_price?: number | null;
  sheet_area_m2?: number | null;
  formula_display?: string | null;
  conversion_applied: boolean;
  note_ro?: string | null;
}

export interface MaterialMarketPriceRecord {
  material_code: string;
  display_name: string;
  category?: string | null;
  subcategory?: string | null;
  variant?: string | null;
  inventory_status?: string | null;
  stock_current?: number | null;
  supplier_id?: number | null;
  supplier_name?: string | null;
  source_type: MaterialSourceType;
  source_name?: string | null;
  source_date?: string | null;
  source_notes?: string | null;
  effective_from?: string | null;
  raw_unit?: string | null;
  raw_price?: number | null;
  currency?: string | null;
  vat_percent?: number | null;
  normalization: MaterialPriceNormalization;
  preferred: boolean;
  freshness: MaterialFreshness;
  freshness_policy_ro?: string | null;
  confidence: "high" | "medium" | "low";
  temporary_ai_fallback: boolean;
  canonical: boolean;
  material_role?: "physical_sku" | "variant_selector" | "unknown";
  variant_codes?: string[];
  requires_direct_price?: boolean;
  blocker?: string | null;
  warning?: string | null;
  active_templates: string[];
  history: Array<{
    history_id: number;
    unit_cost?: number | null;
    currency?: string | null;
    valid_from?: string | null;
    changed_at?: string | null;
    snapshot_source?: string | null;
  }>;
  inventory_href: string;
  pricing_href: string;
}

export interface MaterialMarketPriceRegistryResponse {
  schema_version: string;
  ownership_note_ro: string;
  source_precedence: string[];
  freshness_policy: Record<string, unknown>;
  summary: {
    total: number;
    priced: number;
    missing: number;
    stale: number;
    review_soon: number;
    unknown_date: number;
    with_supplier: number;
    active_template_critical_missing: number;
    temporary_ai_fallback: number;
  };
  items: MaterialMarketPriceRecord[];
  critical_missing: string[];
  warnings: string[];
}

export const materialMarketPriceRegistryApi = {
  getRegistry: async (params?: {
    include_history?: boolean;
    active_templates_only?: boolean;
  }): Promise<MaterialMarketPriceRegistryResponse> => {
    const qs = new URLSearchParams();
    if (params?.include_history === false) qs.set("include_history", "false");
    if (params?.active_templates_only) qs.set("active_templates_only", "true");
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/pricing/material-market-prices${suffix}`,
      { credentials: "include" },
    );
    if (!res.ok) {
      const detail = await formatApiErrorResponse(
        res,
        `material-market-prices failed: HTTP ${res.status}`,
      );
      throw new Error(detail);
    }
    return res.json();
  },
};
