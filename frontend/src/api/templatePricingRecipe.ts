/**
 * Template Pricing Studio — read-only recipe composition API.
 */

import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

export type TemplateRecipeKind =
  | "material"
  | "machine_operation"
  | "labor"
  | "service"
  | "commercial_line"
  | "minimum"
  | "adjustment"
  | "unknown";

export interface TemplatePricingRecipeItem {
  recipe_item_id: string;
  recipe_kind: TemplateRecipeKind;
  operator_name: string;
  stable_code: string;
  catalog_code?: string | null;
  quantity_keys: string[];
  formula_owner?: string | null;
  applicability: Record<string, unknown>;
  rate_source?: string | null;
  cost_or_rate: "purchase_cost" | "reusable_rate" | "commercial_documented" | "unknown";
  cost_label_ro?: string | null;
  unit?: string | null;
  current_value?: number | null;
  currency?: string | null;
  status: "active" | "missing" | "blocked" | "warning" | "inactive";
  provenance?: string | null;
  cpp_line_code?: string | null;
  cpp_pricing_rule_code?: string | null;
  eic_rule_code?: string | null;
  typed_catalog?: string | null;
  machine_family?: string | null;
  data_quality_flags: string[];
  data_quality_message_ro?: string | null;
  technical_ready: boolean;
  commercial_ready: boolean;
  blockers: string[];
  warnings: string[];
  editable: boolean;
  editability_reason_ro: string;
  source_links: Record<string, string>;
  legacy: boolean;
  confidence: "high" | "medium" | "low";
}

export interface TemplatePricingRecipeResponse {
  schema_version: string;
  template_code: string;
  template_name?: string | null;
  template_version?: string | null;
  lifecycle?: string | null;
  usage_mode?: string | null;
  editability_policy: string;
  ownership_note_ro: string;
  summary: {
    total_items: number;
    materials: number;
    machine_operations: number;
    labor: number;
    services: number;
    commercial_lines: number;
    resolved: number;
    missing: number;
    blocked: number;
    warnings: number;
    registry_confirmed: number;
    registry_missing_price: number;
  };
  recipe: TemplatePricingRecipeItem[];
  cpp_preview: {
    available: boolean;
    status: string;
    note_ro: string;
    line_codes: string[];
    blocked_line_codes: string[];
    subtotal?: number | null;
    currency?: string | null;
  };
  eic_preview: {
    available: boolean;
    status: string;
    note_ro: string;
    provenance_notes: string[];
    rule_codes: string[];
  };
  readiness: {
    technical_ready: boolean;
    commercial_ready: boolean;
    technical_notes_ro: string[];
    commercial_notes_ro: string[];
    inventory_notes_ro: string[];
  };
  acm_acceptance: {
    applies: boolean;
    shell_registry_confirmed?: number | null;
    shell_registry_missing?: number | null;
    treatment_commercial_lines_allowed?: boolean | null;
    blockers: string[];
    policy_ro?: string | null;
  };
  blockers: string[];
  warnings: string[];
}

export const templatePricingRecipeApi = {
  getRecipe: async (templateCode: string): Promise<TemplatePricingRecipeResponse> => {
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/product-system/templates/${encodeURIComponent(templateCode)}/pricing`,
      { credentials: "include" },
    );
    if (!res.ok) {
      const detail = await formatApiErrorResponse(
        res,
        `template pricing recipe failed: HTTP ${res.status}`,
      );
      throw new Error(detail);
    }
    return res.json();
  },
};
