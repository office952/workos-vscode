const INVENTORY_PATH = "/inventory";


const ALLOWED_KEYS = new Set([
  "tab",
  "sq_status",
  "sq_issue_code",
  "sq_would_block",
  "sq_material_id",
  "sq_selected_issue_code",
  "trail_material_id",
  "trail_issue_code",
  "trail_changed_by",
  "trail_operation_status",
  "trail_date_from",
  "trail_date_to",
  "trail_limit",
  "trail_offset",
]);

type SheetQualityStatus = "all" | "valid" | "invalid" | "not_applicable";
type SheetQualityIssueCode =
  | "missing_required_field"
  | "missing_configuration"
  | "invalid_unit"
  | "invalid_dimensions"
  | "partial_payload"
  | "unexpected_shape";
type TrailOperationStatus = "applied" | "failed";

export type SheetQualityUrlParams = {
  tab?: "sheet-quality";
  sq_status?: SheetQualityStatus;
  sq_issue_code?: SheetQualityIssueCode;
  sq_would_block?: boolean;
  sq_material_id?: string;
  sq_selected_issue_code?: SheetQualityIssueCode;
  trail_material_id?: string;
  trail_issue_code?: SheetQualityIssueCode;
  trail_changed_by?: string;
  trail_operation_status?: TrailOperationStatus;
  trail_date_from?: string;
  trail_date_to?: string;
  trail_limit?: number;
  trail_offset?: number;
};

export function buildSheetQualityUrl(params: SheetQualityUrlParams = {}): string {
  const search = new URLSearchParams();
  search.set("tab", "sheet-quality");

  for (const [key, rawValue] of Object.entries(params)) {
    if (key === "tab") continue;
    if (!ALLOWED_KEYS.has(key)) continue;
    if (rawValue === undefined || rawValue === null || rawValue === "") continue;

    if (typeof rawValue === "boolean") {
      search.set(key, String(rawValue));
      continue;
    }

    if (typeof rawValue === "number") {
      if (!Number.isFinite(rawValue)) continue;
      search.set(key, String(Math.floor(rawValue)));
      continue;
    }

    search.set(key, rawValue);
  }

  return `${INVENTORY_PATH}?${search.toString()}`;
}

export function buildSheetQualityMaterialUrl(
  materialId: string,
  issueCode?: SheetQualityIssueCode
): string {
  return buildSheetQualityUrl({
    sq_status: "invalid",
    sq_material_id: materialId,
    sq_selected_issue_code: issueCode,
    trail_material_id: materialId,
  });
}

export function buildSheetQualityInvalidSummaryUrl(issueCode?: SheetQualityIssueCode): string {
  return buildSheetQualityUrl({
    sq_status: "invalid",
    sq_issue_code: issueCode,
    sq_would_block: true,
  });
}

export function buildSheetQualityAuditTrailUrl(
  materialId: string,
  issueCode?: SheetQualityIssueCode
): string {
  return buildSheetQualityUrl({
    trail_material_id: materialId,
    trail_issue_code: issueCode,
    trail_offset: 0,
  });
}