import type { ProductTruthDraft, ProductTruthIssue, ProductTruthReadiness, ProductTruthReadinessFlag } from "./productTruthTypes";

const PHASE_3A_PREVIEW_ONLY = "PHASE_3A_PREVIEW_ONLY";

function flag(
  ready: boolean,
  blockerIssues: ProductTruthIssue[],
  warningIssues: ProductTruthIssue[],
  notes: string[] = [],
  extraBlockers: string[] = [],
): ProductTruthReadinessFlag {
  return {
    ready,
    state: ready ? "confirmed" : "blocked",
    blockers: [...extraBlockers, ...blockerIssues.map((issue) => issue.code)],
    warnings: warningIssues.map((issue) => issue.code),
    blockerIssues,
    warningIssues,
    notes,
  };
}

function issuesForGate(issues: ProductTruthIssue[], gate: string): ProductTruthIssue[] {
  return issues.filter((issue) => issue.gates.includes(gate as never));
}

export function evaluateProductTruthDraftReadiness(
  draft: Omit<ProductTruthDraft, "readiness">,
): ProductTruthReadiness {
  const reviewBlockers = issuesForGate(draft.blockers, "review");
  const internalDraftBlockers = issuesForGate(draft.blockers, "internal_draft");
  const commercialBlockers = issuesForGate(draft.blockers, "commercial_proposal");
  const quoteBlockers = issuesForGate(draft.blockers, "quote_snapshot");
  const orderBlockers = issuesForGate(draft.blockers, "order_snapshot");
  const aggregateBlockers = issuesForGate(draft.blockers, "product_aggregate");
  const executionBlockers = issuesForGate(draft.blockers, "execution_plan");

  return {
    readyForReview: flag(reviewBlockers.length === 0, reviewBlockers, draft.warnings),
    productTruthDraftComplete: flag(draft.blockers.length === 0, draft.blockers, draft.warnings),
    readyForInternalDraft: flag(internalDraftBlockers.length === 0, internalDraftBlockers, draft.warnings, [
      "Pure preview only; this does not unlock the existing Intake V6 CTA.",
    ]),
    readyForCommercialProposal: flag(false, commercialBlockers, draft.warnings, [
      "Commercial proposal remains downstream and disabled in Phase 3A.",
    ], [PHASE_3A_PREVIEW_ONLY]),
    readyForQuoteSnapshot: flag(false, quoteBlockers, draft.warnings, [
      "Quote Snapshot is forbidden for this builder-only slice.",
    ], [PHASE_3A_PREVIEW_ONLY]),
    readyForOrderSnapshot: flag(false, orderBlockers, draft.warnings, [
      "Order Snapshot requires an accepted Quote Snapshot later.",
    ], [PHASE_3A_PREVIEW_ONLY]),
    readyForProductAggregate: flag(false, aggregateBlockers, draft.warnings, [
      "ProductAggregate must consume frozen downstream truth later, not this draft.",
    ], [PHASE_3A_PREVIEW_ONLY]),
    readyForExecutionPlan: flag(false, executionBlockers, draft.warnings, [
      "ExecutionPlan remains forbidden until ProductAggregate and Task Graph exist later.",
    ], [PHASE_3A_PREVIEW_ONLY]),
  };
}