/**
 * BUILD 18 — ExecutionReality Quality API Client.
 *
 * Endpoints:
 *   POST /api/v1/execution-reality/{reality_id}/invalidate
 *   POST /api/v1/execution-reality/{reality_id}/restore-valid
 *   GET  /api/v1/execution-reality/{reality_id}/quality-status
 */

import { getAPIBaseURL } from "@/lib/config";

export interface QualityStatus {
  reality_id: number;
  order_id: number;
  order_code: string;
  is_invalid: boolean;
  invalidated_at: string | null;
  invalidated_by: string | null;
  invalid_reason: string | null;
  stock_reconciliation_required: boolean;
  stock_deducted: boolean;
  restored_at: string | null;
  restored_by: string | null;
  restored_reason: string | null;
  warnings: string[];
}

export interface InvalidateRequest {
  reason: string;
}

export interface RestoreRequest {
  reason: string;
}

export class ExecutionRealityQualityHttpError extends Error {
  status: number;
  code: string | null;
  detail: string | null;

  constructor(
    status: number,
    message: string,
    code: string | null,
    detail: string | null,
  ) {
    super(message);
    this.name = "ExecutionRealityQualityHttpError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

async function parseQualityError(res: Response): Promise<ExecutionRealityQualityHttpError> {
  const body = await res.json().catch(() => ({}));
  const detailEnvelope =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail?: unknown }).detail
      : body;
  const detailObj =
    detailEnvelope && typeof detailEnvelope === "object"
      ? (detailEnvelope as Record<string, unknown>)
      : null;

  const code =
    detailObj && typeof detailObj.error === "string"
      ? detailObj.error
      : typeof detailEnvelope === "string"
        ? detailEnvelope
        : null;
  const detail =
    detailObj && typeof detailObj.detail === "string"
      ? detailObj.detail
      : detailObj && typeof detailObj.message === "string"
        ? detailObj.message
        : null;

  const fallback = `HTTP ${res.status}`;
  const message = detail || code || fallback;
  return new ExecutionRealityQualityHttpError(res.status, message, code, detail);
}

export async function getQualityStatus(realityId: number): Promise<QualityStatus> {
  const base = getAPIBaseURL();
  const res = await fetch(
    `${base}/api/v1/execution-reality/${realityId}/quality-status`,
    { credentials: "include" }
  );
  if (!res.ok) {
    throw await parseQualityError(res);
  }
  return res.json();
}

export async function invalidateReality(
  realityId: number,
  req: InvalidateRequest
): Promise<QualityStatus> {
  const base = getAPIBaseURL();
  const res = await fetch(
    `${base}/api/v1/execution-reality/${realityId}/invalidate`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(req),
    }
  );
  if (!res.ok) {
    throw await parseQualityError(res);
  }
  return res.json();
}

export async function restoreReality(
  realityId: number,
  req: RestoreRequest
): Promise<QualityStatus> {
  const base = getAPIBaseURL();
  const res = await fetch(
    `${base}/api/v1/execution-reality/${realityId}/restore-valid`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(req),
    }
  );
  if (!res.ok) {
    throw await parseQualityError(res);
  }
  return res.json();
}