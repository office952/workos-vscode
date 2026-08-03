export type IntakeV6CommercialAdjustmentTrace = {
  basis?: string | null;
  markup_percent?: number | null;
  markup_value?: number | null;
  manual_adjustment_ron?: number | null;
  discount_percent?: number | null;
  discount_value?: number | null;
};

export type IntakeV6CommercialTotals = {
  subtotal_net: number | null;
  vat_rate: number | null;
  vat_amount: number | null;
  total_gross: number | null;
  currency: string;
  /** Raw 7G commercial subtotal before operator Adaos/Discount/Ajustare. */
  commercial_base_subtotal?: number | null;
  commercial_adjustment_trace?: IntakeV6CommercialAdjustmentTrace | null;
};

export type IntakeV6PricedQuoteBlocker = {
  code: string;
  message: string;
};

export type AcmPanelCommercialPreviewLine = {
  code?: string | null;
  label?: string | null;
  quantity?: number | null;
  unit?: string | null;
  rate?: number | null;
  amount?: number | null;
  source?: string | null;
  status?: string | null;
  warnings?: string[];
  basis_type?: string | null;
};

export type AcmPanelCommercialPreview = {
  status?: string | null;
  currency?: string | null;
  estimated_total?: number | null;
  lines?: AcmPanelCommercialPreviewLine[];
  geometry_summary?: {
    assembly_width_mm?: number | null;
    assembly_height_mm?: number | null;
    envelope_width_mm?: number | null;
    envelope_height_mm?: number | null;
    face_area_m2?: number | null;
    cut_length_m?: number | null;
    fold_length_m?: number | null;
    v_groove_l1_ml?: number | null;
    v_groove_l2_ml?: number | null;
    v_groove_total_ml?: number | null;
    assembly_exterior_perimeter_m?: number | null;
    panel_count?: number | null;
    joint_count?: number | null;
    envelope_ignored_for_multi_panel?: boolean | null;
    path_measurement_status?: string | null;
    path_measurement_source?: string | null;
  } | null;
  production_geometry_metrics?: Record<string, unknown> | null;
  material_reference?: {
    preferred_sku?: string | null;
    legacy_alias?: string | null;
    legacy_excluded_from_duplicate?: boolean | null;
  } | null;
  rate_version?: string | null;
  authority_summary?: Record<string, unknown> | null;
  warnings?: string[];
  blockers?: string[];
  final_eligibility?: boolean;
  offer_eligibility?: boolean;
  execution_eligibility?: boolean;
  line_count?: number | null;
  hourly_commercial_detected?: boolean;
};

export interface IntakeV6CommercialCurrencyBucket {
	currency: string;
	subtotal: number;
}

export interface IntakeV6CommercialProductSubtotal {
	/** "letters" | "acm_panel" — backend product ownership key. */
	product_key: string;
	label: string;
	line_codes: string[];
	subtotals_by_currency: IntakeV6CommercialCurrencyBucket[];
	blocked: boolean;
	blocker_codes: string[];
	/** Lines awaiting an Owner decision — priced at nothing, so any subtotal is partial. */
	pending_line_codes?: string[];
}

/**
 * Canonical backend commercial product breakdown (CPP).
 * The frontend only formats what the backend decided — it never sums lines
 * into a second commercial total and never converts between currencies.
 */
export interface IntakeV6CommercialProductBreakdown {
	products: IntakeV6CommercialProductSubtotal[];
	subtotals_by_currency: IntakeV6CommercialCurrencyBucket[];
	currency_mix_detected: boolean;
	/** Scoped presentation currency from CPP (EUR for volumetric+ACM pilot). */
	presentation_currency?: string | null;
	complete_offer_total: number | null;
	complete_offer_total_currency: string | null;
	/** e.g. "COMMERCIAL_CURRENCY_MIX_UNRESOLVED", "COMMERCIAL_PRODUCT_BLOCKED". */
	complete_offer_total_unavailable_reason: string | null;
	/** True when a total exists but omits Owner-pending lines. */
	complete_offer_total_is_partial?: boolean;
	pending_line_codes?: string[];
	tax_status: "tax_exclusive";
	/** null when no canonical fiscal policy value was resolved. */
	vat_policy_source: string | null;
	/** null when unknown — never substitute a default VAT rate. */
	vat_rate_percent: number | null;
}

export type IntakeV6PricedQuoteDryRunResponse = {
  pricing_status: "V6_PRICED_DRY_RUN_READY" | "V6_PRICED_DRY_RUN_BLOCKED" | string;
  pricing_authority?: string | null;
  commercial_authority_status?: "ready" | "blocked" | string | null;
  workspace_id: string;
  workspace_code?: string | null;
  intake_code?: string | null;
  template_code?: string | null;
  pricing_source: string;
  pricing_mode?: string;
	commercial_totals: IntakeV6CommercialTotals;
	/** Optional — absent on older responses and on blocked previews. */
	commercial_product_breakdown?: IntakeV6CommercialProductBreakdown | null;
	commercial_line_items?: Array<Record<string, unknown>>;
  acm_panel_commercial_preview?: AcmPanelCommercialPreview | null;
  internal_cost_trace?: Record<string, unknown>;
  estimated_internal_cost_trace?: Record<string, unknown>;
  diagnostic_cost_plus_trace?: Record<string, unknown> | null;
  commercial_proposal_trace?: Record<string, unknown>;
  warnings?: string[];
  blockers?: IntakeV6PricedQuoteBlocker[];
  dry_run_only?: boolean;
  pricing_hash?: string;
};

export type IntakeV6LogicalListCategory = "MATERIALE" | "SERVICII_OPERATII" | "MANOPERA" | string;

export type IntakeV6LogicalListLineTrace = {
  line_id: string;
  display_label: string;
  category: IntakeV6LogicalListCategory;
  product_template_code?: string | null;
  component_code?: string | null;
  module_code?: string | null;
  formula_code_proposed?: string | null;
  formula_version_proposed?: string | null;
  formula_status?: string | null;
  status?: string | null;
  quantity?: number | null;
  unit?: string | null;
  subtotal?: number | null;
  currency?: string | null;
  runtime_source?: string | null;
  child_rows?: Array<Record<string, unknown>>;
  preferences?: Record<string, unknown>;
  gaps?: string[];
  warnings?: string[];
  blockers?: string[];
};

export type IntakeV6LogicalListReadModelResponse = {
  read_only?: boolean;
  source?: string;
  workspace_id?: string | null;
  workspace_code?: string | null;
  template_code?: string | null;
  categories?: string[];
  core_row_count?: number | null;
  composition_contract_row_count?: number | null;
  /** ACM commercial.* rows surfaced into the logical list (not Letters↔Bond conn). */
  composition_acm_row_count?: number | null;
  /** letters_acm_conn_* commercial rows only. */
  composition_connection_row_count?: number | null;
  target_core_row_count?: number | null;
  core_rows_complete?: boolean;
  rows?: IntakeV6LogicalListLineTrace[];
  excluded_extra_commercial_lines?: Array<Record<string, unknown>>;
  warnings?: string[];
  blockers?: string[];
  runtime_totals?: Record<string, unknown>;
  validation?: Record<string, boolean | string | number | null>;
};

export type IntakeV6PricedQuoteWriteRequest = {
  quote_id: number;
  expected_total_gross: number;
  expected_pricing_hash?: string | null;
  operator_confirmation?: boolean;
};

export type IntakeV6OfferHandoffRequest = {
  client_analysis_hash: string;
  expected_total_gross: number;
  expected_pricing_hash?: string | null;
  operator_confirmation?: boolean;
};

export type IntakeV6OfferHandoffResponse = {
  status:
    | "V6_PRICED_QUOTE_WRITTEN"
    | "V6_PRICED_QUOTE_WRITE_BLOCKED"
    | "V6_OFFER_FROM_SNAPSHOT_WRITTEN"
    | "V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT"
    | "V6_OFFER_FROM_SNAPSHOT_BLOCKED"
    | string;
  quote_created: boolean;
  quote_id: number;
  quote_code: string;
  quote_status: string;
  source_workspace_id: string;
  commercial_totals?: IntakeV6CommercialTotals & {
    discount?: number;
    total_before_vat?: number;
    vat?: number;
    total_gross?: number;
  };
  line_items?: Array<Record<string, unknown>>;
  pricing_trace?: {
    pricing_source?: string;
    pricing_hash?: string;
  };
  blockers?: IntakeV6PricedQuoteBlocker[];
  warnings?: string[];
  can_create_quote_snapshot?: boolean;
  commercial_authority_source?: string | null;
  snapshot_v2?: Record<string, unknown> | null;
  snapshot_authoritative_offer?: boolean;
  next_route?: string;
};

export type IntakeV6PricedQuoteWriteResponse = {
  status: "V6_PRICED_QUOTE_WRITTEN" | "V6_PRICED_QUOTE_WRITE_BLOCKED" | string;
  quote_id: number;
  quote_code?: string | null;
  commercial_totals?: IntakeV6CommercialTotals & {
    discount?: number;
    total_before_vat?: number;
    vat?: number;
    total_gross?: number;
  };
  line_items?: Array<Record<string, unknown>>;
  pricing_trace?: {
    pricing_source?: string;
    pricing_hash?: string;
  };
  blockers?: IntakeV6PricedQuoteBlocker[];
  warnings?: string[];
  can_create_quote_snapshot?: boolean;
};

export type IntakeV6QuoteSnapshotV2CreateRequest = {
  operator_confirmation?: boolean;
  expected_grand_total?: number | null;
  expected_pricing_hash?: string | null;
};

export type IntakeV6QuoteSnapshotV2CreateResponse = {
  status: "V6_QUOTE_SNAPSHOT_V2_CREATED" | "V6_QUOTE_SNAPSHOT_V2_BLOCKED" | string;
  quote_id?: number | null;
  quote_code?: string | null;
  snapshot_id?: number | null;
  blockers?: IntakeV6PricedQuoteBlocker[];
  warnings?: string[];
  can_accept_quote?: boolean;
  can_create_order?: boolean;
};
