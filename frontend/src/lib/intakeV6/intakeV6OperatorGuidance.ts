/**
 * Single operator guidance spine for Intake V6.
 * Presentation-only: consolidates next action + progress + counts.
 * Domain predicates stay in intakeV6Readiness / final blockers.
 */

import type { IntakeV6StepId, IntakeV6WorkspaceState } from "./intakeV6Contracts";
import { isLayerRoleSetupComplete } from "./intakeV6AnalysisIdentity";
import { buildFinalConfirmationBlockers } from "./intakeV6FinalConfirmationBlockers";
import {
  canContinueFromReviewStep,
  getIntakeV6FirstBlocker,
  isFinishSetupConfirmed,
  isOfferScopeConfirmed,
  isProductCompositionConfirmed,
} from "./intakeV6Readiness";
import {
  INTAKE_V6_VISIBLE_PROGRESS_STEPS,
  resolveIntakeV6VisibleProgressStep,
} from "./intakeV6OperatorProgressSteps";
import { operatorStatusSemanticRo } from "./intakeV6OperatorVocabulary";

export type IntakeV6GuidanceProgressItem = {
  id: string;
  label: string;
  done: boolean;
};

export type IntakeV6OperatorGuidanceModel = {
  stepId: IntakeV6StepId;
  whereAmI: string;
  /** High-level status for the current step. */
  statusLabel: string;
  /** e.g. "2 / 4 confirmări" */
  progressLabel: string | null;
  progressDone: number;
  progressTotal: number;
  progressItems: IntakeV6GuidanceProgressItem[];
  /** Single authoritative next action (footer primary). */
  nextAction: string | null;
  blockerCount: number;
  warningCount: number;
  /** Compact counts for chrome. */
  countsLabel: string | null;
  canContinue: boolean;
  continueEnabledLabel: string;
};

function whereLabel(step: IntakeV6StepId): string {
  const visible = resolveIntakeV6VisibleProgressStep(step);
  return INTAKE_V6_VISIBLE_PROGRESS_STEPS.find((s) => s.id === visible)?.label ?? "Intake V6";
}

/** Normalize legacy / technical phrasing in next-action copy (presentation only). */
export function normalizeGuidanceNextAction(raw: string | null | undefined): string | null {
  if (raw == null) return null;
  let text = String(raw).trim();
  if (!text) return null;
  text = text.replace(/\s*propusă de analyzer\.?/gi, ".");
  text = text.replace(/\s*propusa de analyzer\.?/gi, ".");
  text = text.replace(/\banalyzer\b/gi, "sistem");
  text = text.replace(/\.\s*\./g, ".");
  text = text.replace(/\s+/g, " ").trim();
  return text;
}

function buildLayersProgress(state: IntakeV6WorkspaceState): IntakeV6GuidanceProgressItem[] {
  const chips = state.layerChips ?? [];
  const total = chips.length;
  const confirmed = chips.filter((c) => c.status === "confirmed" || c.status === "ignored").length;
  const payloadComplete = isLayerRoleSetupComplete(state.workspace?.payload);
  return [
    {
      id: "analysis",
      label: "Analiză SVG",
      done: Boolean(state.workspace?.payload?.svg_analysis_json) || state.analyzerStatus === "ready",
    },
    {
      id: "roles",
      label: total > 0 ? `Roluri straturi (${confirmed}/${total})` : "Roluri straturi",
      done: payloadComplete || (total > 0 && confirmed >= total),
    },
  ];
}

function buildReviewProgress(state: IntakeV6WorkspaceState): IntakeV6GuidanceProgressItem[] {
  const payload = state.workspace?.payload;
  return [
    {
      id: "composition",
      label: "Compoziție produs",
      done: isProductCompositionConfirmed(payload),
    },
    {
      id: "offer_scope",
      label: "Ce producem",
      done: isOfferScopeConfirmed(payload),
    },
    {
      id: "finish_setup",
      label: "Finisaje confirmate",
      done: isFinishSetupConfirmed(payload),
    },
  ];
}

function buildConfirmProgress(checklist?: { done: number; total: number } | null): IntakeV6GuidanceProgressItem[] {
  if (!checklist || checklist.total <= 0) {
    return [
      { id: "operator", label: "Confirmări operator", done: false },
    ];
  }
  return [
    {
      id: "checklist",
      label: `Confirmări (${checklist.done}/${checklist.total})`,
      done: checklist.done >= checklist.total,
    },
  ];
}

function polishCountsLabel(blockerCount: number, warningCount: number): string | null {
  if (blockerCount <= 0 && warningCount <= 0) return null;
  const parts: string[] = [];
  if (blockerCount === 1) parts.push("1 blocant");
  else if (blockerCount > 1) parts.push(`${blockerCount} blocante`);
  if (warningCount === 1) parts.push("1 avertizare");
  else if (warningCount > 1) parts.push(`${warningCount} avertizări`);
  return parts.join(" · ");
}

export function buildIntakeV6OperatorGuidanceModel(input: {
  state: IntakeV6WorkspaceState;
  canContinueFromAnalyzer: boolean;
  /** Confirm-step checklist from handoff overlay. */
  confirmChecklist?: { done: number; total: number } | null;
  confirmDisabledReason?: string | null;
  confirmCanSubmit?: boolean;
  /** Extra warning/blocker counts from Review sticky (optional overlay). */
  reviewBlockerCount?: number;
  reviewWarningCount?: number;
}): IntakeV6OperatorGuidanceModel {
  const { state } = input;
  const stepId = state.currentStep;
  const whereAmI = whereLabel(stepId);

  let progressItems: IntakeV6GuidanceProgressItem[] = [];
  let canContinue = false;
  let continueEnabledLabel = "Continuă";
  let nextAction: string | null = null;
  let statusLabel = operatorStatusSemanticRo("needs_operator");

  if (stepId === "layers") {
    progressItems = buildLayersProgress(state);
    canContinue = input.canContinueFromAnalyzer;
    continueEnabledLabel = "Continuă la Configurare";
    nextAction = canContinue
      ? null
      : normalizeGuidanceNextAction(getIntakeV6FirstBlocker(state));
    statusLabel = canContinue
      ? operatorStatusSemanticRo("ready")
      : "Straturi incomplete";
  } else if (stepId === "review") {
    progressItems = buildReviewProgress(state);
    canContinue = canContinueFromReviewStep(state);
    continueEnabledLabel = "Continuă la Confirmare";
    nextAction = canContinue
      ? null
      : normalizeGuidanceNextAction(getIntakeV6FirstBlocker(state));
    statusLabel = canContinue
      ? operatorStatusSemanticRo("ready")
      : "Configurare incompletă";
  } else {
    progressItems = buildConfirmProgress(input.confirmChecklist);
    canContinue = Boolean(input.confirmCanSubmit);
    continueEnabledLabel = "Continuă către ofertă";
    nextAction = canContinue
      ? null
      : normalizeGuidanceNextAction(input.confirmDisabledReason ?? getIntakeV6FirstBlocker(state));
    statusLabel = canContinue
      ? operatorStatusSemanticRo("ready")
      : "Confirmare incompletă";
  }

  const checklist = input.confirmChecklist;
  const progressDone =
    stepId === "confirm" && checklist && checklist.total > 0
      ? checklist.done
      : progressItems.filter((p) => p.done).length;
  const progressTotal =
    stepId === "confirm" && checklist && checklist.total > 0
      ? checklist.total
      : progressItems.length;
  const progressLabel =
    progressTotal > 0 ? `${progressDone} / ${progressTotal} confirmări` : null;

  // Counts: final confirmation blockers on review/confirm + optional review overlay
  let blockerCount = Math.max(0, input.reviewBlockerCount ?? 0);
  let warningCount = Math.max(0, input.reviewWarningCount ?? 0);

  if (stepId === "review" || stepId === "confirm") {
    const finals = buildFinalConfirmationBlockers({
      payload: state.workspace?.payload,
      finish: (state.workspace?.payload?.finish_setup as Record<string, unknown> | undefined) ?? null,
    });
    const fromFinalBlockers = finals.filter((f) => f.severity === "blocker").length;
    const fromFinalWarnings = finals.filter((f) => f.severity === "warning").length;
    // Prefer overlay counts when provided (includes handoff surfacing); else final gates
    if (input.reviewBlockerCount == null && input.reviewWarningCount == null) {
      blockerCount = fromFinalBlockers;
      warningCount = fromFinalWarnings;
    } else {
      // Ensure composition/segmented gates are never under-counted vs overlay
      blockerCount = Math.max(blockerCount, fromFinalBlockers);
      warningCount = Math.max(warningCount, fromFinalWarnings);
    }
  } else if (stepId === "layers" && nextAction) {
    blockerCount = Math.max(blockerCount, 1);
  }

  if (!canContinue && nextAction && blockerCount === 0) {
    blockerCount = 1;
  }

  return {
    stepId,
    whereAmI,
    statusLabel,
    progressLabel,
    progressDone,
    progressTotal,
    progressItems,
    nextAction,
    blockerCount,
    warningCount,
    countsLabel: polishCountsLabel(blockerCount, warningCount),
    canContinue,
    continueEnabledLabel,
  };
}

/** Sticky banner should not repeat the footer next-action paragraph. */
export function guidanceStickySuppressesCompactDetail(
  guidance: IntakeV6OperatorGuidanceModel,
): boolean {
  return Boolean(guidance.nextAction);
}
