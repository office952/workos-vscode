import { getAPIBaseURL } from "@/lib/config";

export type PublicationStatus =
  | "DRAFT"
  | "VALIDATED"
  | "E2E_CHECKED"
  | "PUBLISHED"
  | "DEPRECATED"
  | "ARCHIVED";

export type PublicationAction =
  | "enter_draft"
  | "mark_validated"
  | "mark_e2e_checked"
  | "publish"
  | "deprecate"
  | "archive"
  | "reopen_draft";

export interface ProductTemplatePublicationState {
  template_code: string;
  template_id: number;
  db_active: boolean;
  publication_status: PublicationStatus | null;
  effective_status: string;
  legacy_unspecified: boolean;
  publication_version?: number | null;
  last_e2e_verdict?: string | null;
  last_e2e_checked_at?: string | null;
  published_at?: string | null;
  published_by?: string | null;
  offerability_gate: string;
  publish_allowed: boolean;
  publish_blockers: string[];
  publish_warnings?: string[];
  allowed_actions: PublicationAction[];
  active_is_not_published: boolean;
  operational_readiness?: string | null;
  uses_ai_defaults?: boolean;
  ai_decision_ids?: string[];
  publication_eligible?: boolean | null;
  activation_eligible?: boolean | null;
  optional_capability_blockers?: string[];
  recommended_target?: string | null;
  eligibility?: Record<string, unknown> | null;
  contract_version: string;
}

export interface PublicationTransitionResponse {
  ok: boolean;
  state: ProductTemplatePublicationState;
  readiness_verdict?: string | null;
  readiness_e2e_ready?: boolean | null;
  message: string;
  evidence?: Record<string, unknown>;
}

function base(): string {
  return `${getAPIBaseURL()}/api/v1/product-system`;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const err = new Error(`HTTP ${res.status}`) as Error & { status?: number; detail?: unknown };
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  return (await res.json()) as T;
}

export async function getProductTemplatePublication(
  templateCode: string,
): Promise<ProductTemplatePublicationState> {
  return fetchJson(
    `${base()}/templates/${encodeURIComponent(templateCode)}/publication`,
  );
}

export async function transitionProductTemplatePublication(
  templateCode: string,
  action: PublicationAction,
  actor?: string,
): Promise<PublicationTransitionResponse> {
  return fetchJson(`${base()}/templates/${encodeURIComponent(templateCode)}/publication/transition`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, actor: actor ?? "product_system_admin", run_readiness: true }),
  });
}
