/**
 * ConfirmJobProductTruth client — job-level Product Truth revision.
 * Catalog is never written. No ProductInstance tables.
 */

import { getAPIBaseURL } from "@/lib/config";

export type JobConfirmationState = "unconfirmed" | "confirmed" | "stale_after_edit" | string;

export interface JobRevisionMetadata {
  revision: number;
  content_hash: string;
  confirmation_state: JobConfirmationState;
  confirmed_at?: string | null;
  confirmed_by?: string | null;
  expected_draft_hash?: string | null;
  root_template_code?: string | null;
  root_template_version?: string | null;
  contract_version?: string;
  source?: string;
  provenance?: Record<string, unknown>;
}

export interface ConfirmJobProductTruthResponse {
  workspace_id: string;
  workspace_code?: string | null;
  write_performed: boolean;
  idempotent_noop: boolean;
  metadata: JobRevisionMetadata;
  pinned_bag_keys: string[];
  draft_hash: string;
  previous_revision?: number | null;
}

export interface JobProductTruthStatusResponse {
  workspace_id: string;
  has_job_revision: boolean;
  metadata?: JobRevisionMetadata | null;
  draft_hash: string;
  is_stale: boolean;
  commercial_freeze_allowed: boolean;
}

function apiBase(): string {
  return `${getAPIBaseURL()}/api/v1/intake-v6`;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const err = new Error(`HTTP ${res.status}`) as Error & {
      status: number;
      detail: unknown;
    };
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  return (await res.json()) as T;
}

export async function getJobProductTruthStatus(
  workspaceId: string,
): Promise<JobProductTruthStatusResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/product-truth/job-status`,
  );
}

export async function confirmJobProductTruth(
  workspaceId: string,
  body: {
    expected_revision: number;
    expected_draft_hash?: string | null;
    expected_content_hash?: string | null;
    root_template_code?: string | null;
    correction_reason?: string | null;
  },
): Promise<ConfirmJobProductTruthResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/product-truth/confirm-job`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}
