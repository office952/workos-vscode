import { describe, expect, it } from "vitest";
import { buildProductTruthDraft } from "./productTruthDraftBuilder";
import { evaluateProductTruthDraftReadiness } from "./productTruthReadiness";
import {
  gradiCuratCompleteReviewLikeFixture,
  gradiCuratConfirmedRolesFixture,
  gradiCuratExecutionOnlyElectricalFixture,
  gradiCuratUnconfirmedFixture,
} from "./productTruthFixtures";

function withoutReadiness(draft: ReturnType<typeof buildProductTruthDraft>) {
  return {
    metadata: draft.metadata,
    sourceSvg: draft.sourceSvg,
    geometry: draft.geometry,
    layers: draft.layers,
    components: draft.components,
    blockers: draft.blockers,
    warnings: draft.warnings,
    audit: draft.audit,
  };
}

describe("evaluateProductTruthDraftReadiness", () => {
  it("summarizes review blockers and warning issue objects", () => {
    const draft = buildProductTruthDraft(gradiCuratUnconfirmedFixture);
    const readiness = evaluateProductTruthDraftReadiness(withoutReadiness(draft));

    expect(readiness.readyForReview.ready).toBe(false);
    expect(readiness.readyForReview.blockers).toContain("LAYER_ROLES_INCOMPLETE");
    expect(readiness.readyForReview.blockerIssues[0].code).toBe("LAYER_ROLES_INCOMPLETE");
    expect(readiness.readyForReview.warningIssues.length).toBeGreaterThan(0);
  });

  it("can mark Product Truth draft complete while downstream remains disabled", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);
    const readiness = evaluateProductTruthDraftReadiness(withoutReadiness(draft));

    expect(readiness.productTruthDraftComplete.ready).toBe(true);
    expect(readiness.productTruthDraftComplete.blockers).toEqual([]);
    expect(readiness.readyForCommercialProposal.ready).toBe(false);
    expect(readiness.readyForCommercialProposal.blockers).toContain("PHASE_3A_PREVIEW_ONLY");
  });

  it("keeps commercial proposal blocked by Phase 3A and commercial blockers", () => {
    const draft = buildProductTruthDraft(gradiCuratConfirmedRolesFixture);
    const readiness = evaluateProductTruthDraftReadiness(withoutReadiness(draft));

    expect(readiness.readyForCommercialProposal.ready).toBe(false);
    expect(readiness.readyForCommercialProposal.blockers[0]).toBe("PHASE_3A_PREVIEW_ONLY");
    expect(readiness.readyForCommercialProposal.blockers).toContain("FACE_MATERIAL_FALLBACK_REQUIRES_CONFIRMATION");
    expect(readiness.readyForCommercialProposal.blockerIssues.some((issue) => issue.quoteBlocker)).toBe(true);
  });

  it("keeps quote, order, aggregate, and execution gates preview-only", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.readiness.readyForQuoteSnapshot.blockers).toEqual(["PHASE_3A_PREVIEW_ONLY"]);
    expect(draft.readiness.readyForOrderSnapshot.blockers).toEqual(["PHASE_3A_PREVIEW_ONLY"]);
    expect(draft.readiness.readyForProductAggregate.blockers).toEqual(["PHASE_3A_PREVIEW_ONLY"]);
    expect(draft.readiness.readyForExecutionPlan.blockers).toEqual(["PHASE_3A_PREVIEW_ONLY"]);
  });

  it("routes order and execution warnings into downstream warning issue arrays", () => {
    const draft = buildProductTruthDraft(gradiCuratExecutionOnlyElectricalFixture);

    expect(draft.readiness.readyForOrderSnapshot.warningIssues.map((issue) => issue.code)).toContain("ELECTRICAL_SITE_DETAILS_ORDER_EXECUTION_ONLY");
    expect(draft.readiness.readyForExecutionPlan.warningIssues.map((issue) => issue.code)).toContain("PSU_PLACEMENT_ORDER_EXECUTION_ONLY");
  });

  it("does not use readiness to unlock existing Intake V6 actions", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.readiness.readyForInternalDraft.notes).toContain("Pure preview only; this does not unlock the existing Intake V6 CTA.");
    expect(draft.metadata.previewOnly.value).toBe(true);
  });
});
