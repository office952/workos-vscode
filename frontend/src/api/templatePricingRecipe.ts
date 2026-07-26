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

export type LaborClass =
  | "LABOR_INTERNAL"
  | "LABOR_COMMERCIAL"
  | "MACHINE_OPERATION"
  | "INTERNAL_SERVICE"
  | "EXTERNAL_SERVICE"
  | "INSTALLATION_SERVICE"
  | "UNKNOWN_AMBIGUOUS"
  | "LEGACY"
  | "MISSING_RATE";

export type LaborFormulaStatus =
  | "FORMULA_CONFIRMED"
  | "QUANTITY_KEY_CONFIRMED"
  | "OPERATION_ONLY"
  | "MISSING_OWNER_FORMULA"
  | "LEGACY_METADATA"
  | "NOT_APPLICABLE";

export interface TemplateLaborRecipeItem {
  labor_recipe_id: string;
  template_code: string;
  operation_code: string;
  catalog_code: string;
  workcenter_declared?: string | null;
  operator_name: string;
  labor_class: LaborClass;
  recipe_role: "assembly" | "wiring" | "finishing" | "mounting" | "packaging" | "other";
  quantity_keys: string[];
  formula_id?: string | null;
  formula_owner?: string | null;
  formula_status?: LaborFormulaStatus;
  formula_status_label_ro?: string | null;
  formula_source?: string | null;
  quantity_source?: string | null;
  owner_confirmation_required?: boolean;
  unresolved_reason?: string | null;
  evidence_level?: string | null;
  basis: "hour" | "minute" | "buc" | "ml" | "mp" | "set" | "produs" | "unknown";
  rate_basis?: string | null;
  standard_time?: unknown;
  multiplier?: unknown;
  minimum?: unknown;
  dependencies: Record<string, unknown>;
  base_rate_source?: string | null;
  internal_cost_rate?: number | null;
  commercial_rate?: number | null;
  commercial_rate_status: "available" | "unavailable" | "missing";
  unit?: string | null;
  currency?: string | null;
  status: "active" | "missing" | "blocked" | "warning" | "inactive";
  typed_catalog?: string | null;
  data_quality_flags: string[];
  data_quality_message_ro?: string | null;
  cpp_line_code?: string | null;
  eic_rule_code?: string | null;
  technical_ready: boolean;
  commercial_ready: boolean;
  blockers: string[];
  warnings: string[];
  editable: boolean;
  editability_reason_ro: string;
  source_links: Record<string, string>;
  provenance?: string | null;
  legacy: boolean;
  confidence: "high" | "medium" | "low";
  decision_source?: string | null;
  ai_decision_id?: string | null;
  ai_default_value?: number | null;
  ai_confidence?: string | null;
  is_configurable?: boolean;
  resolved_from?: string | null;
  rationale_ro?: string | null;
  review_trigger?: string | null;
}

export type ActivationStatus =
  | "ACTIVE_WITH_CONFIRMED_TRUTH"
  | "ACTIVE_WITH_AI_DEFAULTS"
  | "ACTIVE_WITH_WARNINGS"
  | "BLOCKED";

export interface AiOperationalDecisionItem {
  decision_id: string;
  domain: string;
  target_type: string;
  target_code: string;
  display_name_ro: string;
  formula: string;
  unit: string;
  default_value: number;
  resolved_value: number;
  minimum: number;
  maximum?: number | null;
  currency: string;
  quantity_key?: string | null;
  confidence: "LOW" | "MEDIUM" | "HIGH";
  rationale_ro: string;
  decision_source: string;
  resolved_from: string;
  configurable: boolean;
  has_override: boolean;
  review_trigger?: string | null;
  status: string;
  readiness_effect: string;
  affected_templates: string[];
  packaging_band?: string | null;
  fragile_addon?: number | null;
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
  labor_ownership_note_ro?: string;
  ai_ownership_note_ro?: string;
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
  labor_recipes?: TemplateLaborRecipeItem[];
  labor_summary?: {
    total: number;
    technical_ready: number;
    commercial_ready: number;
    missing_rate: number;
    warnings: number;
    ai_defaults_applied?: number;
  };
  ai_decisions?: AiOperationalDecisionItem[];
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
    activation_status?: ActivationStatus;
    ai_defaults_active?: boolean;
    demoted_blockers?: string[];
    real_blockers_retained?: string[];
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
  putAiDefault: async (decisionId: string, value: number): Promise<void> => {
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/product-system/ai-operational-defaults/${encodeURIComponent(decisionId)}`,
      {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value }),
      },
    );
    if (!res.ok) {
      const detail = await formatApiErrorResponse(
        res,
        `AI default override failed: HTTP ${res.status}`,
      );
      throw new Error(detail);
    }
  },
  deleteAiDefault: async (decisionId: string): Promise<void> => {
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/product-system/ai-operational-defaults/${encodeURIComponent(decisionId)}`,
      { method: "DELETE", credentials: "include" },
    );
    if (!res.ok) {
      const detail = await formatApiErrorResponse(
        res,
        `AI default restore failed: HTTP ${res.status}`,
      );
      throw new Error(detail);
    }
  },
};
