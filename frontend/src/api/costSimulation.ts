/**
 * BUILD 7 — Cost Simulation API adapter.
 *
 * Talks to: POST /api/v1/product-system/simulate-cost
 * Purpose: Read-only cost simulation without persisting any entity.
 *
 * Rules:
 *   - No Quote creation.
 *   - No Order creation.
 *   - Response always includes persisted=false.
 *   - Response always includes trace proving no mutation.
 */

import { getAPIBaseURL } from "@/lib/config";

// ============================================================
// TYPES
// ============================================================

export interface VolumetricQuoteGate {
  simulate_ready?: boolean;
  ready_for_quote?: boolean;
  can_create_commercial_quote?: boolean;
  blockers?: string[];
  warnings?: string[];
  notes?: string[];
  classified?: Record<string, string[]>;
}

export interface CostSimulationRequest {
  template_id: number;
  quantity?: number;
  intake_id?: number;
  quote_input?: Record<string, unknown>;
  pricing?: {
    margin_pct?: number;
    discount_pct?: number;
    vat_pct?: number;
  };
  options?: Record<string, unknown>;
  simulation_context?: {
    source?: string;
    reason?: string;
  };
}

export interface CostSimulationReadiness {
  ready_for_quote: boolean;
  overall_status?: string;
  blockers: string[];
  warnings: string[];
  simulate_ready?: boolean;
  can_create_commercial_quote?: boolean;
  quote_gate?: VolumetricQuoteGate;
}

export interface CostSimulationTrace {
  source: string;
  no_persist: boolean;
  used_template_snapshot: boolean;
  used_costengine_formulas: boolean;
  changed_entities: string[];
}

export interface CostSimulationResponse {
  simulation_id: null;
  persisted: false;
  template_id: number;
  template_code: string;
  cost_engine_version: string;
  readiness: CostSimulationReadiness;
  cost_result: Record<string, unknown>;
  component_breakdown: unknown[];
  linked_module_results?: CostSimulationLinkedModuleResult[];
  warnings: string[];
  blockers: string[];
  status: "simulated" | "blocked" | "error";
  blocked_reasons: string[];
  trace: CostSimulationTrace;
}

export interface CostSimulationLinkedModuleResult extends CostSimulationResponse {
  relation_type?: string;
  pricing_mode?: string;
  execution_mode?: string;
  input_payload?: Record<string, unknown>;
}

// ============================================================
// API
// ============================================================

export const costSimulationApi = {
  /**
   * Run a cost simulation for a product template.
   * Read-only — does not create or modify any entity.
   */
  simulate: async (
    request: CostSimulationRequest
  ): Promise<CostSimulationResponse> => {
    const url = `${getAPIBaseURL()}/api/v1/product-system/simulate-cost`;

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        template_id: request.template_id,
        quantity: request.quantity ?? 1,
        quote_input: request.quote_input ?? {},
        intake_id: request.intake_id,
        pricing: request.pricing ?? {},
        options: request.options ?? {},
        simulation_context: request.simulation_context ?? {
          source: "manual_preview",
          reason: "cost preview",
        },
      }),
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => null);
      const detail =
        errorBody?.detail?.error ?? errorBody?.detail ?? `HTTP ${res.status}`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    return res.json();
  },
};