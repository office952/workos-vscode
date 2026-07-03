/**
 * BUILD 11 — Quote Output Snapshot Governance API adapter.
 *
 * Read-only governance layer for snapshot eligibility evaluation.
 *
 * Rules:
 *   - No Quote mutation
 *   - No Order mutation
 *   - No Order creation
 *   - No status change
 *   - No contract generation
 *   - No send to client
 *   - Pure read-only evaluation
 */

import { getAPIBaseURL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type EligibilityStatus = "eligible" | "blocked" | "needs_review" | "missing";

export interface SnapshotEligibilityResponse {
  quote_id: number;
  eligibility_status: EligibilityStatus;
  reasons: string[];
  approved_snapshot_id: number | null;
  approved_snapshot_code: string | null;
  approved_snapshot_version: number | null;
  conflict_snapshot_ids: number[];
  blockers: string[];
  warnings: string[];
  source_metadata_present: boolean;
  source_template_id: number | null;
  source_template_code: string | null;
  source_dossier_id: number | null;
  source_dossier_version: number | null;
  source_output_block_versions: Array<Record<string, unknown>>;
  total_snapshots: number;
  snapshots_by_status: Record<string, number>;
  governance_version: string;
  read_only: boolean;
  no_order_mutation: boolean;
  no_quote_status_change: boolean;
  no_order_creation: boolean;
  no_contract_generation: boolean;
  no_send_to_client: boolean;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

/**
 * Fetch snapshot eligibility status for a quote.
 * Read-only — no mutations.
 */
export async function getSnapshotEligibility(
  quoteId: number
): Promise<SnapshotEligibilityResponse> {
  const base = getAPIBaseURL();
  const url = `${base}/api/v1/entities/quotes/${quoteId}/output-snapshots/governance/eligibility`;

  const response = await fetch(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch eligibility: ${response.status}`
    );
  }

  return response.json();
}