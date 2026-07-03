/**
 * Live-stack probe for Intake V4 Playwright specs.
 * Requires backend :8000 with dev auth (scripts/start-dev.ps1).
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const BACKEND_URL = process.env.PW_BACKEND_URL ?? "http://localhost:8000";

export interface IntakeV4LiveProbe {
  backendHealthy: boolean;
  reason?: string;
}

export async function probeIntakeV4LiveBackend(): Promise<IntakeV4LiveProbe> {
  try {
    const health = await fetch(`${BACKEND_URL}/health`, { signal: AbortSignal.timeout(8_000) });
    if (!health.ok) {
      return { backendHealthy: false, reason: `Backend health ${health.status}` };
    }
    return { backendHealthy: true };
  } catch (err) {
    return {
      backendHealthy: false,
      reason: err instanceof Error ? err.message : "Backend unreachable",
    };
  }
}

/** Create a V4 workspace via API (dev auth bypass on local stack). */
export async function createIntakeV4WorkspaceForE2e(title = "e2e-v4-workspace"): Promise<string> {
  const response = await fetch(`${BACKEND_URL}/api/v1/intake-v4/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, template_code: "TPL-VOLUMETRIC-LETTERS" }),
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`V4 workspace create failed (${response.status}): ${text.slice(0, 200)}`);
  }
  const body = (await response.json()) as { id?: string };
  if (!body.id) throw new Error("V4 workspace create returned no id");
  return body.id;
}

export async function fetchIntakeV4WorkspacePayload(
  workspaceId: string,
): Promise<Record<string, unknown>> {
  const response = await fetch(`${BACKEND_URL}/api/v1/intake-v4/workspaces/${workspaceId}`, {
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) {
    throw new Error(`V4 workspace fetch failed (${response.status})`);
  }
  const body = (await response.json()) as { payload?: Record<string, unknown> };
  return body.payload ?? {};
}

export function sha256HexFromUtf8(text: string): string {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

export function sha256HexFromFile(filePath: string): string {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

export async function getPersistedAnalysisFileHash(workspaceId: string): Promise<string> {
  const payload = await fetchIntakeV4WorkspacePayload(workspaceId);
  const svgSource = payload.svg_source;
  if (svgSource == null || typeof svgSource !== "object" || Array.isArray(svgSource)) {
    throw new Error("V4 workspace missing svg_source");
  }
  const fileHash = (svgSource as Record<string, unknown>).file_hash;
  if (typeof fileHash !== "string" || fileHash.length !== 64) {
    throw new Error("V4 workspace missing persisted file_hash");
  }
  return fileHash;
}

export async function fetchIntakeV4MaterialBreakdown(workspaceId: string) {
  const response = await fetch(
    `${BACKEND_URL}/api/v1/intake-v4/workspaces/${workspaceId}/material-breakdown`,
    { signal: AbortSignal.timeout(15_000) },
  );
  if (!response.ok) {
    throw new Error(`V4 material breakdown failed (${response.status})`);
  }
  return response.json();
}

export async function fetchIntakeV4PricingPreview(workspaceId: string) {
  const response = await fetch(
    `${BACKEND_URL}/api/v1/intake-v4/workspaces/${workspaceId}/pricing-input-preview`,
    { signal: AbortSignal.timeout(15_000) },
  );
  if (!response.ok) {
    throw new Error(`V4 pricing preview failed (${response.status})`);
  }
  return response.json();
}

export const INTAKE_V4_LINKAGE_CODE_PREFIX = "IV4-";

export function intakeV4LinkageCode(workspaceId: string): string {
  return `${INTAKE_V4_LINKAGE_CODE_PREFIX}${workspaceId}`;
}

export const INTAKE_V4_LINKAGE_JSON_KEY = "intake_v4_linkage_v1";

export interface IntakeV4DraftQuoteE2eResponse {
  quote_created: boolean;
  quote_id: number;
  quote_code: string;
  quote_status: string;
  source_module: string;
  source_workspace_id: string;
  quote_input_payload: Record<string, unknown>;
  snapshot_attached: boolean;
  requires_pricing_review: boolean;
  order_created: boolean;
  execution_plan_created: boolean;
  inventory_mutated: boolean;
}

export interface EntityQuoteRow {
  id: number;
  code: string;
  status: string;
  intake_code?: string | null;
  grand_total?: number | null;
  notes?: string | null;
  line_items?: string | null;
}

const DRAFT_QUOTE_CONFIRM_BODY = {
  confirm_create_draft_only: true,
  confirm_no_order: true,
  confirm_no_execution: true,
  confirm_no_inventory: true,
  decision_reason: "E2E Intake V4 commercial handoff",
} as const;

export async function createIntakeV4DraftQuoteForE2e(
  workspaceId: string,
  overrides: Partial<typeof DRAFT_QUOTE_CONFIRM_BODY & { client_analysis_hash: string }> = {},
): Promise<IntakeV4DraftQuoteE2eResponse> {
  const client_analysis_hash =
    overrides.client_analysis_hash ?? (await getPersistedAnalysisFileHash(workspaceId));
  const response = await fetch(
    `${BACKEND_URL}/api/v1/intake-v4/workspaces/${workspaceId}/create-draft-quote`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...DRAFT_QUOTE_CONFIRM_BODY, client_analysis_hash, ...overrides }),
      signal: AbortSignal.timeout(30_000),
    },
  );
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`V4 create-draft-quote failed (${response.status}): ${text.slice(0, 400)}`);
  }
  return JSON.parse(text) as IntakeV4DraftQuoteE2eResponse;
}

export async function createIntakeV4DraftQuoteRaw(
  workspaceId: string,
  body: Record<string, unknown> = { ...DRAFT_QUOTE_CONFIRM_BODY },
): Promise<{ status: number; body: Record<string, unknown> }> {
  const response = await fetch(
    `${BACKEND_URL}/api/v1/intake-v4/workspaces/${workspaceId}/create-draft-quote`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    },
  );
  const text = await response.text();
  let parsed: Record<string, unknown> = {};
  try {
    parsed = JSON.parse(text) as Record<string, unknown>;
  } catch {
    parsed = { raw: text };
  }
  return { status: response.status, body: parsed };
}

export async function fetchEntityQuoteByCode(code: string): Promise<EntityQuoteRow | null> {
  const query = encodeURIComponent(JSON.stringify({ code }));
  const response = await fetch(
    `${BACKEND_URL}/api/v1/entities/quotes?query=${query}&limit=1&skip=0`,
    { signal: AbortSignal.timeout(15_000) },
  );
  if (!response.ok) {
    throw new Error(`Entity quote query failed (${response.status})`);
  }
  const data = (await response.json()) as { items?: EntityQuoteRow[] };
  return data.items?.[0] ?? null;
}

export function parseIntakeV4LinkageFromQuoteNotes(
  notes: string | null | undefined,
): Record<string, unknown> | null {
  if (!notes) return null;
  try {
    const parsed = JSON.parse(notes) as Record<string, unknown>;
    const linkage = parsed[INTAKE_V4_LINKAGE_JSON_KEY];
    return linkage && typeof linkage === "object"
      ? (linkage as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

const FORBIDDEN_QUOTE_INPUT_PRICE_KEYS = [
  "unit_price",
  "grand_total",
  "total_before_vat",
  "subtotal",
  "owner_fallback",
] as const;

export function assertQuoteInputHasNoCommercialTotals(quoteInput: Record<string, unknown>) {
  for (const key of FORBIDDEN_QUOTE_INPUT_PRICE_KEYS) {
    if (quoteInput[key] !== undefined) {
      throw new Error(`quote_input_payload must not include commercial key: ${key}`);
    }
  }
  if (quoteInput.intake_source !== "intake_v4") {
    throw new Error(`quote_input_payload.intake_source expected intake_v4, got ${String(quoteInput.intake_source)}`);
  }
}

export function assertIntakeV4CommercialLinkage(
  linkage: Record<string, unknown>,
  workspaceId: string,
  quoteInput: Record<string, unknown>,
) {
  if (linkage.source_module !== "intake_v4") {
    throw new Error(`linkage.source_module expected intake_v4, got ${String(linkage.source_module)}`);
  }
  if (linkage.source_workspace_id !== workspaceId) {
    throw new Error("linkage.source_workspace_id mismatch");
  }
  if (linkage.requires_pricing_review !== true) {
    throw new Error("linkage.requires_pricing_review must be true");
  }
  if (!linkage.quote_input_payload || typeof linkage.quote_input_payload !== "object") {
    throw new Error("linkage.quote_input_payload missing");
  }
  if (!linkage.snapshot || typeof linkage.snapshot !== "object") {
    throw new Error("linkage.snapshot missing");
  }

  const snapshot = linkage.snapshot as Record<string, unknown>;
  if (!snapshot.quote_input_payload) {
    throw new Error("snapshot.quote_input_payload missing");
  }
  if (!snapshot.workspace_payload_snapshot) {
    throw new Error("snapshot.workspace_payload_snapshot missing");
  }
  if (!snapshot.operation_flags) {
    throw new Error("snapshot.operation_flags missing");
  }
  if (!Array.isArray(snapshot.integrity_rules) || snapshot.integrity_rules.length === 0) {
    throw new Error("snapshot.integrity_rules missing or empty");
  }

  assertQuoteInputHasNoCommercialTotals(snapshot.quote_input_payload as Record<string, unknown>);

  const perimeter =
    quoteInput.letter_perimeter_m ?? quoteInput.total_letter_perimeter_ml ?? quoteInput.letter_count;
  if (!perimeter) {
    throw new Error("quote_input geometry missing perimeter/count");
  }
  const snapshotQuoteInput = snapshot.quote_input_payload as Record<string, unknown>;
  if (
    !snapshotQuoteInput.letter_perimeter_m &&
    !snapshotQuoteInput.total_letter_perimeter_ml &&
    !snapshotQuoteInput.letter_count
  ) {
    throw new Error("snapshot quote_input geometry missing");
  }
}
