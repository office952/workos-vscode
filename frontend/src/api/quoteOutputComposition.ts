/**
 * BUILD 9 — Quote Output Composition Preview API adapter.
 *
 * Read-only endpoints for output composition preview.
 * No persist, no mutation, no side effects.
 */

import { getAPIBaseURL } from "@/lib/config";

export interface QuoteOutputCompositionPreview {
  persisted: boolean;
  quote_id: number | null;
  quote_code: string;
  composition_type: string;
  source: Record<string, string>;
  template_link: {
    status: string;
    template_id?: number;
    template_code?: string;
    dossier_id?: number | null;
  };
  sections: Array<{
    section_id: string;
    title: string;
    source: string;
    rendered_text: string;
    warnings: string[];
    blockers: string[];
  }>;
  commercial_summary: {
    subtotal: number;
    vat: number;
    total: number;
    currency: string;
  };
  warnings: string[];
  blockers: string[];
  trace: {
    no_persist: boolean;
    changed_entities: string[];
    no_quote_mutation: boolean;
    no_order_mutation: boolean;
    no_snapshot_created: boolean;
    not_client_final: boolean;
  };
}

export interface OutputBlocksCoverage {
  total_templates: number;
  covered_count: number;
  partial_count: number;
  missing_count: number;
  coverage_pct: number;
  covered: Array<{
    template_id: number;
    template_code: string;
    description: string;
    dossier_id: number;
    block_count: number;
  }>;
  partial: Array<{
    template_id: number;
    template_code: string;
    description: string;
    dossier_id: number;
    block_count: number;
    complete_blocks: number;
    reason: string;
  }>;
  missing: Array<{
    template_id: number;
    template_code: string;
    description: string;
    dossier_id?: number;
    reason: string;
  }>;
}

/**
 * Fetch the output composition preview for a quote.
 * Read-only — no persist, no mutation.
 */
export async function fetchQuoteOutputCompositionPreview(
  quoteId: number
): Promise<QuoteOutputCompositionPreview> {
  const baseUrl = getAPIBaseURL();
  const res = await fetch(
    `${baseUrl}/api/v1/entities/quotes/${quoteId}/output-composition-preview`,
    { credentials: "include" }
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch output composition preview: ${res.status}`);
  }
  return res.json();
}

/**
 * Get the HTML export URL for the output composition preview.
 * Returns the URL string (browser will handle download).
 */
export function getQuoteOutputCompositionExportUrl(quoteId: number): string {
  return `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-composition-preview/export`;
}

/**
 * Fetch output blocks coverage diagnostics.
 * Read-only — no persist, no mutation.
 */
export async function fetchOutputBlocksCoverage(): Promise<OutputBlocksCoverage> {
  const baseUrl = getAPIBaseURL();
  const res = await fetch(
    `${baseUrl}/api/v1/product-system/output-blocks/coverage`,
    { credentials: "include" }
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch output blocks coverage: ${res.status}`);
  }
  return res.json();
}