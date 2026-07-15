/**
 * Execution owner-decision operational resolution (W6-T04).
 * POST /api/v1/execution/orders/{order_id}/owner-decisions/{code}/resolve
 */
import { getAPIBaseURL } from "@/lib/config";

export type OwnerDecisionOperationalStatus =
  | "unresolved"
  | "acknowledged"
  | "resolved"
  | "waived";

export type ProductionReleaseStatus =
  | "RELEASE_ALLOWED"
  | "RELEASE_BLOCKED_OWNER_DECISIONS"
  | "RELEASE_BLOCKED_MISSING_RUNTIME_RESOLUTION"
  | "RELEASE_BLOCKED_POLICY_ERROR"
  | "NOT_PROVEN";

export interface OwnerDecisionResolutionRequest {
  status: "acknowledged" | "resolved";
  note: string;
}

export interface OwnerDecisionResolutionResult {
  order_id: number;
  code: string;
  operational_status: OwnerDecisionOperationalStatus;
  release_status: ProductionReleaseStatus;
  idempotent: boolean;
  audit_event_id: string | null;
}

export class OwnerDecisionResolutionError extends Error {
  readonly httpStatus: number;
  readonly errorCode: string;
  readonly detail: Record<string, unknown> | string | null;

  constructor(
    httpStatus: number,
    errorCode: string,
    message: string,
    detail: Record<string, unknown> | string | null,
  ) {
    super(message);
    this.name = "OwnerDecisionResolutionError";
    this.httpStatus = httpStatus;
    this.errorCode = errorCode;
    this.detail = detail;
  }
}

function parseResolutionError(httpStatus: number, body: unknown): OwnerDecisionResolutionError {
  const envelope =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail: unknown }).detail
      : body;

  let errorCode = "unknown";
  let message = `Rezolvare esuata (${httpStatus})`;

  if (typeof envelope === "string") {
    message = envelope;
  } else if (envelope && typeof envelope === "object") {
    const rec = envelope as Record<string, unknown>;
    if (typeof rec.error === "string") errorCode = rec.error;
    if (typeof rec.message === "string") message = rec.message;
  }

  return new OwnerDecisionResolutionError(
    httpStatus,
    errorCode,
    message,
    envelope && typeof envelope === "object" ? (envelope as Record<string, unknown>) : null,
  );
}

export function resolutionErrorHeadline(error: OwnerDecisionResolutionError): string {
  if (error.httpStatus === 403 || error.errorCode === "owner_decision_resolve_forbidden") {
    return "Nu aveti permisiunea de a rezolva aceasta decizie.";
  }
  if (error.errorCode === "owner_decision_note_required") {
    return "Nota de rezolvare este obligatorie (minim 3 caractere).";
  }
  if (error.errorCode === "owner_decision_nonblocking") {
    return "Decizia este doar informativa — nu necesita rezolvare operationala.";
  }
  if (error.errorCode === "owner_decision_not_in_frozen_snapshot") {
    return "Decizia nu exista in snapshot-ul inghetat.";
  }
  if (error.httpStatus === 409) {
    return "Tranzitie invalida sau stare conflictuala.";
  }
  return error.message;
}

/** Backend requires note min length 3 — do not impose stricter frontend-only rules. */
export const RESOLUTION_NOTE_MIN_LENGTH = 3;

const executionBase = () => `${getAPIBaseURL()}/api/v1/execution`;

export async function resolveOwnerDecision(
  orderId: number,
  code: string,
  body: OwnerDecisionResolutionRequest,
): Promise<OwnerDecisionResolutionResult> {
  const res = await fetch(
    `${executionBase()}/orders/${orderId}/owner-decisions/${encodeURIComponent(code)}/resolve`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw parseResolutionError(res.status, errBody);
  }

  return res.json() as Promise<OwnerDecisionResolutionResult>;
}
