export type IntakeV6CommercialTotals = {
  subtotal_net: number | null;
  vat_rate: number | null;
  vat_amount: number | null;
  total_gross: number | null;
  currency: string;
};

export type IntakeV6PricedQuoteBlocker = {
  code: string;
  message: string;
};

export type IntakeV6PricedQuoteDryRunResponse = {
  pricing_status: "V6_PRICED_DRY_RUN_READY" | "V6_PRICED_DRY_RUN_BLOCKED" | string;
  workspace_id: string;
  workspace_code?: string | null;
  intake_code?: string | null;
  template_code?: string | null;
  pricing_source: string;
  pricing_mode?: string;
  commercial_totals: IntakeV6CommercialTotals;
  commercial_line_items?: Array<Record<string, unknown>>;
  warnings?: string[];
  blockers?: IntakeV6PricedQuoteBlocker[];
  dry_run_only?: boolean;
  pricing_hash?: string;
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
  status: "V6_PRICED_QUOTE_WRITTEN" | "V6_PRICED_QUOTE_WRITE_BLOCKED" | string;
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
