/**
 * Single operator guidance spine for Intake V6.
 * Presentation-only: consolidates next action + progress + attention counts.
 * Domain predicates stay in intakeV6Readiness / final blockers.
 */

import type { IntakeV6StepId, IntakeV6WorkspaceState } from "./intakeV6Contracts";
import { isLayerRoleSetupComplete } from "./intakeV6AnalysisIdentity";
import {
  buildFinalConfirmationBlockers,
  type FinalConfirmationBlocker,
} from "./intakeV6FinalConfirmationBlockers";
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

/** Presentation inventory severity — existing operator vocabulary only. */
export type GuidanceAttentionSeverity = "blocker" | "warning" | "information";

export type GuidanceAttentionIssue = {
  id: string;
  severity: GuidanceAttentionSeverity;
  message: string;
  action?: string | null;
  focusTarget?: string | null;
  tabId?: "finisaje" | "iluminare" | "montaj" | "layers" | null;
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
  blockers: GuidanceAttentionIssue[];
  warnings: GuidanceAttentionIssue[];
  information: GuidanceAttentionIssue[];
  blockerCount: number;
  warningCount: number;
  informationCount: number;
  /** Compact counts for spine / sticky (blockers + warnings only). */
  countsLabel: string | null;
  /** Sticky headline — same numbers as countsLabel. */
  stickySummaryTitle: string | null;
  /** Drawer toggle — severity breakdown including information. */
  drawerToggleLabel: string;
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
  text = text.replace(/\s*propus[ăa] de analyzer\.?/gi, "");
  text = text.replace(/\s*înainte de priced dry-run ready\.?/gi, "");
  text = text.replace(/\s*inainte de priced dry-run ready\.?/gi, "");
  text = text.replace(/\bpriced dry-run ready\b/gi, "");
  text = text.replace(/\bdry-run\b/gi, "");
  text = text.replace(/\banalyzer\b/gi, "");
  text = text.replace(/\s{2,}/g, " ");
  text = text.replace(/\s+([.!?])/g, "$1");
  text = text.replace(/\.\s*\./g, ".");
  text = text.trim();
  if (/compozi[țt]ie/i.test(text) && /confirm/i.test(text)) {
    return "Confirmă compoziția produsului.";
  }
  if (text && !/[.!?]$/.test(text)) text = `${text}.`;
  return text || null;
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
    return [{ id: "operator", label: "Confirmări operator", done: false }];
  }
  return [
    {
      id: "checklist",
      label: `Confirmări (${checklist.done}/${checklist.total})`,
      done: checklist.done >= checklist.total,
    },
  ];
}

export function polishGuidanceCountsLabel(
  blockerCount: number,
  warningCount: number,
): string | null {
  if (blockerCount <= 0 && warningCount <= 0) return null;
  const parts: string[] = [];
  if (blockerCount === 1) parts.push("1 blocant");
  else if (blockerCount > 1) parts.push(`${blockerCount} blocante`);
  if (warningCount === 1) parts.push("1 avertizare");
  else if (warningCount > 1) parts.push(`${warningCount} avertizări`);
  return parts.join(" · ");
}

/** Sticky answers: how much attention is needed? Same counts as footer spine. */
export function buildGuidanceStickySummaryTitle(
  blockerCount: number,
  warningCount: number,
): string {
  const counts = polishGuidanceCountsLabel(blockerCount, warningCount);
  if (!counts) return "Verifică starea secțiunii Configurare";
  return `Configurarea necesită atenție · ${counts}`;
}

/** Drawer toggle — severity breakdown (includes information). */
export function buildGuidanceDrawerToggleLabel(
  blockerCount: number,
  warningCount: number,
  informationCount: number,
): string {
  const parts: string[] = [];
  if (blockerCount === 1) parts.push("1 blocant");
  else if (blockerCount > 1) parts.push(`${blockerCount} blocante`);
  if (warningCount === 1) parts.push("1 avertizare");
  else if (warningCount > 1) parts.push(`${warningCount} avertizări`);
  if (informationCount === 1) parts.push("1 informație");
  else if (informationCount > 1) parts.push(`${informationCount} informații`);
  return parts.length > 0 ? parts.join(" · ") : "Probleme, avertizări și detalii";
}

function dedupeKey(issue: GuidanceAttentionIssue): string {
  return `${issue.severity}:${issue.message.trim().toLowerCase()}`;
}

export function mergeGuidanceAttentionIssues(
  issues: GuidanceAttentionIssue[],
): GuidanceAttentionIssue[] {
  const seen = new Set<string>();
  const out: GuidanceAttentionIssue[] = [];
  for (const issue of issues) {
    const message = issue.message.trim();
    if (!message) continue;
    const key = dedupeKey({ ...issue, message });
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ ...issue, message });
  }
  return out;
}

export function guidanceIssuesFromFinalBlockers(
  finals: FinalConfirmationBlocker[],
): GuidanceAttentionIssue[] {
  return finals.map((b) => ({
    id: `final-${b.id}`,
    severity: b.severity === "blocker" ? "blocker" : "warning",
    message: `${b.section}: ${b.message}`,
    action: b.action,
    focusTarget: b.focusTarget,
    tabId: b.tabId,
  }));
}

/** Map sticky banner issues into guidance inventory (presentation only). */
export function guidanceIssuesFromStickyIssues(
  issues: Array<{
    id: string;
    severity: "blocker" | "warning";
    message: string;
    action?: string | null;
    focusTarget?: string | null;
    tabId?: "finisaje" | "iluminare" | "montaj" | "layers" | null;
  }>,
): GuidanceAttentionIssue[] {
  return issues.map((issue) => ({
    id: issue.id,
    severity: issue.severity,
    message: issue.message,
    action: issue.action ?? null,
    focusTarget: issue.focusTarget ?? null,
    tabId: issue.tabId ?? null,
  }));
}

function partitionAttention(issues: GuidanceAttentionIssue[]): {
  blockers: GuidanceAttentionIssue[];
  warnings: GuidanceAttentionIssue[];
  information: GuidanceAttentionIssue[];
} {
  return {
    blockers: issues.filter((i) => i.severity === "blocker"),
    warnings: issues.filter((i) => i.severity === "warning"),
    information: issues.filter((i) => i.severity === "information"),
  };
}

export function buildIntakeV6OperatorGuidanceModel(input: {
  state: IntakeV6WorkspaceState;
  canContinueFromAnalyzer: boolean;
  /** Confirm-step checklist from handoff overlay. */
  confirmChecklist?: { done: number; total: number } | null;
  confirmDisabledReason?: string | null;
  confirmCanSubmit?: boolean;
  /**
   * Authoritative attention inventory from sticky (Configurare).
   * When set, counts and sticky/drawer labels use this list.
   */
  attentionIssues?: GuidanceAttentionIssue[] | null;
  /** Extra informational rows for drawer only (not sticky headline). */
  informationIssues?: GuidanceAttentionIssue[] | null;
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
    nextAction = canContinue ? null : normalizeGuidanceNextAction(getIntakeV6FirstBlocker(state));
    statusLabel = canContinue ? operatorStatusSemanticRo("ready") : "Straturi incomplete";
  } else if (stepId === "review") {
    progressItems = buildReviewProgress(state);
    canContinue = canContinueFromReviewStep(state);
    continueEnabledLabel = "Continuă la Confirmare";
    nextAction = canContinue ? null : normalizeGuidanceNextAction(getIntakeV6FirstBlocker(state));
    statusLabel = canContinue ? operatorStatusSemanticRo("ready") : "Configurare incompletă";
  } else {
    progressItems = buildConfirmProgress(input.confirmChecklist);
    canContinue = Boolean(input.confirmCanSubmit);
    continueEnabledLabel = "Continuă către ofertă";
    nextAction = canContinue
      ? null
      : normalizeGuidanceNextAction(input.confirmDisabledReason ?? getIntakeV6FirstBlocker(state));
    statusLabel = canContinue ? operatorStatusSemanticRo("ready") : "Confirmare incompletă";
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

  const finals =
    stepId === "review" || stepId === "confirm"
      ? buildFinalConfirmationBlockers({
          payload: state.workspace?.payload,
          finish:
            (state.workspace?.payload?.finish_setup as Record<string, unknown> | undefined) ?? null,
        })
      : [];

  const inventorySeed: GuidanceAttentionIssue[] = [];
  if (input.attentionIssues && input.attentionIssues.length > 0) {
    inventorySeed.push(...input.attentionIssues);
  } else {
    inventorySeed.push(...guidanceIssuesFromFinalBlockers(finals));
  }
  if (input.informationIssues?.length) {
    inventorySeed.push(...input.informationIssues);
  }

  let inventory = mergeGuidanceAttentionIssues(inventorySeed);

  if (!canContinue && nextAction) {
    const already = inventory.some(
      (issue) =>
        issue.severity === "blocker" &&
        issue.message.toLowerCase().includes(nextAction!.toLowerCase().slice(0, 24)),
    );
    if (!already && inventory.filter((i) => i.severity === "blocker").length === 0) {
      inventory = mergeGuidanceAttentionIssues([
        ...inventory,
        {
          id: "guidance-next-action",
          severity: "blocker",
          message: nextAction,
        },
      ]);
    }
  }

  const { blockers, warnings, information } = partitionAttention(inventory);
  const blockerCount = blockers.length;
  const warningCount = warnings.length;
  const informationCount = information.length;
  const countsLabel = polishGuidanceCountsLabel(blockerCount, warningCount);

  return {
    stepId,
    whereAmI,
    statusLabel,
    progressLabel,
    progressDone,
    progressTotal,
    progressItems,
    nextAction,
    blockers,
    warnings,
    information,
    blockerCount,
    warningCount,
    informationCount,
    countsLabel,
    stickySummaryTitle:
      blockerCount + warningCount > 0
        ? buildGuidanceStickySummaryTitle(blockerCount, warningCount)
        : null,
    drawerToggleLabel: buildGuidanceDrawerToggleLabel(
      blockerCount,
      warningCount,
      informationCount,
    ),
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
