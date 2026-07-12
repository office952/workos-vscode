import { getAPIBaseURL } from "@/lib/config";
import { IntakeV4ApiError as BaseIntakeApiError } from "./intakeV4Api";
import type {
  IntakeV4AiInformationalAssistPreviewResponse,
  IntakeV4CreateDraftQuoteRequest,
  IntakeV4CommercialSpineStateResponse,
  IntakeV4CreateDraftQuoteResponse,
  IntakeV4FinishSetup,
  IntakeV4LayerRoleSetup,
  IntakeV4NestingPreviewResponse,
  IntakeV4OrderBoundTaskReadinessResponse,
  IntakeV4PricingInputPreviewResponse,
  IntakeV4ProductionTaskDryRunResponse,
  IntakeV4ProductionHandoffPreviewResponse,
  IntakeV4ProductSystemBindingResponse,
  IntakeV4QuoteHandoffPreviewResponse,
  IntakeV4TaskGenerationDryRunResponse,
  IntakeV4TaskPreviewResponse,
  IntakeV4TemplateFormContractResponse,
  IntakeV4WorkspaceResponse,
} from "./intakeV4Api";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";
import type {
  IntakeV6OfferHandoffRequest,
  IntakeV6OfferHandoffResponse,
  IntakeV6LogicalListReadModelResponse,
  IntakeV6PricedQuoteDryRunResponse,
  IntakeV6PricedQuoteWriteRequest,
  IntakeV6PricedQuoteWriteResponse,
  IntakeV6QuoteSnapshotV2CreateRequest,
  IntakeV6QuoteSnapshotV2CreateResponse,
} from "./intakeV6PricedQuoteTypes";

export * from "./intakeV4Api";
export type {
  IntakeV6CommercialTotals,
  IntakeV6OfferHandoffRequest,
  IntakeV6OfferHandoffResponse,
  IntakeV6LogicalListLineTrace,
  IntakeV6LogicalListReadModelResponse,
  IntakeV6PricedQuoteBlocker,
  IntakeV6PricedQuoteDryRunResponse,
  IntakeV6PricedQuoteWriteRequest,
  IntakeV6PricedQuoteWriteResponse,
  IntakeV6QuoteSnapshotV2CreateRequest,
  IntakeV6QuoteSnapshotV2CreateResponse,
} from "./intakeV6PricedQuoteTypes";

const intakeV6ApiBase = () => `${getAPIBaseURL()}/api/v1/intake-v6`;

export type IntakeV6OrderBoundTaskReadinessResponse = Omit<
  IntakeV4OrderBoundTaskReadinessResponse,
  "v4_order_conversion"
> & {
  v6_order_conversion: Record<string, unknown>;
};

export type IntakeV6CommercialSpineStateResponse = Omit<
  IntakeV4CommercialSpineStateResponse,
  "is_iv4_quote" | "v4_order_conversion" | "v4_quote_to_order_enabled"
> & {
  is_v6_quote: boolean;
  snapshot_v2?: Record<string, unknown>;
  v6_order_conversion: Record<string, unknown>;
  v6_quote_to_order_enabled: boolean;
};

export interface IntakeV6RuntimeCaptureReadModelField {
  field_key: string;
  runtime_source: string;
  product_truth_path: string;
  state: string;
  confirmation_rule: string;
  blockers: string[];
  ready_for_product_truth: boolean;
}

export interface IntakeV6RuntimeCaptureReadModelBlocker {
  field_key: string;
  blockers: string[];
  state: string;
}

export interface IntakeV6RuntimeCaptureReadModelResponse {
  read_only: boolean;
  workspace_id: string;
  workspace_record_id: string;
  workspace_code: string;
  root_template_code: string | null;
  product_binding_template_code: string | null;
  read_model_version: string;
  fields: IntakeV6RuntimeCaptureReadModelField[];
  blockers: IntakeV6RuntimeCaptureReadModelBlocker[];
  downstream_write_intent: Record<string, boolean>;
  notes: string[];
}

export interface IntakeV6ProductTruthPromotionPlannerEntry {
  entry_key: string;
  field_key: string;
  runtime_source: string;
  product_truth_path: string;
  state: string;
  value_status: string;
  promotion_allowed: boolean;
  reason: string;
  blockers: string[];
  identity_key?: string;
}

export interface IntakeV6ProductTruthPromotionPlannerBlocker {
  field_key: string;
  identity_key?: string;
  blockers: string[];
  state: string;
}

export interface IntakeV6ProductTruthPromotionPlannerResponse {
  read_only: boolean;
  workspace_id: string;
  workspace_record_id: string;
  workspace_code: string;
  root_template_code: string | null;
  product_binding_template_code: string | null;
  planner_version: string;
  eligible_entries: IntakeV6ProductTruthPromotionPlannerEntry[];
  blocked_entries: IntakeV6ProductTruthPromotionPlannerEntry[];
  blockers: IntakeV6ProductTruthPromotionPlannerBlocker[];
  downstream_write_intent: Record<string, boolean>;
  notes: string[];
}

function parseIntakeV6ApiErrorMessage(status: number, raw: string): string {
  if (!raw.trim()) return `Request failed (${status})`;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (typeof parsed === "object" && parsed !== null && "detail" in parsed) {
      const detail = (parsed as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (typeof detail === "object" && detail !== null) {
        const obj = detail as Record<string, unknown>;
        if (typeof obj.message === "string") return obj.message;
        if (obj.error === "workspace_not_found") {
          return "Workspace V6 inexistent. Deschide /intake-v6/operator pentru un workspace V6 nou.";
        }
        if (typeof obj.error === "string") return obj.error;
      }
    }
  } catch {
    // keep raw text
  }
  return raw.length > 240 ? `${raw.slice(0, 240)}...` : raw;
}

async function requestIntakeV6Json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", cache: "no-store", ...init });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new BaseIntakeApiError(response.status, parseIntakeV6ApiErrorMessage(response.status, text));
  }
  return response.json() as Promise<T>;
}

export async function getIntakeV6Workspace(id: string): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/workspaces/${encodeURIComponent(id)}`);
}

export async function createIntakeV6Workspace(body: {
  title: string;
  template_code?: string;
  client_name?: string;
  job_title?: string;
  intake_request_code?: string;
  analyzer_mode?: "analyzer_first" | "template_hint" | "template_locked";
  template_hint_code?: string;
  selected_template_code?: string;
  offer_method?: string;
  source?: string;
}): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function ensureIntakeV6WorkspaceForIntakeRequest(
  intakeRequestCode: string,
  options: {
    offer_method?: string;
    analyzer_mode?: "analyzer_first" | "template_hint" | "template_locked";
    template_hint_code?: string;
    selected_template_code?: string;
    source?: string;
  } = {},
): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/workspaces/ensure-for-intake-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intake_request_code: intakeRequestCode, ...options }),
  });
}

export async function persistIntakeV6AnalysisBundle(
  workspaceId: string,
  body: {
    file_name: string;
    file_size_bytes: number;
    svg_text: string;
    svg_analysis_json: Record<string, unknown>;
    layer_role_setup: IntakeV4LayerRoleSetup;
  },
): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/analysis-bundle`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function saveIntakeV6FinishSetup(
  workspaceId: string,
  body: IntakeV4FinishSetup,
): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/finish-setup`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function saveIntakeV6ProductCompositionConfirmation(
  workspaceId: string,
  body: {
    confirmed: boolean;
    items?: Array<Record<string, unknown>>;
    operator_note?: string | null;
  },
): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/product-composition-confirmation`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function saveIntakeV6OfferScope(
  workspaceId: string,
  body: {
    mode: "full_product" | "component_subset";
    sold_modules: Array<"FACE" | "RETURN-CANT" | "BACK">;
    confirmed: boolean;
    operator_note?: string | null;
  },
): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/offer-scope`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function getIntakeV6TaskPreview(
  workspaceId: string,
  finishDraft?: Partial<IntakeV4FinishSetup>,
): Promise<IntakeV4TaskPreviewResponse> {
  const params = new URLSearchParams();
  if (finishDraft?.face_finish_type) params.set("face_finish_type", finishDraft.face_finish_type);
  if (finishDraft?.return_finish_type) params.set("return_finish_type", finishDraft.return_finish_type);
  if (finishDraft?.illuminated != null) params.set("illuminated", String(finishDraft.illuminated));
  if (finishDraft?.lighting_system_type) {
    params.set("lighting_system_type", finishDraft.lighting_system_type);
  }
  const qs = params.toString();
  const suffix = qs ? `?${qs}` : "";
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/task-preview${suffix}`,
  );
}

export async function getIntakeV6MaterialBreakdown(
  workspaceId: string,
): Promise<import("./intakeV4Api").IntakeV4MaterialBreakdownResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/material-breakdown`,
  );
}

export async function getIntakeV6LogicalListReadModel(
  workspaceId: string,
): Promise<IntakeV6LogicalListReadModelResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/logical-list-read-model`,
  );
}

export async function getIntakeV6NestingPreview(
  workspaceId: string,
): Promise<IntakeV4NestingPreviewResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/nesting-preview`,
  );
}

export async function getIntakeV6PricingInputPreview(
  workspaceId: string,
): Promise<IntakeV4PricingInputPreviewResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/pricing-input-preview`,
  );
}

export async function getIntakeV6AiInformationalAssistCandidate(
  workspaceId: string,
): Promise<IntakeV4AiInformationalAssistPreviewResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/ai-informational-assist-candidate`,
  );
}

export async function getIntakeV6ProductionHandoffPreview(
  workspaceId: string,
): Promise<IntakeV4ProductionHandoffPreviewResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/production-handoff-preview`,
  );
}

export async function getIntakeV6ProductionTaskDryRun(
  workspaceId: string,
): Promise<IntakeV4ProductionTaskDryRunResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/production-task-dry-run`,
  );
}

export async function getIntakeV6TaskGenerationDryRun(
  workspaceId: string,
): Promise<IntakeV4TaskGenerationDryRunResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/task-generation-dry-run`,
  );
}

export async function getIntakeV6ProductSystemBinding(
  workspaceId: string,
): Promise<IntakeV4ProductSystemBindingResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/product-system-binding`,
  );
}

export async function getIntakeV6TemplateFormContract(
  workspaceId: string,
): Promise<IntakeV4TemplateFormContractResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/template-form-contract`,
  );
}

export async function getIntakeV6RuntimeCaptureReadModel(
  workspaceId: string,
): Promise<IntakeV6RuntimeCaptureReadModelResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/runtime-capture-read-model`,
  );
}

export async function getIntakeV6ProductTruthPromotionPlanner(
  workspaceId: string,
): Promise<IntakeV6ProductTruthPromotionPlannerResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/product-truth-promotion-planner`,
  );
}

/** Template-level modular form contract (Step 5A) — GET only, no workspace mutation. */
export async function getIntakeV6ModularFormContract(
  templateCode: string,
  workspaceId?: string | null,
): Promise<IntakeV6ModularFormContractResponse> {
  const params = new URLSearchParams();
  if (workspaceId) params.set("workspace_id", workspaceId);
  const qs = params.toString();
  const suffix = qs ? `?${qs}` : "";
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/form-contract/${encodeURIComponent(templateCode)}${suffix}`,
  );
}

export async function getIntakeV6OrderBoundTaskReadiness(
  workspaceId: string,
): Promise<IntakeV6OrderBoundTaskReadinessResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/order-bound-task-readiness`,
  );
}

export async function getIntakeV6QuoteHandoffPreview(
  workspaceId: string,
  clientAnalysisHash?: string | null,
): Promise<IntakeV4QuoteHandoffPreviewResponse> {
  const params = new URLSearchParams();
  if (clientAnalysisHash) params.set("client_analysis_hash", clientAnalysisHash);
  const qs = params.toString();
  const suffix = qs ? `?${qs}` : "";
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/quote-handoff-preview${suffix}`,
  );
}

export async function saveIntakeV6InternalDraftQuoteConfirmation(
  workspaceId: string,
  body: { confirmed: boolean },
): Promise<IntakeV4WorkspaceResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/internal-draft-quote-confirmation`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function createIntakeV6DraftQuote(
  workspaceId: string,
  body: IntakeV4CreateDraftQuoteRequest,
): Promise<IntakeV4CreateDraftQuoteResponse> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/create-draft-quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getIntakeV6PricedQuoteDryRun(
  workspaceId: string,
): Promise<IntakeV6PricedQuoteDryRunResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/priced-quote-dry-run`,
  );
}

export async function writeIntakeV6PricedQuote(
  workspaceId: string,
  body: IntakeV6PricedQuoteWriteRequest,
): Promise<IntakeV6PricedQuoteWriteResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/priced-quote/write`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function handoffIntakeV6ToOffer(
  workspaceId: string,
  body: IntakeV6OfferHandoffRequest,
): Promise<IntakeV6OfferHandoffResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/handoff-to-offer`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function createIntakeV6QuoteSnapshotV2(
  workspaceId: string,
  quoteId: number,
  body: IntakeV6QuoteSnapshotV2CreateRequest = {},
): Promise<IntakeV6QuoteSnapshotV2CreateResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/quotes/${quoteId}/snapshot-v2`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function getIntakeV6CommercialSpineState(
  workspaceId: string,
): Promise<IntakeV6CommercialSpineStateResponse> {
  return requestIntakeV6Json(
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(workspaceId)}/commercial-spine-state`,
  );
}

export async function completeIntakeV6PricingReview(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/quotes/${quoteId}/complete-pricing-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function persistIntakeV6OwnerApproval(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/quotes/${quoteId}/owner-approval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function acceptIntakeV6Quote(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/quotes/${quoteId}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function convertIntakeV6QuoteToOrder(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestIntakeV6Json(`${intakeV6ApiBase()}/quotes/${quoteId}/convert-to-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export {
  IntakeV4ApiError as IntakeV6ApiError,
  putIntakeV4SheetFootprintOverride as putIntakeV6SheetFootprintOverride,
  promoteIntakeV4VolumetricLettersV2Template as promoteIntakeV6VolumetricLettersV2Template,
} from "./intakeV4Api";

export type {
  IntakeV4ArtworkFinish as IntakeV6ArtworkFinish,
  IntakeV4AiInformationalAssistPreviewResponse as IntakeV6AiInformationalAssistPreviewResponse,
  IntakeV4AiInformationalSuggestionItem as IntakeV6AiInformationalSuggestionItem,
  IntakeV4AiSuggestionCategory as IntakeV6AiSuggestionCategory,
  IntakeV4CncOperationRow as IntakeV6CncOperationRow,
  IntakeV4CncOperationDryRunCandidate as IntakeV6CncOperationDryRunCandidate,
  IntakeV4CreateDraftQuoteResponse as IntakeV6CreateDraftQuoteResponse,
  IntakeV4EdgeCantOperationDryRunCandidate as IntakeV6EdgeCantOperationDryRunCandidate,
  IntakeV4FaceBackPrepCostDraftResponse as IntakeV6FaceBackPrepCostDraftResponse,
  IntakeV4FinishSetup as IntakeV6FinishSetup,
  IntakeV4MaterialBreakdownResponse as IntakeV6MaterialBreakdownResponse,
  IntakeV4MaterialQuantityRow as IntakeV6MaterialQuantityRow,
  IntakeV4NestingPreviewResponse as IntakeV6NestingPreviewResponse,
  IntakeV4PricingInputPreviewResponse as IntakeV6PricingInputPreviewResponse,
  IntakeV4ProductionHandoffPreviewResponse as IntakeV6ProductionHandoffPreviewResponse,
  IntakeV4ProductSystemBindingResponse as IntakeV6ProductSystemBindingResponse,
  IntakeV4QuoteHandoffPreviewResponse as IntakeV6QuoteHandoffPreviewResponse,
  IntakeV4SheetFootprintOverrideRequest as IntakeV6SheetFootprintOverrideRequest,
  IntakeV4SheetFootprintOverrideResponse as IntakeV6SheetFootprintOverrideResponse,
  IntakeV4SheetQuoteMaterialCandidates as IntakeV6SheetQuoteMaterialCandidates,
  IntakeV4SvgUploadResponse as IntakeV6SvgUploadResponse,
  IntakeV4TaskGenerationDryRunResponse as IntakeV6TaskGenerationDryRunResponse,
  IntakeV4TaskPreviewResponse as IntakeV6TaskPreviewResponse,
  IntakeV4WorkspaceResponse as IntakeV6WorkspaceResponse,
} from "./intakeV4Api";
