import type { IntakeV4WorkspaceState } from "./intakeV4Contracts";
import type { IntakeV4StepId } from "./intakeV4Contracts";
import {
  hasUnsavedAnalysis,
  isAnalysisPersisted,
  isAnalysisReadyForReview,
  isLayerRoleSetupComplete,
} from "./intakeV4AnalysisIdentity";

export function isFinishSetupConfirmed(payload: Record<string, unknown> | undefined): boolean {
  const finish = payload?.finish_setup;
  if (finish == null || typeof finish !== "object" || Array.isArray(finish)) return false;
  return (finish as Record<string, unknown>).confirmed === true;
}

/** @deprecated use isAnalysisPersisted from intakeV4AnalysisIdentity */
export function hasPersistedAnalysis(payload: Record<string, unknown> | undefined): boolean {
  return isAnalysisPersisted(payload);
}

export function canAccessIntakeV4Step(state: IntakeV4WorkspaceState, step: IntakeV4StepId): boolean {
  if (step === "layers") return true;

  if (step === "review" || step === "confirm") {
    return isAnalysisReadyForReview(state);
  }

  return false;
}

export function getIntakeV4FirstBlocker(state: IntakeV4WorkspaceState): string | null {
  const payload = state.workspace?.payload;
  const readiness = state.workspace?.readiness_status;

  if (state.analyzerStatus === "analyzing" || state.phase === "persisting") {
    return "Analiza SVG este în curs…";
  }

  if (hasUnsavedAnalysis(state)) {
    return "Analiza SVG nu este salvată sau fișierul s-a schimbat — salvează din Pas 1.";
  }

  if (!isAnalysisPersisted(payload)) {
    return "Încarcă, analizează și salvează un fișier SVG.";
  }

  if (!isLayerRoleSetupComplete(payload)) {
    return "Confirmă rolul pentru toate straturile.";
  }

  if (readiness === "layer_roles_incomplete") {
    return "Confirmă rolul pentru toate straturile.";
  }

  if (state.currentStep === "confirm" && !isFinishSetupConfirmed(payload)) {
    return "Confirmă finisajele în pasul Review.";
  }

  if (readiness && readiness !== "ready_for_quote_preview" && state.currentStep === "confirm") {
    return `Workspace nepregătit: ${readiness}`;
  }

  return null;
}

export function isIntakeV4ReadyForQuotePreview(state: IntakeV4WorkspaceState): boolean {
  return (
    isAnalysisReadyForReview(state) &&
    state.workspace?.readiness_status === "ready_for_quote_preview" &&
    isFinishSetupConfirmed(state.workspace?.payload)
  );
}

export function canContinueFromReviewStep(state: IntakeV4WorkspaceState): boolean {
  return isAnalysisReadyForReview(state) && isFinishSetupConfirmed(state.workspace?.payload);
}
