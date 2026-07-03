import type { CanonicalOutputBlockPreviewRequest, CanonicalOutputBlockPreviewResponse } from "./canonicalOutputBlockPreview";
import type { RenderPreviewRequest, RenderPreviewResponse, RenderedBlock } from "./outputBlocksPreview";

export const OUTPUTBLOCK_CANONICAL_PREVIEW_FLAG = "VITE_FEATURE_OUTPUTBLOCK_CANONICAL_PREVIEW";

export type CanonicalSelectionReason =
  | "feature_flag_disabled"
  | "invalid_template_id"
  | "missing_block_types"
  | "eligible";

export type OutputBlocksPreviewRouteTarget = "legacy" | "canonical";

export type CanonicalSelectionResult = {
  target: OutputBlocksPreviewRouteTarget;
  reason: CanonicalSelectionReason;
};

export type OutputBlockCanonicalFlagInput = {
  runtimeValue?: unknown;
  envValue?: unknown;
};

function parseBooleanFlag(value: unknown): boolean | null {
  if (typeof value === "boolean") return value;
  if (typeof value !== "string") return null;

  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off", ""].includes(normalized)) return false;

  return null;
}

function toFiniteNumber(value: unknown): number | undefined {
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    return undefined;
  }
  return value;
}

function mapIssuesToMessages(issues: Array<Record<string, unknown>>): string[] {
  return issues.map((issue) => {
    const message = typeof issue.message === "string" ? issue.message : null;
    const code = typeof issue.code === "string" ? issue.code : null;
    if (message) return message;
    if (code) return code;
    return "unknown_issue";
  });
}

function mapCanonicalVariablesToLegacyVariables(
  variablesUsed: Record<string, unknown>
): RenderedBlock["variables_used"] {
  return Object.entries(variablesUsed).map(([name, value]) => ({
    name,
    source_field: "",
    value,
    resolved: value !== null && value !== undefined,
  }));
}

export function resolveOutputBlockCanonicalPreviewFlag(
  input: OutputBlockCanonicalFlagInput = {}
): boolean {
  const runtimeDecision = parseBooleanFlag(input.runtimeValue);
  if (runtimeDecision !== null) {
    return runtimeDecision;
  }

  const envDecision = parseBooleanFlag(input.envValue);
  if (envDecision !== null) {
    return envDecision;
  }

  return false;
}

export function isLegacyRequestEligibleForCanonical(
  request: RenderPreviewRequest
): boolean {
  const templateId = request.template_id;
  const hasValidTemplateId =
    typeof templateId === "number" && Number.isFinite(templateId) && templateId > 0;

  const hasSelectedBlockTypes =
    Array.isArray(request.block_types) && request.block_types.length > 0;

  return hasValidTemplateId && hasSelectedBlockTypes;
}

export function selectOutputBlocksPreviewRoute(
  request: RenderPreviewRequest,
  featureFlagEnabled: boolean
): CanonicalSelectionResult {
  if (!featureFlagEnabled) {
    return { target: "legacy", reason: "feature_flag_disabled" };
  }

  const templateId = request.template_id;
  const hasValidTemplateId =
    typeof templateId === "number" && Number.isFinite(templateId) && templateId > 0;

  if (!hasValidTemplateId) {
    return { target: "legacy", reason: "invalid_template_id" };
  }

  const hasSelectedBlockTypes =
    Array.isArray(request.block_types) && request.block_types.length > 0;

  if (!hasSelectedBlockTypes) {
    return { target: "legacy", reason: "missing_block_types" };
  }

  return { target: "canonical", reason: "eligible" };
}

export function mapLegacyRequestToCanonicalPayload(
  request: RenderPreviewRequest
): CanonicalOutputBlockPreviewRequest {
  const blockTypes = Array.isArray(request.block_types)
    ? request.block_types.filter((value) => typeof value === "string" && value.trim().length > 0)
    : [];

  const quantityCandidate = request.quote_context?.quantity;
  const quantity =
    typeof quantityCandidate === "number" && Number.isFinite(quantityCandidate) && quantityCandidate > 0
      ? Math.floor(quantityCandidate)
      : 1;

  const dimensions = {
    width_mm: toFiniteNumber(request.quote_context?.dimensions?.width_mm),
    height_mm: toFiniteNumber(request.quote_context?.dimensions?.height_mm),
    depth_mm: toFiniteNumber(request.quote_context?.dimensions?.depth_mm),
  };

  return {
    block_types: blockTypes.length > 0 ? blockTypes : undefined,
    context: "quote_preview",
    source_payload: {
      preview: {
        document_type: request.document_type ?? "offer",
        audience: request.audience ?? "client",
        render_mode: request.render_mode ?? "preview",
      },
      quote: {
        client_name: request.quote_context?.client_name ?? "",
        quantity,
      },
      dimensions,
      selection: {
        block_types: blockTypes,
      },
      legacy_reference: {
        template_id: request.template_id ?? null,
        dossier_id: request.dossier_id ?? null,
      },
    },
  };
}

export function normalizeCanonicalResponseToLegacySkeleton(
  canonical: CanonicalOutputBlockPreviewResponse,
  request: RenderPreviewRequest
): RenderPreviewResponse {
  const blocks: RenderedBlock[] = canonical.rendered_blocks.map((block) => ({
    block_id: block.block_id,
    block_type: block.block_type,
    title: block.title ?? "",
    approval_status: block.approval_status,
    rendered_text: block.rendered_text ?? "",
    variables_used: mapCanonicalVariablesToLegacyVariables(block.variables_used),
    warnings: mapIssuesToMessages(block.warnings),
    blockers: mapIssuesToMessages(block.blockers),
  }));

  return {
    persisted: false,
    template_id: request.template_id ?? null,
    dossier_id: request.dossier_id ?? null,
    document_type: request.document_type ?? "offer",
    audience: request.audience ?? "client",
    render_mode: request.render_mode ?? "preview",
    blocks,
    warnings: mapIssuesToMessages(canonical.warnings),
    blockers: mapIssuesToMessages(canonical.blockers),
    trace: {
      source: "canonical_output_blocks_preview",
      no_persist: true,
      changed_entities: [],
      live_changes_affect_accepted_orders: false,
    },
  };
}

export type NormalizeWave2ResponseInput = {
  target: OutputBlocksPreviewRouteTarget;
  request: RenderPreviewRequest;
  legacyResponse?: RenderPreviewResponse;
  canonicalResponse?: CanonicalOutputBlockPreviewResponse;
};

export function normalizeOutputBlocksPreviewResponseSkeleton(
  input: NormalizeWave2ResponseInput
): RenderPreviewResponse {
  if (input.target === "legacy") {
    if (!input.legacyResponse) {
      throw new Error("legacyResponse is required when target is legacy");
    }
    return input.legacyResponse;
  }

  if (!input.canonicalResponse) {
    throw new Error("canonicalResponse is required when target is canonical");
  }

  return normalizeCanonicalResponseToLegacySkeleton(input.canonicalResponse, input.request);
}
