import { getAPIBaseURL } from "@/lib/config";

export type InventorySheetAuditStatus = "all" | "valid" | "not_applicable" | "invalid";
export type InventorySheetAuditItemStatus = "valid" | "not_applicable" | "invalid";
export type InventorySheetAuditIssueCode =
  | "missing_required_field"
  | "missing_configuration"
  | "invalid_unit"
  | "invalid_dimensions"
  | "partial_payload"
  | "unexpected_shape";

export type InventorySheetRemediationCategory =
  | "manual_only"
  | "assisted_manual"
  | "future_bulk_safe"
  | "not_repairable_without_domain_decision";

export type InventorySheetRemediationOperationStatus = "applied" | "failed";

export type InventorySheetFormatType = "none" | "sheet" | "roll" | "linear" | "piece" | "unknown";
export type InventorySheetUnit = "mm" | "cm" | "m" | "unknown";
export type InventorySheetFormatSource = "manual" | "supplier" | "imported" | "unknown";

export interface InventorySheetQualityByIssueCode {
  missing_required_field: number;
  missing_configuration: number;
  invalid_unit: number;
  invalid_dimensions: number;
  partial_payload: number;
  unexpected_shape: number;
}

export interface InventorySheetQualityAuditSummary {
  total_records_checked: number;
  valid_count: number;
  not_applicable_count: number;
  invalid_count: number;
  would_block_intake_assist_count: number;
  by_issue_code: InventorySheetQualityByIssueCode;
}

export interface InventorySheetQualityAuditFilters {
  status: InventorySheetAuditStatus;
  issue_code: InventorySheetAuditIssueCode | null;
  would_block_intake_assist: boolean | null;
  limit: number;
  offset: number;
}

export interface InventorySheetQualityAuditItem {
  material_id: string;
  material_name: string | null;
  material_code: string | null;
  category: string | null;
  status: InventorySheetAuditItemStatus;
  issue_code: InventorySheetAuditIssueCode | null;
  message: string;
  recommended_action: string | null;
  would_block_intake_assist: boolean;
}

export interface InventorySheetQualityAuditResponse {
  source: "backend";
  report_type: "inventory_sheet_quality_audit";
  generated_at: string;
  summary: InventorySheetQualityAuditSummary;
  filters: InventorySheetQualityAuditFilters;
  items: InventorySheetQualityAuditItem[];
  warnings: string[];
}

export interface InventorySheetRemediationPlanSummary {
  total_items: number;
  manual_only_count: number;
  assisted_manual_count: number;
  future_bulk_safe_count: number;
  not_repairable_without_domain_decision_count: number;
}

export interface InventorySheetRemediationPlanItem {
  material_id: string;
  material_name: string | null;
  issue_code: InventorySheetAuditIssueCode;
  remediation_category: InventorySheetRemediationCategory;
  allowed_actions: string[];
  forbidden_actions: string[];
  requires_operator_input: boolean;
  requires_admin_confirmation: boolean;
  recommended_next_step: string;
  future_automation_eligible: boolean;
  would_block_intake_assist: boolean;
}

export interface InventorySheetRemediationPlanResponse {
  source: "backend";
  report_type: "inventory_sheet_remediation_plan";
  generated_at: string;
  summary: InventorySheetRemediationPlanSummary;
  items: InventorySheetRemediationPlanItem[];
  warnings: string[];
}

export interface InventorySheetRemediationProposedValues {
  sheet_format_type?: InventorySheetFormatType;
  sheet_width?: number;
  sheet_height?: number;
  sheet_unit?: InventorySheetUnit;
  sheet_thickness?: number;
  sheet_thickness_unit?: InventorySheetUnit;
  usable_width?: number;
  usable_height?: number;
  format_source?: InventorySheetFormatSource;
  format_verified?: boolean;
  format_notes?: string;
}

export interface InventorySheetRemediationRequest {
  issue_code: InventorySheetAuditIssueCode;
  proposed_values: InventorySheetRemediationProposedValues;
  reason: string;
  confirm: true;
}

export interface InventorySheetRemediationExecutionSnapshot {
  sheet_format: Record<string, unknown>;
  audit_status: InventorySheetAuditItemStatus;
  issue_code: InventorySheetAuditIssueCode | null;
}

export interface InventorySheetRemediationResponse {
  source: "backend";
  operation: "inventory_sheet_remediation";
  status: "applied";
  material_id: string;
  issue_code: InventorySheetAuditIssueCode;
  before: InventorySheetRemediationExecutionSnapshot;
  after: InventorySheetRemediationExecutionSnapshot;
  audit_event_id: string;
  warnings: string[];
}

export interface InventorySheetRemediationAuditTrailByIssueCode {
  missing_required_field: number;
  missing_configuration: number;
  invalid_unit: number;
  invalid_dimensions: number;
  partial_payload: number;
  unexpected_shape: number;
}

export interface InventorySheetRemediationAuditTrailByStatus {
  applied: number;
  failed: number;
}

export interface InventorySheetRemediationAuditTrailSummary {
  total_events: number;
  returned_events: number;
  by_issue_code: InventorySheetRemediationAuditTrailByIssueCode;
  by_status: InventorySheetRemediationAuditTrailByStatus;
}

export interface InventorySheetRemediationAuditTrailFilters {
  material_id: string | null;
  issue_code: InventorySheetAuditIssueCode | null;
  changed_by: string | null;
  date_from: string | null;
  date_to: string | null;
  operation_status: InventorySheetRemediationOperationStatus | null;
  limit: number;
  offset: number;
}

export interface InventorySheetRemediationAuditEvent {
  audit_event_id: string;
  material_id: string;
  issue_code: InventorySheetAuditIssueCode;
  reason: string;
  changed_by: string | null;
  changed_at: string;
  source: string;
  operation_status: InventorySheetRemediationOperationStatus;
  old_values: Record<string, unknown>;
  new_values: Record<string, unknown>;
  validation_result_before: Record<string, unknown>;
  validation_result_after: Record<string, unknown>;
}

export interface InventorySheetRemediationAuditTrailResponse {
  source: "backend";
  report_type: "inventory_sheet_remediation_audit_trail";
  generated_at: string;
  summary: InventorySheetRemediationAuditTrailSummary;
  filters: InventorySheetRemediationAuditTrailFilters;
  events: InventorySheetRemediationAuditEvent[];
  warnings: string[];
}

export interface InventorySheetQualityAuditQuery {
  status?: InventorySheetAuditStatus;
  issue_code?: InventorySheetAuditIssueCode;
  would_block_intake_assist?: boolean;
  limit?: number;
  offset?: number;
}

export interface InventorySheetRemediationAuditTrailQuery {
  material_id?: string;
  issue_code?: InventorySheetAuditIssueCode;
  changed_by?: string;
  date_from?: string;
  date_to?: string;
  operation_status?: InventorySheetRemediationOperationStatus;
  limit?: number;
  offset?: number;
}

export type InventorySheetExportFormat = "csv" | "json";

export interface InventorySheetQualityAuditExportQuery extends InventorySheetQualityAuditQuery {
  format: InventorySheetExportFormat;
}

export interface InventorySheetRemediationAuditTrailExportQuery extends InventorySheetRemediationAuditTrailQuery {
  format: InventorySheetExportFormat;
}

export interface BackendErrorDetail {
  error?: string;
  code?: string;
  field?: string | null;
  message?: string;
}

export class InventorySheetQualityHttpError extends Error {
  status: number;
  detail: BackendErrorDetail | unknown;

  constructor(status: number, message: string, detail: BackendErrorDetail | unknown) {
    super(message);
    this.name = "InventorySheetQualityHttpError";
    this.status = status;
    this.detail = detail;
  }
}

function apiBase(): string {
  return `${getAPIBaseURL()}/api/v1/admin/inventory`;
}

function buildQuery<T extends object>(params: T): string {
  const qs = new URLSearchParams();
  Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
    if (
      value === undefined ||
      value === null ||
      (typeof value !== "string" && typeof value !== "number" && typeof value !== "boolean")
    ) {
      return;
    }
    qs.set(key, String(value));
  });
  const encoded = qs.toString();
  return encoded ? `?${encoded}` : "";
}

const FORBIDDEN_EXPORT_KEYS = new Set([
  "reason",
  "proposed_values",
  "proposedValues",
  "confirm",
  "confirmed",
  "token",
  "secret",
  "password",
  "credential",
  "api_key",
  "apiKey",
  "authorization",
]);

const QUALITY_EXPORT_ALLOWED_KEYS = new Set([
  "format",
  "status",
  "issue_code",
  "would_block_intake_assist",
  "limit",
  "offset",
]);

const TRAIL_EXPORT_ALLOWED_KEYS = new Set([
  "format",
  "material_id",
  "issue_code",
  "changed_by",
  "date_from",
  "date_to",
  "operation_status",
  "limit",
  "offset",
]);

function sanitizeExportParams(
  rawParams: Record<string, unknown>,
  allowedKeys: Set<string>
): Record<string, string | number | boolean> {
  const sanitized: Record<string, string | number | boolean> = {};
  Object.entries(rawParams).forEach(([key, value]) => {
    if (!allowedKeys.has(key)) return;
    if (FORBIDDEN_EXPORT_KEYS.has(key)) return;
    if (
      value === undefined ||
      value === null ||
      (typeof value !== "string" && typeof value !== "number" && typeof value !== "boolean")
    ) {
      return;
    }
    if (typeof value === "string" && value.trim() === "") return;
    sanitized[key] = value;
  });
  return sanitized;
}

function parseFilenameFromContentDisposition(contentDisposition: string | null): string | null {
  if (!contentDisposition) return null;
  const match = /filename="?([^";]+)"?/i.exec(contentDisposition);
  return match?.[1] || null;
}

async function parseErrorBody(response: Response): Promise<{ message: string; detail: BackendErrorDetail | unknown }> {
  try {
    const body = (await response.json()) as { detail?: BackendErrorDetail | BackendErrorDetail[] | string; message?: string };
    if (typeof body?.detail === "string") {
      return { message: body.detail, detail: body.detail };
    }
    if (Array.isArray(body?.detail)) {
      const firstMessage = typeof body.detail[0] === "object" && body.detail[0] && "msg" in body.detail[0]
        ? String((body.detail[0] as { msg?: string }).msg ?? `HTTP ${response.status}`)
        : `HTTP ${response.status}`;
      return { message: firstMessage, detail: body.detail };
    }
    if (body?.detail && typeof body.detail === "object") {
      const detailObj = body.detail as BackendErrorDetail;
      return { message: detailObj.message || detailObj.code || `HTTP ${response.status}`, detail: detailObj };
    }
    if (typeof body?.message === "string") {
      return { message: body.message, detail: body };
    }
  } catch {
    // ignore parse errors
  }
  return { message: `HTTP ${response.status}`, detail: { message: `HTTP ${response.status}` } };
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const parsed = await parseErrorBody(response);
    throw new InventorySheetQualityHttpError(response.status, parsed.message, parsed.detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function getInventorySheetQualityAudit(
  params: InventorySheetQualityAuditQuery = {}
): Promise<InventorySheetQualityAuditResponse> {
  return requestJson<InventorySheetQualityAuditResponse>(
    `/sheet-quality-audit${buildQuery(params)}`,
    { method: "GET" }
  );
}

export function getInventorySheetRemediationPlan(): Promise<InventorySheetRemediationPlanResponse> {
  return requestJson<InventorySheetRemediationPlanResponse>(
    "/sheet-quality-remediation-plan",
    { method: "GET" }
  );
}

export function remediateInventorySheetMaterial(
  materialId: string,
  payload: InventorySheetRemediationRequest
): Promise<InventorySheetRemediationResponse> {
  return requestJson<InventorySheetRemediationResponse>(
    `/materials/${encodeURIComponent(materialId)}/sheet-format-remediation`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export function getInventorySheetRemediationAuditTrail(
  params: InventorySheetRemediationAuditTrailQuery = {}
): Promise<InventorySheetRemediationAuditTrailResponse> {
  return requestJson<InventorySheetRemediationAuditTrailResponse>(
    `/sheet-remediation-audit-trail${buildQuery(params)}`,
    { method: "GET" }
  );
}

export function buildInventorySheetQualityAuditExportUrl(
  params: InventorySheetQualityAuditExportQuery
): string {
  const sanitized = sanitizeExportParams(
    params as unknown as Record<string, unknown>,
    QUALITY_EXPORT_ALLOWED_KEYS
  );
  return `${apiBase()}/sheet-quality-audit/export${buildQuery(sanitized)}`;
}

export function buildInventorySheetRemediationAuditTrailExportUrl(
  params: InventorySheetRemediationAuditTrailExportQuery
): string {
  const sanitized = sanitizeExportParams(
    params as unknown as Record<string, unknown>,
    TRAIL_EXPORT_ALLOWED_KEYS
  );
  return `${apiBase()}/sheet-remediation-audit-trail/export${buildQuery(sanitized)}`;
}

export async function downloadInventorySheetExport(url: string, filename?: string): Promise<void> {
  const response = await fetch(url, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    const parsed = await parseErrorBody(response);
    throw new InventorySheetQualityHttpError(response.status, parsed.message, parsed.detail);
  }

  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  const derivedFilename =
    parseFilenameFromContentDisposition(response.headers.get("content-disposition")) ||
    filename ||
    "inventory_sheet_export.dat";

  link.href = objectUrl;
  link.download = derivedFilename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(objectUrl);
}
