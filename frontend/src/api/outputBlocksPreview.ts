/**
 * BUILD 8 — Output Blocks Render Preview API adapter.
 *
 * Talks to: POST /api/v1/product-system/output-blocks/render-preview
 *           GET  /api/v1/entities/quotes/{quote_id}/output-blocks-preview
 *
 * Purpose: Read-only rendering of Output Blocks as preview.
 *
 * Rules:
 *   - No Quote creation/modification.
 *   - No Order creation/modification.
 *   - No ProductTemplate mutation.
 *   - No BlueprintDossier mutation.
 *   - Response always includes persisted=false.
 *   - Response always includes trace.changed_entities=[].
 */

import { getAPIBaseURL } from "@/lib/config";

// ============================================================
// TYPES
// ============================================================

export interface RenderPreviewQuoteContext {
  quote_id?: number | null;
  client_name?: string;
  quantity?: number;
  dimensions?: {
    width_mm?: number;
    height_mm?: number;
    depth_mm?: number;
  };
  selected_options?: Record<string, unknown>;
}

export interface RenderPreviewRequest {
  template_id?: number | null;
  dossier_id?: number | null;
  document_type?: string;
  audience?: string;
  block_types?: string[];
  quote_context?: RenderPreviewQuoteContext;
  render_mode?: string;
}

export interface RenderedBlock {
  block_id: string;
  block_type: string;
  title: string;
  approval_status: string;
  rendered_text: string;
  variables_used: Array<{
    name: string;
    source_field: string;
    value: unknown;
    resolved: boolean;
  }>;
  warnings: string[];
  blockers: string[];
}

export interface RenderPreviewTrace {
  source: string;
  no_persist: boolean;
  changed_entities: string[];
  live_changes_affect_accepted_orders: boolean;
}

export interface RenderPreviewResponse {
  persisted: false;
  template_id: number | null;
  dossier_id: number | null;
  document_type: string;
  audience: string;
  render_mode: string;
  blocks: RenderedBlock[];
  warnings: string[];
  blockers: string[];
  trace: RenderPreviewTrace;
}

// ============================================================
// API
// ============================================================

export const outputBlocksPreviewApi = {
  /**
   * Render Output Blocks preview for a template/dossier.
   * Read-only — does not create or modify any entity.
   */
  renderPreview: async (
    request: RenderPreviewRequest
  ): Promise<RenderPreviewResponse> => {
    const url = `${getAPIBaseURL()}/api/v1/product-system/output-blocks/render-preview`;

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        template_id: request.template_id ?? null,
        dossier_id: request.dossier_id ?? null,
        document_type: request.document_type ?? "offer",
        audience: request.audience ?? "client",
        block_types: request.block_types ?? null,
        quote_context: request.quote_context ?? null,
        render_mode: request.render_mode ?? "preview",
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

  /**
   * Get Output Blocks preview for a quote (bridge).
   * Read-only — does not modify the quote.
   */
  quotePreview: async (quoteId: number): Promise<RenderPreviewResponse> => {
    const url = `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-blocks-preview`;

    const res = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
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