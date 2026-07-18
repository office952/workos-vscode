import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import IntakeV6SegmentedBackgroundPanel from "./IntakeV6SegmentedBackgroundPanel";
import { proposeSegmentedBackgroundFromCandidates, SEGMENTED_MESSAGES_RO } from "@/lib/intakeV6/segmentedBackground";
import type { ClosedContourCandidate } from "@/lib/svgAnalyzer/closed-contour/closedContourTypes";

function cand(id: string, x: number): ClosedContourCandidate {
  return {
    contour_id: id,
    element_id: id,
    source_element_type: "rect",
    source_index: 0,
    source_subpath_index: null,
    is_closed: true,
    closure_method: "primitive_closed",
    geometry_hash: id,
    bbox: { x, y: 0, width: 1000, height: 1000 },
    width_mm: 1000,
    height_mm: 1000,
    area_mm2: 1_000_000,
    perimeter_mm: 4000,
    centroid: { x: x + 500, y: 500 },
    orientation: "square",
    contains_count: 1,
    contained_area_ratio: 0.2,
    is_outer_candidate: true,
    rectangularity_score: 0.95,
    confidence: 0.9,
    reasons: [],
    warnings: [],
  };
}

describe("IntakeV6SegmentedBackgroundPanel", () => {
  it("shows proposal and confirm/reject actions", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates([cand("e1", 0), cand("e2", 1000)])!;
    const onPatch = vi.fn();
    render(
      <IntakeV6SegmentedBackgroundPanel
        finish={{ segmented_background: proposal }}
        onPatch={onPatch}
      />,
    );
    expect(screen.getByTestId("intake-v6-segmented-background-panel")).toBeTruthy();
    expect(screen.getByText(/Posibil fundal format din mai multe panouri/i)).toBeTruthy();
    expect(screen.getByTestId("intake-v6-segmented-status").textContent).toMatch(/Propus/i);
    fireEvent.click(screen.getByTestId("intake-v6-segmented-confirm"));
    expect(onPatch).toHaveBeenCalled();
    expect(onPatch.mock.calls[0][0].segmented_background.status).toBe("CONFIRMED");
  });

  it("shows applied crossing as info not blocker, and cutout as blocker", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates([cand("e1", 0), cand("e2", 1000)])!;
    proposal.element_bindings = [
      {
        binding_id: "eb_a",
        construction_type: "APPLIED_VOLUMETRIC_LETTER",
        primary_panel_id: "panel_1",
        secondary_panel_id: "panel_2",
        crosses_joint: true,
        element_ref: "P",
      },
      {
        binding_id: "eb_c",
        construction_type: "CUTOUT",
        primary_panel_id: "panel_1",
        secondary_panel_id: "panel_2",
        crosses_joint: true,
      },
    ];
    render(
      <IntakeV6SegmentedBackgroundPanel
        finish={{ segmented_background: proposal }}
        onPatch={vi.fn()}
      />,
    );
    expect(screen.getByTestId("intake-v6-segmented-applied-crossing").textContent).toContain(
      SEGMENTED_MESSAGES_RO.appliedCrossing,
    );
    expect(screen.getByTestId("intake-v6-segmented-cutout-blocker").textContent).toContain(
      "decupaj",
    );
    expect(screen.getByTestId("intake-v6-segmented-confirm")).toBeDisabled();
  });

  it("shows confirmed banner after confirmation", () => {
    const proposal = proposeSegmentedBackgroundFromCandidates([cand("e1", 0), cand("e2", 1000)])!;
    proposal.status = "CONFIRMED";
    proposal.operator_confirmed = true;
    render(
      <IntakeV6SegmentedBackgroundPanel
        finish={{ segmented_background: proposal }}
        onPatch={vi.fn()}
      />,
    );
    expect(screen.getByTestId("intake-v6-segmented-confirmed-banner").textContent).toBe(
      SEGMENTED_MESSAGES_RO.confirmed,
    );
    expect(screen.queryByTestId("intake-v6-segmented-confirm")).toBeNull();
  });
});
