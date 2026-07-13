import type { IntakeV6StepId, IntakeV6WorkspaceState } from "./intakeV6Contracts";
import {
  hasUnsavedAnalysis,
  isAnalysisPersisted,
  isAnalysisReadyForReview,
  isLayerRoleSetupComplete,
} from "./intakeV6AnalysisIdentity";

export function isFinishSetupConfirmed(payload: Record<string, unknown> | undefined): boolean {
  const finish = payload?.finish_setup;
  if (finish == null || typeof finish !== "object" || Array.isArray(finish)) return false;
  return (finish as Record<string, unknown>).confirmed === true;
}

export function hasPersistedAnalysis(payload: Record<string, unknown> | undefined): boolean {
  return isAnalysisPersisted(payload);
}

export function isProductCompositionConfirmed(payload: Record<string, unknown> | undefined): boolean {
  const confirmation = payload?.product_composition_confirmed;
  if (confirmation == null || typeof confirmation !== "object" || Array.isArray(confirmation)) return false;
  return (confirmation as Record<string, unknown>).confirmed === true;
}

export function isOfferScopeConfirmed(payload: Record<string, unknown> | undefined): boolean {
  const scope = payload?.offer_scope;
  const confirmation = payload?.offer_scope_confirmed;
  if (scope == null && confirmation == null) return true;
  if (confirmation == null || typeof confirmation !== "object" || Array.isArray(confirmation)) return false;
  if ((confirmation as Record<string, unknown>).confirmed !== true) return false;
  return isOfferScopeValid(payload);
}

export function isOfferScopeValid(payload: Record<string, unknown> | undefined): boolean {
  const scope = payload?.offer_scope;
  if (scope == null || typeof scope !== "object" || Array.isArray(scope)) {
    return confirmationOnlyOfferScope(payload);
  }
  const mode = (scope as Record<string, unknown>).mode;
  const soldModules = (scope as Record<string, unknown>).sold_modules;
  if (mode === "full_product") return true;
  if (mode !== "component_subset") return false;
  if (!Array.isArray(soldModules) || soldModules.length === 0) return false;
  return soldModules.every(
    (code) =>
      code === "FACE" ||
      code === "RETURN-CANT" ||
      code === "BACK" ||
      code === "LIGHTING" ||
      code === "ELECTRICAL",
  );
}

function confirmationOnlyOfferScope(payload: Record<string, unknown> | undefined): boolean {
  const confirmation = payload?.offer_scope_confirmed;
  if (confirmation == null) return true;
  return typeof confirmation === "object" && !Array.isArray(confirmation) && confirmation.confirmed === true;
}

export function canAccessIntakeV6Step(state: IntakeV6WorkspaceState, step: IntakeV6StepId): boolean {
  if (step === "layers") return true;

  if (step === "review" || step === "confirm") {
    return isAnalysisReadyForReview(state);
  }

  return false;
}

export function getIntakeV6FirstBlocker(state: IntakeV6WorkspaceState): string | null {
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

  if (readiness === "product_composition_not_confirmed" && !isProductCompositionConfirmed(payload)) {
    return "Confirmă compoziția produsului propusă de analyzer.";
  }

  if (readiness === "offer_scope_not_confirmed" || !isOfferScopeConfirmed(payload)) {
    if (!isOfferScopeValid(payload)) {
      return "Selectează cel puțin o componentă pentru scope parțial.";
    }
    return "Confirmă ce producem (produs complet sau componente selectate).";
  }

  if (state.currentStep === "confirm" && !isFinishSetupConfirmed(payload)) {
    return "Confirmă finisajele în pasul Review.";
  }

  if (state.currentStep === "confirm" && !isProductCompositionConfirmed(payload)) {
    return "Confirmă compoziția produsului în pasul Review.";
  }

  if (readiness && readiness !== "ready_for_quote_preview" && state.currentStep === "confirm") {
    return `Workspace nepregătit: ${readiness}`;
  }

  return null;
}

export function isIntakeV6ReadyForQuotePreview(state: IntakeV6WorkspaceState): boolean {
  return (
    isAnalysisReadyForReview(state) &&
    state.workspace?.readiness_status === "ready_for_quote_preview" &&
    isProductCompositionConfirmed(state.workspace?.payload) &&
    isOfferScopeConfirmed(state.workspace?.payload) &&
    isFinishSetupConfirmed(state.workspace?.payload)
  );
}

export function canContinueFromReviewStep(state: IntakeV6WorkspaceState): boolean {
  return (
    isAnalysisReadyForReview(state) &&
    isProductCompositionConfirmed(state.workspace?.payload) &&
    isOfferScopeConfirmed(state.workspace?.payload) &&
    isFinishSetupConfirmed(state.workspace?.payload)
  );
}
