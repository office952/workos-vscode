/**
 * BUILD 5 — Quote Commercial Document API adapter.
 *
 * Functions:
 *   getQuoteCommercialDocument(quoteId) — fetch commercial document DTO
 *   downloadQuoteDocument(quoteId, format) — trigger download of export
 *
 * Rules:
 *   - No silent mock fallback.
 *   - Throws on backend error.
 *   - Uses canonical route pattern.
 */

import { getAPIBaseURL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface CommercialDocumentClient {
  name: string;
  contact_person?: string | null;
  company?: string | null;
  email?: string | null;
  phone?: string | null;
  fiscal_id?: string | null;
  address?: string | null;
}

export interface CommercialTerms {
  currency: string;
  tva_percent: number;
  validity_days: number;
  validity_display?: string | null;
  valid_until?: string | null;
  payment_terms?: string | null;
  delivery_terms?: string | null;
  warranty_terms?: string | null;
}

export interface ProductText {
  client_title?: string | null;
  short_description?: string | null;
  technical_description?: string | null;
  materials_summary?: string | null;
  operations_summary?: string | null;
  included_finishes?: string | null;
  optional_finishes?: string | null;
  production_assumptions?: string | null;
  externalization_note?: string | null;
  limitations?: string | null;
}

export interface DocumentLineItem {
  description: string;
  product_code?: string;
  quantity: number;
  unit_price: number;
  total: number;
  type?: string;
}

export interface DocumentTotals {
  subtotal: number;
  discount: number;
  discount_pct: number;
  total_before_vat: number;
  tva: number;
  grand_total: number;
  margin_pct: number;
  currency: string;
}

export interface DocumentReadiness {
  ready_for_quote?: boolean | null;
  overall_status: string;
  warnings: string[];
  blockers: string[];
  source: string;
}

export interface DocumentSection {
  id: string;
  title: string;
  content: Record<string, unknown>;
}

export interface ProductSummary {
  product_code?: string | null;
  product_name: string;
  family?: string | null;
  description: string;
  technical_description?: string | null;
  externalized: boolean;
  template_code?: string | null;
}

export interface CommercialDocument {
  quote_id: number;
  quote_code: string;
  status: string;
  version: number;
  client: CommercialDocumentClient;
  commercial: CommercialTerms;
  product_summary: ProductSummary;
  product_text: ProductText;
  line_items: DocumentLineItem[];
  component_breakdown?: unknown[] | null;
  totals: DocumentTotals;
  readiness: DocumentReadiness;
  document: {
    title: string;
    sections: DocumentSection[];
    generated_at: string;
    source: string;
    format_version: string;
  };
  metadata: {
    created_at?: string | null;
    updated_at?: string | null;
    valid_until?: string | null;
    assigned_to?: string | null;
    intake_code?: string | null;
    notes?: string | null;
  };
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * Fetch the commercial document DTO for a quote.
 * Throws on backend error — no silent fallback.
 */
export async function getQuoteCommercialDocument(
  quoteId: number
): Promise<CommercialDocument> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/commercial-document`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to fetch commercial document for quote ${quoteId}: ${res.status} — ${detail}`
    );
  }

  return res.json();
}

/**
 * Download the commercial document as HTML export.
 * Opens a download in the browser.
 */
export async function downloadQuoteDocument(
  quoteId: number,
  format: "html" = "html"
): Promise<void> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/commercial-document/export?format=${format}`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to export commercial document for quote ${quoteId}: ${res.status} — ${detail}`
    );
  }

  // Trigger browser download
  const blob = await res.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `oferta_${quoteId}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(downloadUrl);
}