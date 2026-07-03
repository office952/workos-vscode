import { previewCanonicalOutputBlocks } from "./canonicalOutputBlockPreview";
import {
  OUTPUTBLOCK_CANONICAL_PREVIEW_FLAG,
  mapLegacyRequestToCanonicalPayload,
  normalizeCanonicalResponseToLegacySkeleton,
  resolveOutputBlockCanonicalPreviewFlag,
  selectOutputBlocksPreviewRoute,
} from "./outputBlocksPreviewWave2Helpers";
import {
  outputBlocksPreviewApi,
  type RenderPreviewRequest,
  type RenderPreviewResponse,
} from "./outputBlocksPreview";

export type OutputBlocksPreviewWave2OrchestratorDeps = {
  legacyRenderPreview: (request: RenderPreviewRequest) => Promise<RenderPreviewResponse>;
  canonicalPreview: ReturnType<typeof previewCanonicalOutputBlocks> extends Promise<infer T>
    ? (request: ReturnType<typeof mapLegacyRequestToCanonicalPayload>) => Promise<T>
    : never;
};

export type OutputBlocksPreviewWave2Options = {
  runtimeFlagValue?: unknown;
  envFlagValue?: unknown;
  deps?: OutputBlocksPreviewWave2OrchestratorDeps;
};

const DEFAULT_FALLBACK_WARNING = "wave2_canonical_fallback_to_legacy";

function getDefaultDeps(): OutputBlocksPreviewWave2OrchestratorDeps {
  return {
    legacyRenderPreview: outputBlocksPreviewApi.renderPreview,
    canonicalPreview: previewCanonicalOutputBlocks,
  };
}

function resolveEnvFlagValue(): unknown {
  return (import.meta as { env?: Record<string, unknown> }).env?.[
    OUTPUTBLOCK_CANONICAL_PREVIEW_FLAG
  ];
}

function annotateLegacyFallback(
  response: RenderPreviewResponse,
  error: unknown
): RenderPreviewResponse {
  const detail = error instanceof Error && error.message ? error.message : "unknown_error";
  const fallbackWarning = `${DEFAULT_FALLBACK_WARNING}:${detail}`;

  return {
    ...response,
    warnings: [...response.warnings, fallbackWarning],
    trace: {
      ...response.trace,
      source: `${response.trace.source}|canonical_fallback`,
    },
  };
}

export async function renderOutputBlocksPreviewWave2(
  request: RenderPreviewRequest,
  options: OutputBlocksPreviewWave2Options = {}
): Promise<RenderPreviewResponse> {
  const deps = options.deps ?? getDefaultDeps();

  const featureFlagEnabled = resolveOutputBlockCanonicalPreviewFlag({
    runtimeValue: options.runtimeFlagValue,
    envValue: options.envFlagValue ?? resolveEnvFlagValue(),
  });

  const routeSelection = selectOutputBlocksPreviewRoute(request, featureFlagEnabled);
  if (routeSelection.target === "legacy") {
    return deps.legacyRenderPreview(request);
  }

  try {
    const canonicalPayload = mapLegacyRequestToCanonicalPayload(request);
    const canonicalResponse = await deps.canonicalPreview(canonicalPayload);
    return normalizeCanonicalResponseToLegacySkeleton(canonicalResponse, request);
  } catch (error) {
    const legacyResponse = await deps.legacyRenderPreview(request);
    return annotateLegacyFallback(legacyResponse, error);
  }
}
