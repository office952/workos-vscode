import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  ExternalLink,
  Loader2,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import {
  buildInventorySheetQualityAuditExportUrl,
  buildInventorySheetRemediationAuditTrailExportUrl,
  downloadInventorySheetExport,
  getInventorySheetQualityAudit,
  getInventorySheetRemediationAuditTrail,
  getInventorySheetRemediationPlan,
  remediateInventorySheetMaterial,
  type BackendErrorDetail,
  type InventorySheetAuditIssueCode,
  type InventorySheetAuditStatus,
  type InventorySheetQualityAuditItem,
  type InventorySheetQualityAuditResponse,
  type InventorySheetRemediationAuditEvent,
  type InventorySheetRemediationAuditTrailResponse,
  type InventorySheetRemediationOperationStatus,
  type InventorySheetRemediationPlanItem,
  type InventorySheetRemediationPlanResponse,
  type InventorySheetRemediationRequest,
  type InventorySheetRemediationResponse,
  InventorySheetQualityHttpError,
} from "@/api/inventorySheetQuality";
import { buildSheetQualityUrl } from "@/utils/inventorySheetQualityLinks";

const ISSUE_CODES: InventorySheetAuditIssueCode[] = [
  "missing_required_field",
  "missing_configuration",
  "invalid_unit",
  "invalid_dimensions",
  "partial_payload",
  "unexpected_shape",
];

const OPERATION_STATUS_OPTIONS: InventorySheetRemediationOperationStatus[] = [
  "applied",
  "failed",
];

const AUDIT_STATUS_OPTIONS: InventorySheetAuditStatus[] = [
  "all",
  "valid",
  "not_applicable",
  "invalid",
];

const SUPPORTED_EXECUTION_ISSUES: InventorySheetAuditIssueCode[] = [
  "missing_configuration",
  "invalid_dimensions",
  "partial_payload",
];

const TRAIL_LIMIT_OPTIONS = [10, 25, 50, 100] as const;
const DEFAULT_TRAIL_LIMIT = 25;

type FormValues = {
  sheet_format_type: string;
  sheet_width: string;
  sheet_height: string;
  sheet_unit: string;
  sheet_thickness: string;
  sheet_thickness_unit: string;
  usable_width: string;
  usable_height: string;
  format_source: string;
  format_verified: boolean;
  format_notes: string;
};

const EMPTY_FORM: FormValues = {
  sheet_format_type: "",
  sheet_width: "",
  sheet_height: "",
  sheet_unit: "",
  sheet_thickness: "",
  sheet_thickness_unit: "",
  usable_width: "",
  usable_height: "",
  format_source: "",
  format_verified: false,
  format_notes: "",
};

type UrlState = {
  sqStatus: InventorySheetAuditStatus;
  sqIssueCode: InventorySheetAuditIssueCode | undefined;
  sqWouldBlock: boolean | undefined;
  sqMaterialId: string | undefined;
  sqSelectedIssueCode: InventorySheetAuditIssueCode | undefined;
  trailMaterialId: string | undefined;
  trailIssueCode: InventorySheetAuditIssueCode | undefined;
  trailChangedBy: string | undefined;
  trailOperationStatus: InventorySheetRemediationOperationStatus | undefined;
  trailDateFrom: string | undefined;
  trailDateTo: string | undefined;
  trailLimit: number;
  trailOffset: number;
  invalidFiltersIgnored: boolean;
};

type ActiveFilterChip = {
  key: string;
  label: string;
  value: string;
};

function isIssueCode(value: string | null): value is InventorySheetAuditIssueCode {
  return !!value && ISSUE_CODES.includes(value as InventorySheetAuditIssueCode);
}

function isAuditStatus(value: string | null): value is InventorySheetAuditStatus {
  return !!value && AUDIT_STATUS_OPTIONS.includes(value as InventorySheetAuditStatus);
}

function isOperationStatus(
  value: string | null
): value is InventorySheetRemediationOperationStatus {
  return !!value && OPERATION_STATUS_OPTIONS.includes(value as InventorySheetRemediationOperationStatus);
}

function parseBoolean(value: string | null): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

function parseNumber(value: string | null, fallback: number): { value: number; valid: boolean } {
  if (!value) return { value: fallback, valid: true };
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return { value: fallback, valid: false };
  }
  return { value: Math.floor(parsed), valid: true };
}

function parseLimit(value: string | null): { value: number; valid: boolean } {
  if (!value) return { value: DEFAULT_TRAIL_LIMIT, valid: true };
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || !TRAIL_LIMIT_OPTIONS.includes(parsed as (typeof TRAIL_LIMIT_OPTIONS)[number])) {
    return { value: DEFAULT_TRAIL_LIMIT, valid: false };
  }
  return { value: parsed, valid: true };
}

function readSheetQualityParams(searchParams: URLSearchParams): UrlState {
  let invalidFiltersIgnored = false;

  const sqStatusRaw = searchParams.get("sq_status");
  const sqStatus = isAuditStatus(sqStatusRaw) ? sqStatusRaw : "invalid";
  if (sqStatusRaw && !isAuditStatus(sqStatusRaw)) invalidFiltersIgnored = true;

  const sqIssueCodeRaw = searchParams.get("sq_issue_code");
  const sqIssueCode = isIssueCode(sqIssueCodeRaw) ? sqIssueCodeRaw : undefined;
  if (sqIssueCodeRaw && !sqIssueCode) invalidFiltersIgnored = true;

  const sqWouldBlockRaw = searchParams.get("sq_would_block");
  const sqWouldBlock = parseBoolean(sqWouldBlockRaw);
  if (sqWouldBlockRaw && sqWouldBlock === undefined) invalidFiltersIgnored = true;

  const sqMaterialId = searchParams.get("sq_material_id") || undefined;
  const sqSelectedIssueCodeRaw = searchParams.get("sq_selected_issue_code");
  const sqSelectedIssueCode = isIssueCode(sqSelectedIssueCodeRaw)
    ? sqSelectedIssueCodeRaw
    : undefined;
  if (sqSelectedIssueCodeRaw && !sqSelectedIssueCode) invalidFiltersIgnored = true;

  const trailIssueCodeRaw = searchParams.get("trail_issue_code");
  const trailIssueCode = isIssueCode(trailIssueCodeRaw) ? trailIssueCodeRaw : undefined;
  if (trailIssueCodeRaw && !trailIssueCode) invalidFiltersIgnored = true;

  const trailOperationStatusRaw = searchParams.get("trail_operation_status");
  const trailOperationStatus = isOperationStatus(trailOperationStatusRaw)
    ? trailOperationStatusRaw
    : undefined;
  if (trailOperationStatusRaw && !trailOperationStatus) invalidFiltersIgnored = true;

  const parsedLimit = parseLimit(searchParams.get("trail_limit"));
  const parsedOffset = parseNumber(searchParams.get("trail_offset"), 0);
  if (!parsedLimit.valid || !parsedOffset.valid) invalidFiltersIgnored = true;

  return {
    sqStatus,
    sqIssueCode,
    sqWouldBlock,
    sqMaterialId,
    sqSelectedIssueCode,
    trailMaterialId: searchParams.get("trail_material_id") || undefined,
    trailIssueCode,
    trailChangedBy: searchParams.get("trail_changed_by") || undefined,
    trailOperationStatus,
    trailDateFrom: searchParams.get("trail_date_from") || undefined,
    trailDateTo: searchParams.get("trail_date_to") || undefined,
    trailLimit: parsedLimit.value,
    trailOffset: parsedOffset.value,
    invalidFiltersIgnored,
  };
}

function mapBackendError(error: unknown): string {
  if (error instanceof InventorySheetQualityHttpError) {
    const detail = error.detail as BackendErrorDetail;
    const code = detail?.code;

    if (error.status === 401 || error.status === 403) {
      return "Admin authentication is required for this action.";
    }
    if (code === "confirm_required") return "Confirm must be checked before submit.";
    if (code === "reason_required") return "Reason is required.";
    if (code === "unsupported_issue_code") {
      return "This issue cannot be remediated via this endpoint.";
    }
    if (code === "issue_mismatch") {
      return "Selected issue does not match current backend audit state.";
    }
    if (code === "validation_failed") {
      return "Backend validation failed. Please correct proposed values.";
    }
    if (code === "audit_log_unavailable") {
      return "Audit log unavailable. No changes were applied.";
    }
    if (code === "material_not_found") return "Material not found.";
    if (code === "invalid_date_range") return "Invalid date range.";
    if (detail?.message) return detail.message;
    return error.message;
  }

  if (error instanceof Error) return error.message;
  return "Unexpected error.";
}

function asISODateFromInput(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.valueOf())) return undefined;
  return parsed.toISOString();
}

function toDateInputValue(isoValue: string | undefined): string {
  if (!isoValue) return "";
  const parsed = new Date(isoValue);
  if (Number.isNaN(parsed.valueOf())) return "";
  const local = new Date(parsed.getTime() - parsed.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function toReadableDate(isoValue: string): string {
  const parsed = new Date(isoValue);
  if (Number.isNaN(parsed.valueOf())) return isoValue;
  return parsed.toLocaleString();
}

function buildProposedValues(form: FormValues): InventorySheetRemediationRequest["proposed_values"] {
  const payload: InventorySheetRemediationRequest["proposed_values"] = {};

  if (form.sheet_format_type.trim()) payload.sheet_format_type = form.sheet_format_type.trim() as InventorySheetRemediationRequest["proposed_values"]["sheet_format_type"];
  if (form.sheet_unit.trim()) payload.sheet_unit = form.sheet_unit.trim() as InventorySheetRemediationRequest["proposed_values"]["sheet_unit"];
  if (form.sheet_thickness_unit.trim()) payload.sheet_thickness_unit = form.sheet_thickness_unit.trim() as InventorySheetRemediationRequest["proposed_values"]["sheet_thickness_unit"];
  if (form.format_source.trim()) payload.format_source = form.format_source.trim() as InventorySheetRemediationRequest["proposed_values"]["format_source"];
  if (form.format_notes.trim()) payload.format_notes = form.format_notes.trim();

  if (form.sheet_width.trim()) payload.sheet_width = Number(form.sheet_width);
  if (form.sheet_height.trim()) payload.sheet_height = Number(form.sheet_height);
  if (form.sheet_thickness.trim()) payload.sheet_thickness = Number(form.sheet_thickness);
  if (form.usable_width.trim()) payload.usable_width = Number(form.usable_width);
  if (form.usable_height.trim()) payload.usable_height = Number(form.usable_height);
  if (form.format_verified) payload.format_verified = true;

  Object.entries(payload).forEach(([key, value]) => {
    if (typeof value === "number" && Number.isNaN(value)) {
      delete payload[key as keyof typeof payload];
    }
  });

  return payload;
}

function JsonBlock({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="text-[11px] text-slate-300 bg-[#0B1220] border border-[#1E293B] rounded p-2 overflow-x-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export default function InventorySheetQualityPanel() {
  const [searchParams, setSearchParams] = useSearchParams();

  const urlState = useMemo(() => readSheetQualityParams(searchParams), [searchParams]);

  const [auditResponse, setAuditResponse] = useState<InventorySheetQualityAuditResponse | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  const [planResponse, setPlanResponse] = useState<InventorySheetRemediationPlanResponse | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);

  const [trailResponse, setTrailResponse] = useState<InventorySheetRemediationAuditTrailResponse | null>(null);
  const [trailLoading, setTrailLoading] = useState(false);
  const [trailError, setTrailError] = useState<string | null>(null);

  const [expandedAuditEventId, setExpandedAuditEventId] = useState<string | null>(null);

  const [formValues, setFormValues] = useState<FormValues>(EMPTY_FORM);
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState(false);

  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitResult, setSubmitResult] = useState<InventorySheetRemediationResponse | null>(null);
  const [exportLoading, setExportLoading] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const [uiMessage, setUiMessage] = useState<string | null>(null);

  const [trailMaterialDraft, setTrailMaterialDraft] = useState(urlState.trailMaterialId || "");
  const [trailIssueDraft, setTrailIssueDraft] = useState<InventorySheetAuditIssueCode | "">(
    urlState.trailIssueCode || ""
  );
  const [trailChangedByDraft, setTrailChangedByDraft] = useState(urlState.trailChangedBy || "");
  const [trailOpStatusDraft, setTrailOpStatusDraft] = useState<InventorySheetRemediationOperationStatus | "">(
    urlState.trailOperationStatus || ""
  );
  const [trailDateFromDraft, setTrailDateFromDraft] = useState(toDateInputValue(urlState.trailDateFrom));
  const [trailDateToDraft, setTrailDateToDraft] = useState(toDateInputValue(urlState.trailDateTo));

  useEffect(() => {
    setTrailMaterialDraft(urlState.trailMaterialId || "");
    setTrailIssueDraft(urlState.trailIssueCode || "");
    setTrailChangedByDraft(urlState.trailChangedBy || "");
    setTrailOpStatusDraft(urlState.trailOperationStatus || "");
    setTrailDateFromDraft(toDateInputValue(urlState.trailDateFrom));
    setTrailDateToDraft(toDateInputValue(urlState.trailDateTo));
  }, [
    urlState.trailChangedBy,
    urlState.trailDateFrom,
    urlState.trailDateTo,
    urlState.trailIssueCode,
    urlState.trailMaterialId,
    urlState.trailOperationStatus,
  ]);

  const updateQuery = useCallback(
    (updates: Record<string, string | undefined>) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        Object.entries(updates).forEach(([key, value]) => {
          if (!value) {
            next.delete(key);
          } else {
            next.set(key, value);
          }
        });
        return next;
      });
    },
    [setSearchParams]
  );

  const clearAuditFilters = useCallback(() => {
    updateQuery({
      sq_status: undefined,
      sq_issue_code: undefined,
      sq_would_block: undefined,
      sq_material_id: undefined,
      sq_selected_issue_code: undefined,
      tab: "sheet-quality",
    });
    setSubmitResult(null);
    setSubmitError(null);
  }, [updateQuery]);

  const clearTrailFilters = useCallback(() => {
    updateQuery({
      trail_material_id: undefined,
      trail_issue_code: undefined,
      trail_changed_by: undefined,
      trail_operation_status: undefined,
      trail_date_from: undefined,
      trail_date_to: undefined,
      trail_offset: undefined,
      trail_limit: undefined,
      tab: "sheet-quality",
    });
  }, [updateQuery]);

  const clearAllSheetQualityFilters = useCallback(() => {
    updateQuery({
      sq_status: undefined,
      sq_issue_code: undefined,
      sq_would_block: undefined,
      sq_material_id: undefined,
      sq_selected_issue_code: undefined,
      trail_material_id: undefined,
      trail_issue_code: undefined,
      trail_changed_by: undefined,
      trail_operation_status: undefined,
      trail_date_from: undefined,
      trail_date_to: undefined,
      trail_offset: undefined,
      trail_limit: undefined,
      tab: "sheet-quality",
    });
    setSubmitResult(null);
    setSubmitError(null);
  }, [updateQuery]);

  const fetchAudit = useCallback(async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const response = await getInventorySheetQualityAudit({
        status: urlState.sqStatus,
        issue_code: urlState.sqIssueCode,
        would_block_intake_assist: urlState.sqWouldBlock,
        limit: 200,
        offset: 0,
      });
      setAuditResponse(response);
    } catch (error) {
      setAuditError(mapBackendError(error));
      setAuditResponse(null);
    } finally {
      setAuditLoading(false);
    }
  }, [urlState.sqIssueCode, urlState.sqStatus, urlState.sqWouldBlock]);

  const fetchPlan = useCallback(async () => {
    setPlanLoading(true);
    setPlanError(null);
    try {
      const response = await getInventorySheetRemediationPlan();
      setPlanResponse(response);
    } catch (error) {
      setPlanError(mapBackendError(error));
      setPlanResponse(null);
    } finally {
      setPlanLoading(false);
    }
  }, []);

  const fetchAuditTrail = useCallback(async () => {
    setTrailLoading(true);
    setTrailError(null);
    try {
      const response = await getInventorySheetRemediationAuditTrail({
        material_id: urlState.trailMaterialId,
        issue_code: urlState.trailIssueCode,
        changed_by: urlState.trailChangedBy,
        date_from: urlState.trailDateFrom,
        date_to: urlState.trailDateTo,
        operation_status: urlState.trailOperationStatus,
        limit: urlState.trailLimit,
        offset: urlState.trailOffset,
      });
      setTrailResponse(response);
    } catch (error) {
      setTrailError(`Audit trail unavailable. ${mapBackendError(error)}`);
      setTrailResponse(null);
    } finally {
      setTrailLoading(false);
    }
  }, [
    urlState.trailChangedBy,
    urlState.trailDateFrom,
    urlState.trailDateTo,
    urlState.trailIssueCode,
    urlState.trailLimit,
    urlState.trailMaterialId,
    urlState.trailOffset,
    urlState.trailOperationStatus,
  ]);

  useEffect(() => {
    void fetchAudit();
  }, [fetchAudit]);

  useEffect(() => {
    void fetchPlan();
  }, [fetchPlan]);

  useEffect(() => {
    void fetchAuditTrail();
  }, [fetchAuditTrail]);

  const auditItems = auditResponse?.items || [];

  const selectedItem = useMemo<InventorySheetQualityAuditItem | null>(() => {
    if (!urlState.sqMaterialId || !urlState.sqSelectedIssueCode) return null;
    return (
      auditItems.find(
        (item) =>
          item.material_id === urlState.sqMaterialId &&
          item.issue_code === urlState.sqSelectedIssueCode
      ) || null
    );
  }, [auditItems, urlState.sqMaterialId, urlState.sqSelectedIssueCode]);

  const planItem = useMemo<InventorySheetRemediationPlanItem | null>(() => {
    if (!planResponse || !selectedItem) return null;
    return (
      planResponse.items.find(
        (item) =>
          item.material_id === selectedItem.material_id &&
          item.issue_code === selectedItem.issue_code
      ) || null
    );
  }, [planResponse, selectedItem]);

  useEffect(() => {
    if (!urlState.sqMaterialId || !urlState.sqSelectedIssueCode) {
      return;
    }
    if (!auditLoading && auditResponse && !selectedItem) {
      setUiMessage("Selected material is not visible with current filters.");
    }
  }, [
    auditLoading,
    auditResponse,
    selectedItem,
    urlState.sqMaterialId,
    urlState.sqSelectedIssueCode,
  ]);

  const selectedIssueCode = selectedItem?.issue_code || undefined;
  const issueSupportedByExecution = !!selectedIssueCode && SUPPORTED_EXECUTION_ISSUES.includes(selectedIssueCode);

  const disableRemediationForm =
    !selectedItem ||
    !selectedIssueCode ||
    !issueSupportedByExecution ||
    planItem?.remediation_category === "not_repairable_without_domain_decision";

  const proposedValues = useMemo(() => buildProposedValues(formValues), [formValues]);
  const proposedValuesCount = Object.keys(proposedValues).length;

  const canSubmit =
    !disableRemediationForm &&
    reason.trim().length > 0 &&
    confirm &&
    proposedValuesCount > 0;

  const trailEvents = trailResponse?.events || [];
  const trailSummary = trailResponse?.summary;
  const pageIndex = Math.floor(urlState.trailOffset / urlState.trailLimit) + 1;
  const totalPages = trailSummary
    ? Math.max(1, Math.ceil(trailSummary.total_events / urlState.trailLimit))
    : 1;
  const canPrevPage = urlState.trailOffset > 0;
  const canNextPage =
    !!trailSummary &&
    urlState.trailOffset + trailSummary.returned_events < trailSummary.total_events;

  const auditActiveFilterChips = useMemo<ActiveFilterChip[]>(() => {
    const chips: ActiveFilterChip[] = [];
    const statusFromUrl = searchParams.get("sq_status");

    if (statusFromUrl && urlState.sqStatus !== "all") {
      chips.push({ key: "sq_status", label: "Status", value: urlState.sqStatus });
    }
    if (urlState.sqIssueCode) {
      chips.push({ key: "sq_issue_code", label: "Issue", value: urlState.sqIssueCode });
    }
    if (urlState.sqWouldBlock !== undefined) {
      chips.push({
        key: "sq_would_block",
        label: "Would block",
        value: urlState.sqWouldBlock ? "yes" : "no",
      });
    }
    if (urlState.sqMaterialId) {
      chips.push({ key: "sq_material_id", label: "Material", value: urlState.sqMaterialId });
    }
    if (urlState.sqSelectedIssueCode) {
      chips.push({
        key: "sq_selected_issue_code",
        label: "Selected issue",
        value: urlState.sqSelectedIssueCode,
      });
    }

    return chips;
  }, [
    searchParams,
    urlState.sqIssueCode,
    urlState.sqMaterialId,
    urlState.sqSelectedIssueCode,
    urlState.sqStatus,
    urlState.sqWouldBlock,
  ]);

  const trailActiveFilterChips = useMemo<ActiveFilterChip[]>(() => {
    const chips: ActiveFilterChip[] = [];
    if (urlState.trailMaterialId) {
      chips.push({
        key: "trail_material_id",
        label: "Trail material",
        value: urlState.trailMaterialId,
      });
    }
    if (urlState.trailIssueCode) {
      chips.push({ key: "trail_issue_code", label: "Trail issue", value: urlState.trailIssueCode });
    }
    if (urlState.trailChangedBy) {
      chips.push({ key: "trail_changed_by", label: "Changed by", value: urlState.trailChangedBy });
    }
    if (urlState.trailOperationStatus) {
      chips.push({
        key: "trail_operation_status",
        label: "Operation",
        value: urlState.trailOperationStatus,
      });
    }
    if (urlState.trailDateFrom) {
      chips.push({ key: "trail_date_from", label: "From", value: toReadableDate(urlState.trailDateFrom) });
    }
    if (urlState.trailDateTo) {
      chips.push({ key: "trail_date_to", label: "To", value: toReadableDate(urlState.trailDateTo) });
    }
    if (urlState.trailLimit !== DEFAULT_TRAIL_LIMIT) {
      chips.push({ key: "trail_limit", label: "Page size", value: String(urlState.trailLimit) });
    }
    if (urlState.trailOffset > 0) {
      chips.push({ key: "trail_offset", label: "Offset", value: String(urlState.trailOffset) });
    }
    return chips;
  }, [
    urlState.trailChangedBy,
    urlState.trailDateFrom,
    urlState.trailDateTo,
    urlState.trailIssueCode,
    urlState.trailLimit,
    urlState.trailMaterialId,
    urlState.trailOffset,
    urlState.trailOperationStatus,
  ]);

  const hasAuditExportFilters = auditActiveFilterChips.length > 0;
  const hasTrailExportFilters = trailActiveFilterChips.length > 0;

  function removeAuditChip(key: ActiveFilterChip["key"]) {
    if (key === "sq_status" || key === "sq_issue_code" || key === "sq_would_block") {
      updateQuery({
        [key]: undefined,
        sq_material_id: undefined,
        sq_selected_issue_code: undefined,
        tab: "sheet-quality",
      });
      setSubmitResult(null);
      setSubmitError(null);
      return;
    }

    if (key === "sq_material_id" || key === "sq_selected_issue_code") {
      updateQuery({
        sq_material_id: undefined,
        sq_selected_issue_code: undefined,
        tab: "sheet-quality",
      });
      setSubmitResult(null);
      setSubmitError(null);
    }
  }

  function removeTrailChip(key: ActiveFilterChip["key"]) {
    if (key === "trail_offset") {
      updateQuery({ trail_offset: undefined, tab: "sheet-quality" });
      return;
    }
    if (key === "trail_limit") {
      updateQuery({ trail_limit: undefined, trail_offset: "0", tab: "sheet-quality" });
      return;
    }
    updateQuery({ [key]: undefined, trail_offset: "0", tab: "sheet-quality" });
  }

  async function handleSubmitRemediation() {
    if (!selectedItem || !selectedItem.issue_code) {
      setSubmitError("Select one invalid material first.");
      return;
    }

    if (!canSubmit) {
      setSubmitError(
        "Submit blocked: selected material, issue_code, reason, confirm, and proposed_values are required."
      );
      return;
    }

    setSubmitLoading(true);
    setSubmitError(null);

    try {
      const payload: InventorySheetRemediationRequest = {
        issue_code: selectedItem.issue_code,
        proposed_values: proposedValues,
        reason: reason.trim(),
        confirm: true,
      };

      const response = await remediateInventorySheetMaterial(selectedItem.material_id, payload);
      setSubmitResult(response);

      setFormValues(EMPTY_FORM);
      setReason("");
      setConfirm(false);

      updateQuery({
        tab: "sheet-quality",
        sq_material_id: response.material_id,
        sq_selected_issue_code: response.issue_code,
      });

      await Promise.all([fetchAudit(), fetchPlan(), fetchAuditTrail()]);
    } catch (error) {
      setSubmitError(mapBackendError(error));
    } finally {
      setSubmitLoading(false);
    }
  }

  async function handleCopyLink() {
    if (!selectedItem || !selectedItem.issue_code) return;

    const relativeLink = buildSheetQualityUrl({
      sq_material_id: selectedItem.material_id,
      sq_selected_issue_code: selectedItem.issue_code,
    });
    const absoluteLink = new URL(relativeLink, window.location.origin).toString();

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(absoluteLink);
        setUiMessage("Remediation deep link copied.");
      } else {
        setUiMessage(`Copy this remediation link: ${absoluteLink}`);
      }
    } catch {
      setUiMessage(`Copy this remediation link: ${absoluteLink}`);
    }
  }

  function handleAuditFilterChange(updates: {
    status?: InventorySheetAuditStatus;
    issueCode?: InventorySheetAuditIssueCode | "";
    wouldBlock?: "all" | "true" | "false";
  }) {
    const nextStatus = updates.status ?? urlState.sqStatus;
    const nextIssueCode = updates.issueCode ?? (urlState.sqIssueCode || "");
    const nextWouldBlock = updates.wouldBlock ?? (urlState.sqWouldBlock === undefined ? "all" : String(urlState.sqWouldBlock) as "true" | "false");

    updateQuery({
      sq_status: nextStatus,
      sq_issue_code: nextIssueCode || undefined,
      sq_would_block: nextWouldBlock === "all" ? undefined : nextWouldBlock,
      sq_material_id: undefined,
      sq_selected_issue_code: undefined,
      tab: "sheet-quality",
    });

    setSubmitResult(null);
    setSubmitError(null);
  }

  function handleAuditItemSelect(item: InventorySheetQualityAuditItem) {
    updateQuery({
      sq_material_id: item.material_id,
      sq_selected_issue_code: item.issue_code || undefined,
      tab: "sheet-quality",
    });
    setSubmitError(null);
    setSubmitResult(null);
  }

  function applyTrailFilters() {
    const dateFrom = asISODateFromInput(trailDateFromDraft);
    const dateTo = asISODateFromInput(trailDateToDraft);

    if (trailDateFromDraft.trim() && !dateFrom) {
      setTrailError("Invalid date range.");
      return;
    }
    if (trailDateToDraft.trim() && !dateTo) {
      setTrailError("Invalid date range.");
      return;
    }

    updateQuery({
      trail_material_id: trailMaterialDraft.trim() || undefined,
      trail_issue_code: trailIssueDraft || undefined,
      trail_changed_by: trailChangedByDraft.trim() || undefined,
      trail_operation_status: trailOpStatusDraft || undefined,
      trail_date_from: dateFrom,
      trail_date_to: dateTo,
      trail_offset: "0",
      tab: "sheet-quality",
    });
  }

  function handleTrailLimitChange(limit: number) {
    updateQuery({
      trail_limit: String(limit),
      trail_offset: "0",
      tab: "sheet-quality",
    });
  }

  function applyTrailPreset(hours: number) {
    const now = new Date();
    const from = new Date(now.getTime() - hours * 60 * 60 * 1000);
    updateQuery({
      trail_date_from: from.toISOString(),
      trail_date_to: now.toISOString(),
      trail_offset: "0",
      tab: "sheet-quality",
    });
  }

  function clearTrailDateRange() {
    updateQuery({
      trail_date_from: undefined,
      trail_date_to: undefined,
      trail_offset: "0",
      tab: "sheet-quality",
    });
  }

  function goToPrevPage() {
    const nextOffset = Math.max(0, urlState.trailOffset - urlState.trailLimit);
    updateQuery({
      trail_offset: String(nextOffset),
      tab: "sheet-quality",
    });
  }

  function goToNextPage() {
    const nextOffset = urlState.trailOffset + urlState.trailLimit;
    updateQuery({
      trail_offset: String(nextOffset),
      tab: "sheet-quality",
    });
  }

  function viewSelectedMaterialTrail() {
    if (!selectedItem) return;
    updateQuery({
      trail_material_id: selectedItem.material_id,
      trail_offset: "0",
      tab: "sheet-quality",
    });
  }

  async function handleExport(
    target: "audit_csv" | "audit_json" | "trail_csv" | "trail_json"
  ) {
    setExportError(null);
    setExportLoading(target);

    try {
      if (target === "audit_csv" || target === "audit_json") {
        const format = target === "audit_csv" ? "csv" : "json";
        const url = buildInventorySheetQualityAuditExportUrl({
          format,
          status: urlState.sqStatus,
          issue_code: urlState.sqIssueCode,
          would_block_intake_assist: urlState.sqWouldBlock,
          limit: 1000,
          offset: 0,
        });
        await downloadInventorySheetExport(
          url,
          format === "csv"
            ? "inventory_sheet_quality_audit.csv"
            : "inventory_sheet_quality_audit.json"
        );
      } else {
        const format = target === "trail_csv" ? "csv" : "json";
        const url = buildInventorySheetRemediationAuditTrailExportUrl({
          format,
          material_id: urlState.trailMaterialId,
          issue_code: urlState.trailIssueCode,
          changed_by: urlState.trailChangedBy,
          date_from: urlState.trailDateFrom,
          date_to: urlState.trailDateTo,
          operation_status: urlState.trailOperationStatus,
          limit: urlState.trailLimit,
          offset: urlState.trailOffset,
        });
        await downloadInventorySheetExport(
          url,
          format === "csv"
            ? "inventory_sheet_remediation_audit_trail.csv"
            : "inventory_sheet_remediation_audit_trail.json"
        );
      }
    } catch (error) {
      setExportError(mapBackendError(error));
    } finally {
      setExportLoading(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <h2 className="text-[14px] font-semibold text-slate-100">Inventory Sheet Quality</h2>
        </div>
        <button
          onClick={() => {
            void fetchAudit();
            void fetchPlan();
            void fetchAuditTrail();
          }}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] text-slate-300 border border-[#2A3548] rounded hover:bg-[#1A2236]"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {urlState.invalidFiltersIgnored && (
        <div className="text-[12px] text-amber-300 bg-amber-900/20 border border-amber-800/40 rounded p-2">
          Invalid URL filters were ignored.
        </div>
      )}

      {uiMessage && (
        <div className="text-[12px] text-blue-300 bg-blue-900/20 border border-blue-800/40 rounded p-2">
          {uiMessage}
        </div>
      )}

      {exportError && (
        <div className="text-[12px] text-red-300 bg-red-900/20 border border-red-800/40 rounded p-2">
          Export failed: {exportError}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2">
          <p className="text-[10px] uppercase text-slate-500">Total checked</p>
          <p className="text-[18px] font-semibold text-slate-100">{auditResponse?.summary.total_records_checked ?? "-"}</p>
        </div>
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2">
          <p className="text-[10px] uppercase text-slate-500">Valid</p>
          <p className="text-[18px] font-semibold text-emerald-400">{auditResponse?.summary.valid_count ?? "-"}</p>
        </div>
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2">
          <p className="text-[10px] uppercase text-slate-500">Invalid</p>
          <p className="text-[18px] font-semibold text-red-400">{auditResponse?.summary.invalid_count ?? "-"}</p>
        </div>
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2">
          <p className="text-[10px] uppercase text-slate-500">Not applicable</p>
          <p className="text-[18px] font-semibold text-slate-300">{auditResponse?.summary.not_applicable_count ?? "-"}</p>
        </div>
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2">
          <p className="text-[10px] uppercase text-slate-500">Would block</p>
          <p className="text-[18px] font-semibold text-amber-400">{auditResponse?.summary.would_block_intake_assist_count ?? "-"}</p>
        </div>
      </div>

      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3 space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={urlState.sqStatus}
            onChange={(event) =>
              handleAuditFilterChange({
                status: event.target.value as InventorySheetAuditStatus,
              })
            }
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          >
            <option value="all">status: all</option>
            <option value="valid">status: valid</option>
            <option value="invalid">status: invalid</option>
            <option value="not_applicable">status: not_applicable</option>
          </select>

          <select
            value={urlState.sqIssueCode || ""}
            onChange={(event) =>
              handleAuditFilterChange({
                issueCode: event.target.value as InventorySheetAuditIssueCode | "",
              })
            }
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          >
            <option value="">issue_code: all</option>
            {ISSUE_CODES.map((issueCode) => (
              <option key={issueCode} value={issueCode}>
                {issueCode}
              </option>
            ))}
          </select>

          <select
            value={urlState.sqWouldBlock === undefined ? "all" : String(urlState.sqWouldBlock)}
            onChange={(event) =>
              handleAuditFilterChange({
                wouldBlock: event.target.value as "all" | "true" | "false",
              })
            }
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          >
            <option value="all">would_block: all</option>
            <option value="true">would_block: true</option>
            <option value="false">would_block: false</option>
          </select>

          <button
            onClick={() => void handleExport("audit_csv")}
            disabled={exportLoading !== null}
            className="px-2.5 py-1.5 text-[12px] text-emerald-300 border border-emerald-700/40 rounded hover:bg-emerald-900/20 disabled:opacity-50"
          >
            {exportLoading === "audit_csv" ? "Exporting..." : "Export audit CSV"}
          </button>

          <button
            onClick={() => void handleExport("audit_json")}
            disabled={exportLoading !== null}
            className="px-2.5 py-1.5 text-[12px] text-cyan-300 border border-cyan-700/40 rounded hover:bg-cyan-900/20 disabled:opacity-50"
          >
            {exportLoading === "audit_json" ? "Exporting..." : "Export audit JSON"}
          </button>

          <button
            onClick={clearAuditFilters}
            className="px-2.5 py-1.5 text-[12px] text-slate-300 border border-[#2A3548] rounded hover:bg-[#1A2236]"
          >
            Reset audit filters
          </button>

          <button
            onClick={clearAllSheetQualityFilters}
            className="px-2.5 py-1.5 text-[12px] text-slate-200 border border-[#2A3548] rounded hover:bg-[#1A2236]"
          >
            Reset all Sheet Quality filters
          </button>
        </div>

        <div className="text-[11px] text-slate-400 bg-[#0D1321] border border-[#1E293B] rounded p-2">
          <p>Exports use current filters.</p>
          <p>{hasAuditExportFilters ? "Audit export: filtered." : "No filters active for this export."}</p>
        </div>

        <div className="bg-[#0D1321] border border-[#1E293B] rounded p-2 space-y-2">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Active audit filters</p>
          {auditActiveFilterChips.length === 0 ? (
            <p className="text-[12px] text-slate-500">No audit filters active.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {auditActiveFilterChips.map((chip) => (
                <button
                  key={chip.key}
                  onClick={() => removeAuditChip(chip.key)}
                  className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-blue-700/40 bg-blue-900/20 text-blue-200 hover:bg-blue-900/30"
                >
                  <span className="text-blue-300">{chip.label}:</span>
                  <span>{chip.value}</span>
                  <span className="text-blue-300">x</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {auditLoading && (
          <div className="flex items-center gap-2 text-[12px] text-slate-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading audit report...
          </div>
        )}

        {auditError && (
          <div className="flex items-start gap-2 p-3 bg-red-900/20 border border-red-800/40 rounded">
            <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5" />
            <div className="text-[12px] text-red-300">
              <p className="font-semibold">Inventory Sheet Quality audit unavailable.</p>
              <p>{auditError}</p>
            </div>
          </div>
        )}

        {!auditLoading && !auditError && auditItems.length === 0 && (
          <div className="text-[12px] text-slate-500 italic">No audit items found for the selected filters.</div>
        )}

        {!auditLoading && !auditError && auditItems.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="text-left text-slate-500 border-b border-[#1E293B]">
                  <th className="px-2 py-2">Material</th>
                  <th className="px-2 py-2">Code</th>
                  <th className="px-2 py-2">Category</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Issue code</th>
                  <th className="px-2 py-2">Message</th>
                  <th className="px-2 py-2">Recommended action</th>
                  <th className="px-2 py-2">Would block</th>
                </tr>
              </thead>
              <tbody>
                {auditItems.map((item) => {
                  const isSelected =
                    urlState.sqMaterialId === item.material_id &&
                    urlState.sqSelectedIssueCode === item.issue_code;
                  return (
                    <tr
                      key={`${item.material_id}-${item.issue_code || "none"}`}
                      onClick={() => handleAuditItemSelect(item)}
                      className={`border-b border-[#1E293B]/60 cursor-pointer ${
                        isSelected ? "bg-blue-900/20" : "hover:bg-[#1A2236]/60"
                      }`}
                    >
                      <td className="px-2 py-2 text-slate-200">{item.material_name || "-"}</td>
                      <td className="px-2 py-2 font-mono text-slate-400">{item.material_code || item.material_id}</td>
                      <td className="px-2 py-2 text-slate-400">{item.category || "-"}</td>
                      <td className="px-2 py-2 text-slate-300">{item.status}</td>
                      <td className="px-2 py-2 text-amber-300">{item.issue_code || "-"}</td>
                      <td className="px-2 py-2 text-slate-300">{item.message}</td>
                      <td className="px-2 py-2 text-slate-400">{item.recommended_action || "-"}</td>
                      <td className="px-2 py-2 text-slate-300">{String(item.would_block_intake_assist)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3 space-y-3">
          <h3 className="text-[13px] font-semibold text-slate-100">Remediation plan</h3>

          {planLoading && (
            <div className="flex items-center gap-2 text-[12px] text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading remediation plan...
            </div>
          )}

          {planError && (
            <div className="text-[12px] text-red-300 bg-red-900/20 border border-red-800/40 rounded p-2">
              {planError}
            </div>
          )}

          {!selectedItem && (
            <div className="text-[12px] text-slate-500">
              Select one invalid audit item to inspect remediation policy.
            </div>
          )}

          {selectedItem && !planItem && !planLoading && (
            <div className="text-[12px] text-amber-300 bg-amber-900/20 border border-amber-800/40 rounded p-2">
              Selected material not found under current filters.
            </div>
          )}

          {selectedItem && planItem && (
            <div className="space-y-2 text-[12px]">
              <p className="text-slate-200">
                <span className="text-slate-500">material_id:</span> {planItem.material_id}
              </p>
              <p className="text-slate-200">
                <span className="text-slate-500">issue_code:</span> {planItem.issue_code}
              </p>
              <p className="text-slate-200">
                <span className="text-slate-500">remediation_category:</span> {planItem.remediation_category}
              </p>
              <p className="text-slate-300">
                <span className="text-slate-500">requires_operator_input:</span> {String(planItem.requires_operator_input)}
              </p>
              <p className="text-slate-300">
                <span className="text-slate-500">requires_admin_confirmation:</span> {String(planItem.requires_admin_confirmation)}
              </p>
              <p className="text-slate-300">
                <span className="text-slate-500">future_automation_eligible:</span> {String(planItem.future_automation_eligible)}
              </p>
              <p className="text-slate-300">
                <span className="text-slate-500">recommended_next_step:</span> {planItem.recommended_next_step}
              </p>

              <button
                onClick={viewSelectedMaterialTrail}
                className="inline-flex items-center gap-1 px-2 py-1 text-[11px] text-blue-300 border border-blue-700/40 rounded hover:bg-blue-900/20"
              >
                <ExternalLink className="w-3 h-3" />
                View audit trail for this material
              </button>

              <button
                onClick={() => void handleCopyLink()}
                className="inline-flex items-center gap-1 px-2 py-1 text-[11px] text-slate-300 border border-[#2A3548] rounded hover:bg-[#1A2236]"
              >
                <Copy className="w-3 h-3" />
                Copy remediation link
              </button>

              <div>
                <p className="text-slate-500 mb-1">allowed_actions:</p>
                <ul className="list-disc pl-5 text-slate-300 space-y-1">
                  {planItem.allowed_actions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-slate-500 mb-1">forbidden_actions:</p>
                <ul className="list-disc pl-5 text-slate-300 space-y-1">
                  {planItem.forbidden_actions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {!issueSupportedByExecution && selectedIssueCode && (
            <div className="text-[12px] text-amber-300 bg-amber-900/20 border border-amber-800/40 rounded p-2">
              This issue requires manual/domain remediation outside this endpoint.
            </div>
          )}
        </div>

        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3 space-y-3">
          <h3 className="text-[13px] font-semibold text-slate-100">Single-material remediation</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <input
              value={formValues.sheet_format_type}
              onChange={(event) => setFormValues((prev) => ({ ...prev, sheet_format_type: event.target.value }))}
              placeholder="sheet_format_type"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.sheet_unit}
              onChange={(event) => setFormValues((prev) => ({ ...prev, sheet_unit: event.target.value }))}
              placeholder="sheet_unit"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.sheet_width}
              onChange={(event) => setFormValues((prev) => ({ ...prev, sheet_width: event.target.value }))}
              placeholder="sheet_width (ex: 3050)"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.sheet_height}
              onChange={(event) => setFormValues((prev) => ({ ...prev, sheet_height: event.target.value }))}
              placeholder="sheet_height (ex: 2050)"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.sheet_thickness}
              onChange={(event) => setFormValues((prev) => ({ ...prev, sheet_thickness: event.target.value }))}
              placeholder="sheet_thickness"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.sheet_thickness_unit}
              onChange={(event) => setFormValues((prev) => ({ ...prev, sheet_thickness_unit: event.target.value }))}
              placeholder="sheet_thickness_unit"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.usable_width}
              onChange={(event) => setFormValues((prev) => ({ ...prev, usable_width: event.target.value }))}
              placeholder="usable_width"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.usable_height}
              onChange={(event) => setFormValues((prev) => ({ ...prev, usable_height: event.target.value }))}
              placeholder="usable_height"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.format_source}
              onChange={(event) => setFormValues((prev) => ({ ...prev, format_source: event.target.value }))}
              placeholder="format_source"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
            <input
              value={formValues.format_notes}
              onChange={(event) => setFormValues((prev) => ({ ...prev, format_notes: event.target.value }))}
              placeholder="format_notes"
              disabled={disableRemediationForm}
              className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
            />
          </div>

          <label className="flex items-center gap-2 text-[12px] text-slate-300">
            <input
              type="checkbox"
              checked={formValues.format_verified}
              onChange={(event) => setFormValues((prev) => ({ ...prev, format_verified: event.target.checked }))}
              disabled={disableRemediationForm}
            />
            format_verified
          </label>

          <textarea
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="reason (required)"
            disabled={disableRemediationForm}
            className="w-full bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200 min-h-[68px]"
          />

          <label className="flex items-center gap-2 text-[12px] text-slate-300">
            <input
              type="checkbox"
              checked={confirm}
              onChange={(event) => setConfirm(event.target.checked)}
              disabled={disableRemediationForm}
            />
            confirm=true (required)
          </label>

          <div className="text-[11px] text-slate-500">proposed_values fields provided: {proposedValuesCount}</div>

          {submitError && (
            <div className="text-[12px] text-red-300 bg-red-900/20 border border-red-800/40 rounded p-2">
              {submitError}
            </div>
          )}

          <button
            onClick={() => void handleSubmitRemediation()}
            disabled={!canSubmit || submitLoading}
            className="px-3 py-1.5 text-[12px] rounded border border-blue-700/40 text-blue-300 hover:bg-blue-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitLoading ? "Submitting..." : "Submit single-material remediation"}
          </button>

          {submitResult && (
            <div className="space-y-2 bg-emerald-900/10 border border-emerald-800/30 rounded p-3">
              <div className="flex items-center gap-2 text-emerald-300 text-[12px] font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                status: {submitResult.status}
              </div>
              <p className="text-[12px] text-slate-200">material_id: {submitResult.material_id}</p>
              <p className="text-[12px] text-slate-200">issue_code: {submitResult.issue_code}</p>
              <p className="text-[12px] text-slate-200">before audit status: {submitResult.before.audit_status}</p>
              <p className="text-[12px] text-slate-200">after audit status: {submitResult.after.audit_status}</p>
              <p className="text-[12px] text-slate-200">audit_event_id: {submitResult.audit_event_id}</p>
              {submitResult.warnings.length > 0 && (
                <div className="text-[12px] text-amber-300">
                  warnings: {submitResult.warnings.join(" | ")}
                </div>
              )}
              <div>
                <p className="text-[11px] text-slate-500 mb-1">before.sheet_format</p>
                <JsonBlock data={submitResult.before.sheet_format} />
              </div>
              <div>
                <p className="text-[11px] text-slate-500 mb-1">after.sheet_format</p>
                <JsonBlock data={submitResult.after.sheet_format} />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3 space-y-3">
        <h3 className="text-[13px] font-semibold text-slate-100">Remediation audit trail (read-only)</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
          <input
            value={trailMaterialDraft}
            onChange={(event) => setTrailMaterialDraft(event.target.value)}
            placeholder="trail material_id"
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          />

          <select
            value={trailIssueDraft}
            onChange={(event) => setTrailIssueDraft(event.target.value as InventorySheetAuditIssueCode | "")}
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          >
            <option value="">trail issue_code: all</option>
            {ISSUE_CODES.map((issueCode) => (
              <option key={issueCode} value={issueCode}>
                {issueCode}
              </option>
            ))}
          </select>

          <input
            value={trailChangedByDraft}
            onChange={(event) => setTrailChangedByDraft(event.target.value)}
            placeholder="trail changed_by"
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          />

          <select
            value={trailOpStatusDraft}
            onChange={(event) =>
              setTrailOpStatusDraft(event.target.value as InventorySheetRemediationOperationStatus | "")
            }
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          >
            <option value="">trail operation_status: all</option>
            <option value="applied">applied</option>
            <option value="failed">failed</option>
          </select>

          <input
            value={trailDateFromDraft}
            onChange={(event) => setTrailDateFromDraft(event.target.value)}
            type="datetime-local"
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          />

          <input
            value={trailDateToDraft}
            onChange={(event) => setTrailDateToDraft(event.target.value)}
            type="datetime-local"
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1.5 text-[12px] text-slate-200"
          />

          <button
            onClick={applyTrailFilters}
            className="px-2.5 py-1.5 text-[12px] text-blue-300 border border-blue-700/40 rounded hover:bg-blue-900/20"
          >
            Apply trail filters
          </button>

          <button
            onClick={() => applyTrailPreset(24)}
            className="px-2.5 py-1.5 text-[12px] text-violet-300 border border-violet-700/40 rounded hover:bg-violet-900/20"
          >
            Last 24h
          </button>

          <button
            onClick={() => applyTrailPreset(24 * 7)}
            className="px-2.5 py-1.5 text-[12px] text-violet-300 border border-violet-700/40 rounded hover:bg-violet-900/20"
          >
            Last 7d
          </button>

          <button
            onClick={clearTrailDateRange}
            className="px-2.5 py-1.5 text-[12px] text-slate-300 border border-[#2A3548] rounded hover:bg-[#1A2236]"
          >
            Clear date range
          </button>

          <button
            onClick={() => void handleExport("trail_csv")}
            disabled={exportLoading !== null}
            className="px-2.5 py-1.5 text-[12px] text-emerald-300 border border-emerald-700/40 rounded hover:bg-emerald-900/20 disabled:opacity-50"
          >
            {exportLoading === "trail_csv" ? "Exporting..." : "Export trail CSV"}
          </button>

          <button
            onClick={() => void handleExport("trail_json")}
            disabled={exportLoading !== null}
            className="px-2.5 py-1.5 text-[12px] text-cyan-300 border border-cyan-700/40 rounded hover:bg-cyan-900/20 disabled:opacity-50"
          >
            {exportLoading === "trail_json" ? "Exporting..." : "Export trail JSON"}
          </button>

          <button
            onClick={clearTrailFilters}
            className="px-2.5 py-1.5 text-[12px] text-slate-300 border border-[#2A3548] rounded hover:bg-[#1A2236]"
          >
            Reset trail filters
          </button>
        </div>

        <div className="text-[11px] text-slate-400 bg-[#0D1321] border border-[#1E293B] rounded p-2">
          <p>Exports use current filters.</p>
          <p>{hasTrailExportFilters ? "Trail export: filtered." : "No filters active for this export."}</p>
        </div>

        <div className="bg-[#0D1321] border border-[#1E293B] rounded p-2 space-y-2">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Active trail filters</p>
          {trailActiveFilterChips.length === 0 ? (
            <p className="text-[12px] text-slate-500">No audit trail filters active.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {trailActiveFilterChips.map((chip) => (
                <button
                  key={chip.key}
                  onClick={() => removeTrailChip(chip.key)}
                  className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-teal-700/40 bg-teal-900/20 text-teal-200 hover:bg-teal-900/30"
                >
                  <span className="text-teal-300">{chip.label}:</span>
                  <span>{chip.value}</span>
                  <span className="text-teal-300">x</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[12px] text-slate-400">Page size:</span>
          <select
            value={urlState.trailLimit}
            onChange={(event) => handleTrailLimitChange(Number(event.target.value))}
            className="bg-[#0D1321] border border-[#1E293B] rounded px-2 py-1 text-[12px] text-slate-200"
          >
            {TRAIL_LIMIT_OPTIONS.map((limit) => (
              <option key={limit} value={limit}>
                {limit}
              </option>
            ))}
          </select>

          <button
            onClick={goToPrevPage}
            disabled={!canPrevPage}
            className="px-2.5 py-1 text-[12px] text-slate-300 border border-[#2A3548] rounded disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={goToNextPage}
            disabled={!canNextPage}
            className="px-2.5 py-1 text-[12px] text-slate-300 border border-[#2A3548] rounded disabled:opacity-50"
          >
            Next
          </button>

          <span className="text-[12px] text-slate-400">
            Page {pageIndex}/{totalPages}
            {trailSummary ? ` • total events: ${trailSummary.total_events}` : ""}
          </span>
        </div>

        {trailLoading && (
          <div className="flex items-center gap-2 text-[12px] text-slate-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading audit trail...
          </div>
        )}

        {trailError && (
          <div className="text-[12px] text-red-300 bg-red-900/20 border border-red-800/40 rounded p-2">
            {trailError}
          </div>
        )}

        {!trailLoading && !trailError && trailEvents.length === 0 && (
          <div className="text-[12px] text-slate-500 italic">No audit trail events found.</div>
        )}

        {!trailLoading && !trailError && trailEvents.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="text-left text-slate-500 border-b border-[#1E293B]">
                  <th className="px-2 py-2">changed_at</th>
                  <th className="px-2 py-2">material_id</th>
                  <th className="px-2 py-2">issue_code</th>
                  <th className="px-2 py-2">changed_by</th>
                  <th className="px-2 py-2">reason</th>
                  <th className="px-2 py-2">operation_status</th>
                  <th className="px-2 py-2">audit_event_id</th>
                </tr>
              </thead>
              <tbody>
                {trailEvents.map((event: InventorySheetRemediationAuditEvent) => {
                  const expanded = expandedAuditEventId === event.audit_event_id;
                  return (
                    <Fragment key={event.audit_event_id}>
                      <tr
                        className="border-b border-[#1E293B]/60 hover:bg-[#1A2236]/50 cursor-pointer"
                        onClick={() => setExpandedAuditEventId(expanded ? null : event.audit_event_id)}
                      >
                        <td className="px-2 py-2 text-slate-300">{event.changed_at}</td>
                        <td className="px-2 py-2 text-slate-300">{event.material_id}</td>
                        <td className="px-2 py-2 text-amber-300">{event.issue_code}</td>
                        <td className="px-2 py-2 text-slate-400">{event.changed_by || "-"}</td>
                        <td className="px-2 py-2 text-slate-300">{event.reason}</td>
                        <td className="px-2 py-2 text-slate-300">{event.operation_status}</td>
                        <td className="px-2 py-2 font-mono text-slate-400">{event.audit_event_id}</td>
                      </tr>
                      {expanded && (
                        <tr className="border-b border-[#1E293B]/60 bg-[#0D1321]">
                          <td className="px-2 py-2" colSpan={7}>
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
                              <div>
                                <p className="text-[11px] text-slate-500 mb-1">old_values</p>
                                <JsonBlock data={event.old_values} />
                              </div>
                              <div>
                                <p className="text-[11px] text-slate-500 mb-1">new_values</p>
                                <JsonBlock data={event.new_values} />
                              </div>
                              <div>
                                <p className="text-[11px] text-slate-500 mb-1">validation_result_before</p>
                                <JsonBlock data={event.validation_result_before} />
                              </div>
                              <div>
                                <p className="text-[11px] text-slate-500 mb-1">validation_result_after</p>
                                <JsonBlock data={event.validation_result_after} />
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
