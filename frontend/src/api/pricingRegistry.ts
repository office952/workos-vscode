/**
 * Pricing Registry API — template-driven quote pricing (read-only).
 */

import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

export type PricingRegistryKind =
  | "material"
  | "service"
  | "operation_rate"
  | "workcenter_rate"
  | "markup_rule";

export type PricingRegistryConfidence =
  | "owner_confirmed"
  | "estimated"
  | "supplier_average"
  | "imported_from_inventory"
  | "missing";

export interface PricingRegistryItem {
  pricing_code: string;
  display_name: string;
  pricing_kind: PricingRegistryKind;
  registry_category: string;
  unit: string;
  base_cost: number | null;
  currency: string | null;
  vat_percent?: number | null;
  status: string;
  confidence: PricingRegistryConfidence | string;
  source_notes?: string | null;
  used_by_templates: string[];
  affects_quote_calculation: boolean;
  technical_source: string;
  cost_engine_rate?: number | null;
  cost_engine_rate_match?: boolean;
  editable?: boolean;
  rate_basis?: string;
  scope_type?: string;
  scope_value?: string;
}

export interface PricingRegistryResponse {
  summary: {
    templates_active: number;
    items_template_used: number;
    materials_count: number;
    rates_count: number;
    markup_rules_count: number;
    owner_confirmed: number;
    needs_review: number;
    missing_price: number;
  };
  template_usage: Array<{
    template_code: string;
    material_codes: string[];
    workcenter_codes: string[];
  }>;
  items: PricingRegistryItem[];
  markup_policies: PricingRegistryItem[];
  registry_categories: string[];
  technical_debt_note: string;
}

export const pricingRegistryApi = {
  getRegistry: async (params?: {
    template_code?: string;
    include_all_inventory?: boolean;
  }): Promise<PricingRegistryResponse> => {
    const qs = new URLSearchParams();
    if (params?.template_code) qs.set("template_code", params.template_code);
    if (params?.include_all_inventory) qs.set("include_all_inventory", "true");
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/pricing/registry${suffix}`,
      { credentials: "include" }
    );
    if (!res.ok) {
      const detail = await formatApiErrorResponse(
        res,
        `pricing/registry failed: HTTP ${res.status}`
      );
      throw new Error(detail);
    }
    return res.json();
  },
};
