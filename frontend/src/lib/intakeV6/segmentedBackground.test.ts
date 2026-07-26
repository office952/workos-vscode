import { describe, expect, it } from "vitest";
import type { ClosedContourCandidate } from "@/lib/svgAnalyzer/closed-contour/closedContourTypes";
import {
  buildConfirmSegmentedBackgroundPatch,
  buildRejectSegmentedBackgroundPatch,
  confirmationBlocked,
  proposeSegmentedBackgroundFromCandidates,
  SEGMENTED_MESSAGES_RO,
  selectNearbySupportCandidates,
} from "./segmentedBackground";

function candidate(
  partial: Partial<ClosedContourCandidate> & Pick<ClosedContourCandidate, "contour_id" | "element_id" | "bbox">,
): ClosedContourCandidate {
  const w = partial.width_mm ?? partial.bbox.width;
  const h = partial.height_mm ?? partial.bbox.height;
  return {
    source_element_type: "rect",
    source_index: 0,
    source_subpath_index: null,
    is_closed: true,
    closure_method: "primitive_closed",
    geometry_hash: partial.contour_id,
    width_mm: w,
    height_mm: h,
    area_mm2: w * h,
    perimeter_mm: 2 * (w + h),
    centroid: { x: partial.bbox.x + w / 2, y: partial.bbox.y + h / 2 },
    orientation: "landscape",
    contains_count: 1,
    contained_area_ratio: 0.2,
    is_outer_candidate: true,
    rectangularity_score: 0.95,
    confidence: 0.9,
    reasons: [],
    warnings: [],
    ...partial,
  };
}

describe("segmentedBackground proposal + confirm helpers", () => {
  const twoPanels = [
    candidate({
      contour_id: "c1",
      element_id: "e1",
      bbox: { x: 0, y: 0, width: 1000, height: 1000 },
      width_mm: 1000,
      height_mm: 1000,
    }),
    candidate({
      contour_id: "c2",
      element_id: "e2",
      bbox: { x: 1000, y: 0, width: 1000, height: 1000 },
      width_mm: 1000,
      height_mm: 1000,
    }),
  ];

  it("proposes from nearby support candidates without confirming", () => {
    const group = selectNearbySupportCandidates(twoPanels);
    expect(group).toHaveLength(2);
    const proposal = proposeSegmentedBackgroundFromCandidates(twoPanels);
    expect(proposal).not.toBeNull();
    expect(proposal!.status).toBe("PROPOSED");
    expect(proposal!.operator_confirmed).toBe(false);
    expect(proposal!.detection?.authority).toBe("PROPOSAL_ONLY");
    expect(proposal!.panels).toHaveLength(2);
    expect(proposal!.joints).toHaveLength(1);
  });

  it("does not propose for a single panel", () => {
    expect(proposeSegmentedBackgroundFromCandidates([twoPanels[0]])).toBeNull();
  });

  it("confirm patch sets CONFIRMED + operator authority", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates(twoPanels)!;
    const patch = buildConfirmSegmentedBackgroundPatch(proposal);
    expect(patch.segmented_background.status).toBe("CONFIRMED");
    expect(patch.segmented_background.operator_confirmed).toBe(true);
    expect(patch.segmented_background.confirmation?.message).toBe(SEGMENTED_MESSAGES_RO.confirmed);
  });

  it("reject patch clears confirmed authority", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates(twoPanels)!;
    const patch = buildRejectSegmentedBackgroundPatch(proposal);
    expect(patch.segmented_background.status).toBe("REJECTED");
    expect(patch.segmented_background.operator_confirmed).toBe(false);
    expect(patch.segmented_background.confirmation?.message).toBe(SEGMENTED_MESSAGES_RO.rejected);
  });

  it("blocks confirmation when cutout crosses joint", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates(twoPanels)!;
    proposal.element_bindings = [
      {
        binding_id: "eb_cut",
        construction_type: "CUTOUT",
        primary_panel_id: "panel_1",
        secondary_panel_id: "panel_2",
        crosses_joint: true,
      },
    ];
    const blockers = confirmationBlocked(proposal);
    expect(blockers.some((m) => m.includes("decupaj"))).toBe(true);
  });

  it("allows applied letter crossing (not a confirm blocker)", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates(twoPanels)!;
    proposal.element_bindings = [
      {
        binding_id: "eb_app",
        construction_type: "APPLIED_VOLUMETRIC_LETTER",
        primary_panel_id: "panel_1",
        secondary_panel_id: "panel_2",
        crosses_joint: true,
      },
    ];
    expect(confirmationBlocked(proposal)).toEqual([]);
  });

  it("blocks acrylic insert crossing", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates(twoPanels)!;
    proposal.element_bindings = [
      {
        binding_id: "eb_ins",
        construction_type: "ACRYLIC_INSERT",
        primary_panel_id: "panel_1",
        secondary_panel_id: "panel_2",
        crosses_joint: true,
      },
    ];
    expect(confirmationBlocked(proposal).some((m) => m.includes("plexiglas"))).toBe(true);
  });
});
