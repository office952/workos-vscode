import {
  collectArtworkUndecidedWarnings,
  formatQuoteHandoffBlocker,
} from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";

export const INTAKE_V6_CONFIRM_STATUS_TITLE = "Status configurație";

export type IntakeV6ConfirmConsolidatedStatusTier =
  | "blocked"
  | "attention"
  | "ready"
  | "informational";

export interface IntakeV6ConfirmConsolidatedStatusDisplay {
  tier: IntakeV6ConfirmConsolidatedStatusTier;
  title: string;
  headline: string;
  observations: string[];
  indicatorLabel: string;
}

const MAX_OBSERVATIONS = 3;

function pushObservation(observations: string[], message: string): void {
  if (!message || observations.length >= MAX_OBSERVATIONS) return;
  if (observations.includes(message)) return;
  observations.push(message);
}

export function buildIntakeV6ConfirmConsolidatedStatus(input: {
  loading: boolean;
  fetchError?: string | null;
  finishSetupIncomplete: boolean;
  effectiveHandoffAllowed: boolean;
  bindingBlockers: string[];
  allFatalBlockers: string[];
  artworkNeedsDecision: boolean;
  reviewWarnings: string[];
  containsMissingPrices: boolean;
  operatorConfirmationComplete: boolean;
  confirmInternalDraft: boolean;
  confirmDraftBoundary: boolean;
  showHandoffCheckboxes: boolean;
  checklistProgress: { done: number; total: number };
  modularPendingCount: number;
  formatBlocker?: (code: string) => string;
}): IntakeV6ConfirmConsolidatedStatusDisplay {
  const formatBlocker = input.formatBlocker ?? formatQuoteHandoffBlocker;
  const observations: string[] = [];

  if (input.loading) {
    return {
      tier: "informational",
      title: INTAKE_V6_CONFIRM_STATUS_TITLE,
      headline: "Verific configurația curentă…",
      observations: [],
      indicatorLabel: "In curs",
    };
  }

  if (input.fetchError) {
    return {
      tier: "blocked",
      title: INTAKE_V6_CONFIRM_STATUS_TITLE,
      headline: "Previzualizarea confirmării nu este disponibilă.",
      observations: ["Reîncarcă pasul sau revino după ce datele sunt sincronizate."],
      indicatorLabel: "Blocat",
    };
  }

  if (input.finishSetupIncomplete) {
    pushObservation(observations, "Finalizează finisajele în Review înainte de draft.");
  }

  for (const blocker of input.bindingBlockers) {
    pushObservation(observations, formatBlocker(blocker));
  }

  if (!input.effectiveHandoffAllowed) {
    for (const blocker of input.allFatalBlockers) {
      pushObservation(observations, formatBlocker(blocker));
    }
  }

  const artworkWarnings = collectArtworkUndecidedWarnings(input.reviewWarnings);
  for (const warning of artworkWarnings) {
    pushObservation(observations, warning);
  }

  if (input.artworkNeedsDecision && artworkWarnings.length === 0) {
    pushObservation(observations, "Există finisaje artwork care necesită decizie în Review.");
  }

  if (input.containsMissingPrices) {
    pushObservation(observations, "Calculul conține linii fără tarif — verifică costul intern.");
  }

  if (input.modularPendingCount > 0) {
    pushObservation(
      observations,
      `${input.modularPendingCount} component${input.modularPendingCount === 1 ? "" : "e"} produs necesită completare.`,
    );
  }

  if (!input.operatorConfirmationComplete || !input.confirmInternalDraft) {
    pushObservation(observations, "Confirmă finisajele și datele de ofertare pentru draft intern.");
  }

  if (input.showHandoffCheckboxes && !input.confirmDraftBoundary) {
    pushObservation(observations, "Confirmă limitele draftului intern (fără comandă / execuție / stoc).");
  }

  const hasBlockers =
    input.finishSetupIncomplete ||
    input.bindingBlockers.length > 0 ||
    !input.effectiveHandoffAllowed;

  if (hasBlockers) {
    return {
      tier: "blocked",
      title: INTAKE_V6_CONFIRM_STATUS_TITLE,
      headline: "Configurația nu este pregătită pentru confirmare.",
      observations,
      indicatorLabel: "Blocat",
    };
  }

  const checklistComplete =
    input.checklistProgress.total > 0 &&
    input.checklistProgress.done >= input.checklistProgress.total;

  if (observations.length > 0) {
    return {
      tier: "attention",
      title: INTAKE_V6_CONFIRM_STATUS_TITLE,
      headline: "Necesită verificare înainte de confirmare.",
      observations,
      indicatorLabel: "Atenție",
    };
  }

  if (checklistComplete && input.effectiveHandoffAllowed) {
    return {
      tier: "ready",
      title: INTAKE_V6_CONFIRM_STATUS_TITLE,
      headline: "Pregătit pentru confirmare.",
      observations: ["Poți continua cu confirmările de draft intern de mai jos."],
      indicatorLabel: "Pregătit",
    };
  }

  return {
    tier: "informational",
    title: INTAKE_V6_CONFIRM_STATUS_TITLE,
    headline: "Recapitulare configurație înainte de draft intern.",
    observations: observations.length > 0 ? observations : ["Revizuiește sumarul produsului și confirmările."],
    indicatorLabel: "Recapitulare",
  };
}
