import { describe, expect, it } from "vitest";
import { buildProductTruthDraft } from "./productTruthDraftBuilder";
import {
  gradiCuratArtworkIgnoredFixture,
  gradiCuratArtworkOnlyFixture,
  gradiCuratCompleteReviewLikeFixture,
  gradiCuratConfirmedRolesFixture,
  gradiCuratExecutionOnlyElectricalFixture,
  gradiCuratLaminateWithoutPrintWarningFixture,
  gradiCuratMissingFinishTargetFixture,
  gradiCuratPrintNoLaminateFixture,
  gradiCuratSupportMountingMismatchFixture,
  gradiCuratUnconfirmedFixture,
} from "./productTruthFixtures";

function codes(issues: { code: string }[]): string[] {
  return issues.map((issue) => issue.code);
}

describe("buildProductTruthDraft", () => {
  it("keeps analyzer suggestions blocked until operator confirmation", () => {
    const draft = buildProductTruthDraft(gradiCuratUnconfirmedFixture);

    expect(draft.metadata.previewOnly.value).toBe(true);
    expect(draft.layers).toHaveLength(6);
    expect(draft.layers[0].autoRole.state).toBe("suggested");
    expect(draft.layers[0].confirmedRole.state).toBe("blocked");
    expect(codes(draft.blockers)).toContain("LAYER_ROLES_INCOMPLETE");
    expect(draft.readiness.readyForReview.ready).toBe(false);
  });

  it("marks confirmed layer roles as operator sourced truth", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.layers.every((layer) => layer.confirmedRole.state === "confirmed")).toBe(true);
    expect(draft.layers[0].confirmedRole.sourceRefs[0].sourceKind).toBe("operator");
    expect(codes(draft.blockers)).not.toContain("LAYER_ROLES_INCOMPLETE");
  });

  it("preserves owner defaults as fallback instead of confirmed truth", () => {
    const draft = buildProductTruthDraft(gradiCuratUnconfirmedFixture);

    expect(draft.components.face.materialFamily.value).toBe("plexiglas_opal");
    expect(draft.components.face.materialFamily.state).toBe("fallback");
    expect(draft.components.face.thicknessMm.value).toBe(3);
    expect(draft.components.face.thicknessMm.state).toBe("fallback");
    expect(codes(draft.blockers)).toContain("FACE_MATERIAL_FALLBACK_REQUIRES_CONFIRMATION");
    expect(codes(draft.blockers)).toContain("FACE_THICKNESS_FALLBACK_REQUIRES_CONFIRMATION");
  });

  it("accepts explicit face material and 3 mm thickness as confirmed truth", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.face.materialFamily.state).toBe("confirmed");
    expect(draft.components.face.thicknessMm.value).toBe(3);
    expect(draft.components.face.thicknessMm.state).toBe("confirmed");
    expect(codes(draft.blockers)).not.toContain("FACE_THICKNESS_FALLBACK_REQUIRES_CONFIRMATION");
  });

  it("does not treat 5 mm as the default face thickness", () => {
    const draft = buildProductTruthDraft(gradiCuratUnconfirmedFixture);

    expect(draft.components.face.thicknessMm.value).toBe(3);
  });

  it("keeps Forex 10 no-sanfren as default backing", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.back.material.value).toBe("forex_10");
    expect(draft.components.back.bevelEnabled.value).toBe(false);
  });

  it("maps selected sanfren as manual or confirmed input instead of fallback", () => {
    const draft = buildProductTruthDraft({
      ...gradiCuratCompleteReviewLikeFixture,
      finishSetup: {
        ...gradiCuratCompleteReviewLikeFixture.finishSetup,
        back_bevel_enabled: true,
        confirmed: false,
      },
    });

    expect(draft.components.back.bevelEnabled.value).toBe(true);
    expect(draft.components.back.bevelEnabled.state).toBe("manual");
  });

  it("keeps return/cant depth at 60 mm when explicit", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.returnCant.depthMm.value).toBe(60);
    expect(codes(draft.blockers)).not.toContain("RETURN_CANT_DEPTH_MISSING");
  });

  it("blocks active return/cant finish when depth is missing", () => {
    const draft = buildProductTruthDraft({
      ...gradiCuratCompleteReviewLikeFixture,
      finishSetup: {
        ...gradiCuratCompleteReviewLikeFixture.finishSetup,
        return_depth_mm: null,
      },
    });

    expect(draft.components.returnCant.depthMm.value).toBe(60);
    expect(codes(draft.blockers)).toContain("RETURN_CANT_DEPTH_MISSING");
  });

  it("keeps Oracal series, color, and roll width as separate fields", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.finish.oracalSeries.value).toBe("651");
    expect(draft.components.finish.oracalColor.value).toBeNull();
    expect(draft.components.finish.rollWidthMm.value).toBe(1000);
    expect(draft.components.finish.groupFinishes[0].faceOracalCode.value).toBe("056");
  });

  it("blocks active finish without explicit finish target", () => {
    const draft = buildProductTruthDraft(gradiCuratMissingFinishTargetFixture);

    expect(draft.components.finish.finishTarget.value).toBeNull();
    expect(draft.components.finish.finishTarget.state).toBe("blocked");
    expect(codes(draft.blockers)).toContain("FINISH_TARGET_MISSING");
  });

  it("separates print and lamination draft fields from encoded artwork execution", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.artwork.items[0].executionType.value).toBe("print_laminate");
    expect(draft.components.artwork.items[0].printRequired.value).toBe(true);
    expect(draft.components.artwork.items[0].laminationRequired.value).toBe(true);
    expect(draft.components.finish.printRequired.value).toBe(true);
    expect(draft.components.finish.laminationRequired.value).toBe(true);
    expect(codes(draft.warnings)).toContain("PRINT_LAMINATION_ENCODED_NOT_CANONICAL");
  });

  it("does not turn printed_artwork analyzer suggestion into final print without a decision", () => {
    const draft = buildProductTruthDraft(gradiCuratConfirmedRolesFixture);

    expect(draft.components.artwork.hasPrintedArtworkSuggestion.value).toBe(true);
    expect(codes(draft.blockers)).toContain("ARTWORK_DECISION_MISSING");
  });

  it("preserves ignored artwork decisions and clears print requirements", () => {
    const draft = buildProductTruthDraft(gradiCuratArtworkIgnoredFixture);

    expect(draft.components.artwork.items.every((item) => item.artworkDecision.value === "ignored")).toBe(true);
    expect(draft.components.artwork.items.every((item) => item.printRequired.value === false)).toBe(true);
    expect(draft.components.finish.printRequired.value).toBe(false);
  });

  it("preserves artwork-only decisions without requiring print", () => {
    const draft = buildProductTruthDraft(gradiCuratArtworkOnlyFixture);

    expect(draft.components.artwork.items[0].artworkDecision.value).toBe("artwork_only");
    expect(draft.components.artwork.items[0].printRequired.value).toBe(false);
    expect(draft.components.artwork.items[0].laminationRequired.value).toBe(false);
  });

  it("supports print without lamination", () => {
    const draft = buildProductTruthDraft(gradiCuratPrintNoLaminateFixture);

    expect(draft.components.finish.printRequired.value).toBe(true);
    expect(draft.components.finish.laminationRequired.value).toBe(false);
    expect(codes(draft.warnings)).not.toContain("LAMINATION_WITHOUT_PRINT");
  });

  it("warns when lamination is selected without print", () => {
    const draft = buildProductTruthDraft(gradiCuratLaminateWithoutPrintWarningFixture);

    expect(draft.components.finish.printRequired.value).toBe(false);
    expect(draft.components.finish.laminationRequired.value).toBe(true);
    expect(codes(draft.warnings)).toContain("LAMINATION_WITHOUT_PRINT");
  });

  it("does not promote bar mounting to confirmed support truth", () => {
    const draft = buildProductTruthDraft(gradiCuratSupportMountingMismatchFixture);

    expect(draft.components.mounting.mountingSystem.value).toBe("steel_bars");
    expect(draft.components.mounting.mountingSystem.state).toBe("confirmed");
    expect(draft.components.support.supportRequired.value).toBe("suggested");
    expect(draft.components.support.supportRequired.state).toBe("suggested");
    expect(draft.components.support.supportType.value).toBe("steel_bars");
    expect(draft.components.support.supportType.state).toBe("suggested");
    expect(codes(draft.warnings)).toContain("SUPPORT_MOUNTING_BRIDGE_NOT_CANONICAL");
  });

  it("does not treat direct_wall as support truth", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.mounting.mountingSystem.value).toBe("direct_wall");
    expect(draft.components.support.supportRequired.value).toBe("no");
    expect(codes(draft.warnings)).not.toContain("SUPPORT_MOUNTING_BRIDGE_NOT_CANONICAL");
  });

  it("keeps cable defaults as fallback Product Truth", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.components.electrical.cableDefaults.value).toEqual({
      perLetterCableM: 1,
      finalFeedCableM: 5,
      perLetterCableType: "2x0.75",
      finalFeedCableType: "2x1.5",
    });
    expect(draft.components.electrical.cableDefaults.state).toBe("fallback");
  });

  it("keeps extra cable and PSU placement as order/execution-only unless quote scoped", () => {
    const draft = buildProductTruthDraft(gradiCuratExecutionOnlyElectricalFixture);

    expect(draft.components.electrical.extraCableOrSiteDetails.value).toContain("PSU placement");
    expect(draft.components.electrical.extraCableOrSiteDetails.warnings).toContain("ELECTRICAL_SITE_DETAILS_ORDER_EXECUTION_ONLY");
    expect(draft.components.electrical.psuPlacement.value).toBe("inside_letter_group");
    expect(draft.components.electrical.psuPlacement.warnings).toContain("PSU_PLACEMENT_ORDER_EXECUTION_ONLY");
    expect(codes(draft.warnings)).toContain("ELECTRICAL_SITE_DETAILS_ORDER_EXECUTION_ONLY");
    expect(codes(draft.warnings)).toContain("PSU_PLACEMENT_ORDER_EXECUTION_ONLY");
  });

  it("does not include commercial price as Product Truth", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(JSON.stringify(draft.components.pricingBoundary)).not.toMatch(/price|costEngine|CommercialPriceProposal/i);
    expect(draft.components.pricingBoundary.commercialPreviewStatus.value).toBe("preview_only");
  });

  it("adds issue metadata required by the canonical draft contract", () => {
    const draft = buildProductTruthDraft(gradiCuratUnconfirmedFixture);
    const issue = draft.blockers[0];

    expect(issue.affectedComponent).toBeTruthy();
    expect(issue.affectedField).toBeTruthy();
    expect(issue.source).toBeTruthy();
    expect(typeof issue.quoteBlocker).toBe("boolean");
    expect(typeof issue.orderBlocker).toBe("boolean");
    expect(typeof issue.executionBlocker).toBe("boolean");
  });

  it("is deterministic for identical input", () => {
    const first = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);
    const second = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(second).toEqual(first);
  });

  it("does not mutate fixture input", () => {
    const before = JSON.stringify(gradiCuratExecutionOnlyElectricalFixture);

    buildProductTruthDraft(gradiCuratExecutionOnlyElectricalFixture);

    expect(JSON.stringify(gradiCuratExecutionOnlyElectricalFixture)).toBe(before);
  });

  it("keeps downstream readiness disabled in Phase 3A", () => {
    const draft = buildProductTruthDraft(gradiCuratCompleteReviewLikeFixture);

    expect(draft.readiness.readyForCommercialProposal.ready).toBe(false);
    expect(draft.readiness.readyForCommercialProposal.blockers).toContain("PHASE_3A_PREVIEW_ONLY");
    expect(draft.readiness.readyForQuoteSnapshot.ready).toBe(false);
    expect(draft.readiness.readyForOrderSnapshot.ready).toBe(false);
    expect(draft.readiness.readyForProductAggregate.ready).toBe(false);
    expect(draft.readiness.readyForExecutionPlan.ready).toBe(false);
  });
});
