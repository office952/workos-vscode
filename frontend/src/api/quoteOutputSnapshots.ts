/**
 * BUILD 10 — Quote Output Snapshot Candidate API adapter.
 *
 * Provides typed access to snapshot candidate endpoints.
 * Read-only display + controlled lifecycle actions.
 *
 * Rules:
 *   - No Quote mutation
 *   - No Order mutation
 *   - No CostEngine call
 *   - No email/send
 */

import { getAPIBaseURL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface QuoteOutputSnapshotCandidate {
  snapshot_id: number;
  quote_id: number;
  quote_code: string;
  snapshot_code: string;
  snapshot_type: string;
  status: string;
  version: number;
  source_template_id: number | null;
  source_template_code: string | null;
  source_dossier_id: number | null;
  source_dossier_version: number | null;
  rendered_sections_json: Array<{
    section_id?: string;
    title?: string;
    rendered_text?: string;
    warnings?: string[];
    blockers?: string[];
  }> | null;
  commercial_summary_json: {
    subtotal?: number;
    vat?: number;
    total?: number;
    currency?: string;
  } | null;
  warnings: string[];
  blockers: string[];
  variables_used: Record<string, unknown>;
  trace: Record<string, unknown>;
  content_hash: string | null;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  archived_at: string | null;
  superseded_by_snapshot_id: number | null;
  notes: string | null;
  persisted: boolean;
  not_order_snapshot: boolean;
  not_final_contract: boolean;
  not_sent_to_client: boolean;
}

export interface CreateSnapshotRequest {
  source?: string;
  notes?: string;
  initial_status?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function createOutputSnapshot(
  quoteId: number,
  request: CreateSnapshotRequest = {}
): Promise<QuoteOutputSnapshotCandidate> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        source: request.source || "quote_output_composition_preview",
        notes: request.notes || null,
        initial_status: request.initial_status || "draft",
      }),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to create snapshot" }));
    throw new Error(err.detail || "Failed to create snapshot");
  }
  return res.json();
}

export async function listOutputSnapshots(
  quoteId: number
): Promise<QuoteOutputSnapshotCandidate[]> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots`,
    { headers: getAuthHeaders() }
  );
  if (!res.ok) throw new Error("Failed to list snapshots");
  return res.json();
}

export async function getOutputSnapshot(
  quoteId: number,
  snapshotId: number
): Promise<QuoteOutputSnapshotCandidate> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}`,
    { headers: getAuthHeaders() }
  );
  if (!res.ok) throw new Error("Snapshot not found");
  return res.json();
}

export async function submitSnapshotForReview(
  quoteId: number,
  snapshotId: number
): Promise<QuoteOutputSnapshotCandidate> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}/submit-review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to submit for review" }));
    throw new Error(err.detail || "Failed to submit for review");
  }
  return res.json();
}

export async function approveSnapshot(
  quoteId: number,
  snapshotId: number
): Promise<QuoteOutputSnapshotCandidate> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to approve" }));
    throw new Error(err.detail || "Failed to approve");
  }
  return res.json();
}

export async function archiveSnapshot(
  quoteId: number,
  snapshotId: number
): Promise<QuoteOutputSnapshotCandidate> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}/archive`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to archive" }));
    throw new Error(err.detail || "Failed to archive");
  }
  return res.json();
}

export async function rejectSnapshot(
  quoteId: number,
  snapshotId: number,
  reason?: string
): Promise<QuoteOutputSnapshotCandidate> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}/reject`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ reason: reason || null }),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to reject" }));
    throw new Error(err.detail || "Failed to reject");
  }
  return res.json();
}

export function getSnapshotExportUrl(quoteId: number, snapshotId: number): string {
  return `${getAPIBaseURL()}/api/v1/entities/quotes/${quoteId}/output-snapshots/${snapshotId}/export`;
}