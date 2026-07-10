import type { IntakeV6WorkspaceState } from "./intakeV6Contracts";
import { hasUnsavedAnalysis, isAnalysisReadyForReview } from "./intakeV6AnalysisIdentity";
import {
  buildReviewHeaderStatus,
  type BuildReviewHeaderStatusInput,
  type ReviewHeaderStatusModel,
} from "./intakeV6ReviewHeaderStatus";

export type WorkspaceHeaderStatusOverlay = Partial<BuildReviewHeaderStatusInput> & {
  secondaryWarnings?: readonly string[];
};

export function buildWorkspaceHeaderStatus(
  state: IntakeV6WorkspaceState,
  overlay: WorkspaceHeaderStatusOverlay = {},
): ReviewHeaderStatusModel {
  const layersTotal = overlay.layersTotal ?? state.layerChips.length;
  const layersConfirmed =
    overlay.layersConfirmed ??
    state.layerChips.filter((chip) => chip.status === "confirmed" || chip.status === "ignored").length;
  const pendingLayers = state.layerChips.filter((chip) => chip.status === "pending").length;

  const analysisReady = overlay.analysisReady ?? isAnalysisReadyForReview(state);
  const svgReady =
    overlay.svgReady ??
    (state.phase === "svg_ready" || analysisReady || Boolean(state.workspace?.payload?.svg_analysis_json));

  let pendingConfirmationCount = overlay.pendingConfirmationCount ?? 0;
  if (state.currentStep === "layers" && pendingLayers > 0) {
    pendingConfirmationCount += pendingLayers;
  }

  const status = buildReviewHeaderStatus({
    loading: overlay.loading,
    analysisReady,
    svgReady,
    containsMissingPrices: overlay.containsMissingPrices,
    layersConfirmed,
    layersTotal,
    artworkTotal: overlay.artworkTotal ?? 0,
    artworkConfigured: overlay.artworkConfigured ?? overlay.artworkConfirmed ?? 0,
    operatorConfirmationMissing: overlay.operatorConfirmationMissing,
    reviewWarnings: overlay.reviewWarnings,
    surfacing: overlay.surfacing ?? { showBanner: false, reasons: [], actions: [] },
    pendingSave: overlay.pendingSave,
    pendingConfirmationCount,
    currentStep: state.currentStep,
    widthMm: overlay.widthMm,
    heightMm: overlay.heightMm,
    perimeterM: overlay.perimeterM,
  });

  const svgFileName = state.svg?.fileName;
  if (svgFileName) {
    const svgRow = status.details.find((row) => row.id === "svg");
    if (svgRow && !svgRow.value.includes(svgFileName)) {
      svgRow.value = `${svgRow.value} · ${svgFileName}`;
    }
  }

  return status;
}

export function shouldShowIntakeV6SmartBanner(
  state: IntakeV6WorkspaceState,
  firstBlocker?: string | null,
): boolean {
  if (state.phase === "loading" || state.analyzerStatus === "analyzing") return true;
  if (hasUnsavedAnalysis(state)) return true;
  // Review step uses the operator blocker banner under tabs — avoid duplicate handoff strip.
  if (firstBlocker && state.currentStep !== "layers" && state.currentStep !== "review") return true;
  return false;
}
