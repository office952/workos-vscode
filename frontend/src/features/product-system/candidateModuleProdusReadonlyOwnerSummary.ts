import type { CandidateModuleProdusCompletenessAssessment } from "./candidateModuleProdusReadonlyCompleteness";
import type { CandidateModuleProdusContractDriftAssessment } from "./candidateModuleProdusReadonlyCompleteness";
import type { CandidateModuleProdusDossierAlignmentAssessment } from "./candidateModuleProdusReadonlyDossierAlignment";

export type CandidateModuleProdusOwnerStatusLevel =
  | "SAFE_READONLY"
  | "NEEDS_LIVE_ROWS"
  | "PARTIAL_LIVE_ROWS"
  | "BLOCKED";

export type CandidateModuleProdusOwnerNextDecision =
  | "NONE_NOW"
  | "REVIEW_ONLY"
  | "OWNER_GO_REQUIRED_FOR_NEXT_STEP";

export type CandidateModuleProdusOwnerVisibleCheck = {
  label: string;
  value: string;
};

export type CandidateModuleProdusOwnerSummary = {
  statusTitle: string;
  statusLevel: CandidateModuleProdusOwnerStatusLevel;
  oneSentenceSummary: string;
  canBeUsedInWorkIntake: false;
  canPrice: false;
  canCreateQuote: false;
  canCreateOrder: false;
  canMaterializeTasks: false;
  nextOwnerDecisionNeeded: CandidateModuleProdusOwnerNextDecision;
  ownerVisibleChecks: CandidateModuleProdusOwnerVisibleCheck[];
};

function isBlockedState(
  completeness: CandidateModuleProdusCompletenessAssessment,
  drift: CandidateModuleProdusContractDriftAssessment,
  dossier: CandidateModuleProdusDossierAlignmentAssessment
): boolean {
  return (
    completeness.sourceMode === "blocked_invalid_live_state" ||
    drift.driftState === "BLOCKED_INVALID_LIVE_STATE" ||
    dossier.overallAlignmentState === "BLOCKED_INVALID_LIVE_STATE" ||
    dossier.overallAlignmentState === "BLOCKED_DOSSIER_ACTIVATION_LEAK"
  );
}

export function buildCandidateModuleProdusOwnerSummary(
  completeness: CandidateModuleProdusCompletenessAssessment,
  drift: CandidateModuleProdusContractDriftAssessment,
  dossier: CandidateModuleProdusDossierAlignmentAssessment
): CandidateModuleProdusOwnerSummary {
  const liveRowsLabel = `${completeness.foundRowCount}/${completeness.expectedRowCount}`;
  const dossierContractLabel = `${dossier.dossierContractCount}/${dossier.expectedCount}`;

  const baseChecks: CandidateModuleProdusOwnerVisibleCheck[] = [
    { label: "Template set exists as readonly contract", value: "yes" },
    { label: "Live seeded rows", value: liveRowsLabel },
    { label: "Dossier contract", value: dossierContractLabel },
    { label: "Activation", value: "blocked until owner GO" },
    { label: "Work Intake exposure", value: "no" },
    { label: "Pricing / Quote / Order / Execution", value: "no" },
  ];

  if (isBlockedState(completeness, drift, dossier)) {
    return {
      statusTitle: "Blocked — owner review needed",
      statusLevel: "BLOCKED",
      oneSentenceSummary:
        "Blocked: neactivat readonly set detected active row or activation leak. Do not treat as safe or complete.",
      canBeUsedInWorkIntake: false,
      canPrice: false,
      canCreateQuote: false,
      canCreateOrder: false,
      canMaterializeTasks: false,
      nextOwnerDecisionNeeded: "REVIEW_ONLY",
      ownerVisibleChecks: baseChecks,
    };
  }

  if (completeness.sourceMode === "partial_live_inactive") {
    return {
      statusTitle: "Partial live rows — not complete",
      statusLevel: "PARTIAL_LIVE_ROWS",
      oneSentenceSummary:
        "Partial live rows present. Do not treat as complete; set remains neactivat and not exposed in Work Intake.",
      canBeUsedInWorkIntake: false,
      canPrice: false,
      canCreateQuote: false,
      canCreateOrder: false,
      canMaterializeTasks: false,
      nextOwnerDecisionNeeded: "REVIEW_ONLY",
      ownerVisibleChecks: baseChecks,
    };
  }

  if (completeness.sourceMode === "live_seeded_inactive") {
    return {
      statusTitle: "Live inactive rows complete — still not offerable",
      statusLevel: "SAFE_READONLY",
      oneSentenceSummary:
        "All 7 inactive catalog rows exist, but set is neactivat, not exposed in Work Intake, and cannot price, quote, order, or execute.",
      canBeUsedInWorkIntake: false,
      canPrice: false,
      canCreateQuote: false,
      canCreateOrder: false,
      canMaterializeTasks: false,
      nextOwnerDecisionNeeded: "OWNER_GO_REQUIRED_FOR_NEXT_STEP",
      ownerVisibleChecks: baseChecks,
    };
  }

  return {
    statusTitle: "Safe readonly contract",
    statusLevel: "NEEDS_LIVE_ROWS",
    oneSentenceSummary:
      "Noul set este definit ca structura readonly in cod, dar nu are inca randuri live in catalog. Neactivat si neexpus in Work Intake.",
    canBeUsedInWorkIntake: false,
    canPrice: false,
    canCreateQuote: false,
    canCreateOrder: false,
    canMaterializeTasks: false,
    nextOwnerDecisionNeeded: "OWNER_GO_REQUIRED_FOR_NEXT_STEP",
    ownerVisibleChecks: baseChecks,
  };
}

export function candidateModuleProdusOwnerStatusTone(level: CandidateModuleProdusOwnerStatusLevel): string {
  switch (level) {
    case "SAFE_READONLY":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-200";
    case "NEEDS_LIVE_ROWS":
      return "border-cyan-700/40 bg-cyan-900/20 text-cyan-200";
    case "PARTIAL_LIVE_ROWS":
      return "border-amber-700/40 bg-amber-900/20 text-amber-200";
    case "BLOCKED":
      return "border-rose-700/40 bg-rose-900/20 text-rose-200";
  }
}

export const CANDIDATE_MODULE_OWNER_FORBIDDEN_WORDING = [
  "ready to quote",
  "offerable",
  "active product",
  "available in Work Intake",
  "ready for use",
  "can quote",
  "live product",
] as const;
