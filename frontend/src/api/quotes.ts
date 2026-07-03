/**
 * Quote pricing API wrapper.
 *
 * Thin, typed wrapper around the real backend endpoint
 *   POST /api/v1/entities/quotes/price
 *
 * The frontend NEVER computes costs. It only passes:
 *   - product_template       (canonical row from product_templates)
 *   - user_config            (quantity + dimensions chosen in the wizard)
 *   - pricing                (margin/vat/discount as agreed with client)
 *   - quote_input            (formula-based inputs required by the template)
 *   - client_name            (used by the orchestrator for persistence)
 *
 * The backend returns the full hierarchical snapshot (see Sprint #21.4 proof):
 *   {
 *     quote_id: number,
 *     snapshot: {
 *       product_definition: {...},
 *       cost_result: { total_cost, materials_cost, labour_cost, breakdown: [...] },
 *       pricing: { margin_pct, discount_pct, vat_pct },
 *       price: { net, gross, final },
 *       status: "priced" | "draft" | ...,
 *       blocked_reasons: string[]
 *     }
 *   }
 *
 * On HTTP 422 (validation block, e.g. NEEDS_QUOTE_INPUT) the backend returns
 *   { detail: { status: "blocked", blocked_reasons: [...] } }
 * which we surface back to the caller via `QuotePricingError`.
 */
import { getAPIBaseURL } from "../lib/config";
import type { ProductTemplateEntity } from "../lib/api";

const apiBase = () => `${getAPIBaseURL()}/api/v1`;

// ============================================================
// Types — mirror backend request/response contract exactly
// ============================================================
export interface QuoteDimensions {
  width_mm: number;
  height_mm: number;
  depth_mm?: number;
}

export interface QuoteUserConfig {
  quantity: number;
  dimensions: QuoteDimensions;
}

export interface QuotePricingInput {
  margin_pct: number;
  vat_pct: number;
  discount_pct: number;
}

/**
 * Formula-based inputs required by TPL-ACP-LIGHT-ROUTED.
 *
 * Keys MUST match the `requires_quote_input` entries serialized in
 * `components_json`. The names below are the full set seeded by
 * `scripts/seed_tpl_acp_light_routed.py` and validated in Sprint #21.4.
 *
 * For templates other than TPL-ACP-LIGHT-ROUTED, additional keys may be
 * needed — this interface is open via the index signature below.
 */
export interface QuoteInputPayload {
  front_face_area_m2?: number;
  personalization_path_length_mm?: number;
  personalization_bounding_area_m2?: number;
  diffuser_cut_path_length_mm?: number;
  led_count?: number;
  relief_cut_path_length_mm?: number;
  /** TPL-VOLUMETRIC-LETTERS preliminary costing */
  letter_face_area_m2?: number;
  letter_perimeter_m?: number;
  letter_count?: number;
  return_depth_mm?: number;
  selected_psu_watts?: number;
  psu_watts?: number;
  led_module_count?: number;
  mounting_template_area_m2?: number;
  /** Whole RAL spray tubes estimate — CostEngine charges ceil(value). */
  paint_tube_count?: number;
  /** Forex 10 mm back optional bevel — adds 2 CNC passes when true. */
  back_bevel_enabled?: boolean;
  /** Face finish — Oracal / print priced via Pricing Registry when not none. */
  face_finish_type?:
    | "none"
    | "oracal_651"
    | "printed_vinyl"
    | "printed_laminated_vinyl";
  /** Mounting / support system (independent from Forex mounting template). */
  mounting_system?:
    | "direct_wall"
    | "steel_bars"
    | "aluminum_bars"
    | "acm_panel";
  /** Optional Forex mounting template — independent from mounting_system. */
  mounting_template_enabled?: boolean;
  /** Assembly width (mm) — used for auto premount bar length when override absent. */
  width_mm?: number;
  /** Optional total premount bar length override (ml). */
  mounting_bar_length_m?: number;
  /** Premount bar count — default 2 (top + bottom). */
  mounting_bar_count?: number;
  /** Selectable profile e.g. 30x30x1.5 mm — priced profiles only in registry. */
  mounting_bar_profile?: string;
  /** Production metadata — not used for costing unless priced path exists. */
  paint_ral_code?: string;
  paint_ral_name?: string;
  paint_finish?: string;
  face_vinyl_color_code?: string;
  face_vinyl_color_name?: string;
  face_vinyl_roll_width_mm?: number;
  face_vinyl_finish?: string;
  face_vinyl_notes?: string;
  /** Intake subtype when Oracal 8500 priced via oracal_651 path. */
  face_finish_subtype?: string;
  mounting_notes?: string;
  lighting_notes?: string;
  [key: string]: number | boolean | string | undefined;
}

export interface QuotePriceRequest {
  product_template?: ProductTemplateEntity;
  user_config?: QuoteUserConfig;
  pricing?: QuotePricingInput;
  client_name?: string;
  quote_input?: QuoteInputPayload;
  /** DB intake id for vector/file readiness gate on commercial quote. */
  intake_id?: number;
}

export interface QuoteBreakdownLine {
  type: "material" | "labour" | "machine" | "external" | "overhead" | string;
  name: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  total: number;
}

export interface QuoteCostResult {
  is_valid: boolean;
  currency: string;
  materials_cost: number;
  labour_cost: number;
  machine_cost: number;
  external_cost: number;
  overhead_cost: number;
  total_cost: number;
  parent_total_cost?: number;
  linked_modules_total_cost?: number;
  composite_total_cost?: number;
  estimated_time_minutes: number;
  breakdown: QuoteBreakdownLine[];
  validation: {
    missing_cost_data: string[];
    warnings: string[];
  };
}

export interface QuoteSnapshot {
  product_definition: unknown;
  cost_result: QuoteCostResult;
  linked_module_results?: Array<Record<string, unknown>>;
  pricing: QuotePricingInput;
  price: { net: number; gross: number; final: number };
  status: string;
  blocked_reasons: string[];
}

export interface QuotePriceResponse {
  quote_id: number;
  quote_code?: string;
  quote_version?: number;
  revised?: boolean;
  legacy_reconstructed?: boolean;
  snapshot: QuoteSnapshot;
}

/** Payload passed to QuoteWizard / volumetric flow after commercial quote creation. */
export interface QuoteCreatedPayload {
  quoteId: number;
  quoteCode?: string;
}

export interface QuoteSendLogRequest {
  channel: string;
  recipient?: string;
  note?: string;
  document_ref?: string;
}

export interface QuoteSendLogResponse {
  quote_id: number;
  quote_code?: string;
  status: string;
  quote_version: number;
  sent_at: string;
  status_changed: boolean;
  log_entry: {
    channel: string;
    sent_at: string;
    quote_version: number;
    recipient?: string;
    note?: string;
    document_ref?: string;
    actor_email?: string;
  };
}

// ============================================================
// Error type
// ============================================================
export class QuotePricingError extends Error {
  status: number;
  blockedReasons: string[];

  constructor(message: string, status: number, blockedReasons: string[] = []) {
    super(message);
    this.name = "QuotePricingError";
    this.status = status;
    this.blockedReasons = blockedReasons;
  }
}

// ============================================================
// API call
// ============================================================
export async function priceQuote(
  body: QuotePriceRequest
): Promise<QuotePriceResponse> {
  const res = await fetch(`${apiBase()}/entities/quotes/price`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detailMsg = `HTTP ${res.status}`;
    let blocked: string[] = [];
    try {
      const errBody = await res.json();
      const detail = errBody?.detail;
      if (detail && typeof detail === "object") {
        if (Array.isArray(detail.blocked_reasons)) {
          blocked = detail.blocked_reasons.map(String);
        }
        if (detail.status) {
          detailMsg = `${detail.status}${
            blocked.length ? `: ${blocked.length} reason(s)` : ""
          }`;
        }
      } else if (typeof detail === "string") {
        detailMsg = detail;
      }
    } catch {
      // non-JSON error body — keep default detailMsg
    }
    throw new QuotePricingError(detailMsg, res.status, blocked);
  }

  return (await res.json()) as QuotePriceResponse;
}

export async function postQuoteSendLog(
  quoteDbId: number,
  body: QuoteSendLogRequest
): Promise<QuoteSendLogResponse> {
  const res = await fetch(`${apiBase()}/entities/quotes/${quoteDbId}/send-log`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detailMsg = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      const detail = errBody?.detail;
      if (typeof detail === "string") {
        detailMsg = detail;
      } else if (detail && typeof detail === "object" && detail.message) {
        detailMsg = String(detail.message);
      }
    } catch {
      // non-JSON error body
    }
    throw new Error(detailMsg);
  }

  return (await res.json()) as QuoteSendLogResponse;
}

export async function priceExistingQuote(
  quoteDbId: number,
  body: QuotePriceRequest
): Promise<QuotePriceResponse> {
  const res = await fetch(`${apiBase()}/entities/quotes/${quoteDbId}/price`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detailMsg = `HTTP ${res.status}`;
    let blocked: string[] = [];
    try {
      const errBody = await res.json();
      const detail = errBody?.detail;
      if (detail && typeof detail === "object") {
        if (Array.isArray(detail.blocked_reasons)) {
          blocked = detail.blocked_reasons.map(String);
        }
        if (detail.message) {
          detailMsg = String(detail.message);
        } else if (detail.error) {
          detailMsg = String(detail.error);
        } else if (detail.status) {
          detailMsg = `${detail.status}${
            blocked.length ? `: ${blocked.length} reason(s)` : ""
          }`;
        }
      } else if (typeof detail === "string") {
        detailMsg = detail;
      }
    } catch {
      // non-JSON error body
    }
    throw new QuotePricingError(detailMsg, res.status, blocked);
  }

  return (await res.json()) as QuotePriceResponse;
}