import { describe, expect, it } from "vitest";
import {
  buildAssociatePrimarySupportContourPatch,
  resolvePrimaryClosedContourCandidate,
} from "./associatePrimarySupportContour";
import type { ClosedContourCandidate, SvgAnalysisReport } from "@/lib/svgAnalyzer";

function candidate(
  partial: Partial<ClosedContourCandidate> & { contour_id: string },
): ClosedContourCandidate {
  return {
    contour_id: partial.contour_id,
    element_id: partial.element_id ?? partial.contour_id,
    source_element_type: "path",
    source_index: 0,
    source_subpath_index: null,
    is_closed: true,
    closure_method: "explicit_z",
    geometry_hash: partial.geometry_hash ?? "hash1",
    width_mm: partial.width_mm ?? 1200,
    height_mm: partial.height_mm ?? 800,
    area_mm2: partial.area_mm2 ?? 960_000,
    perimeter_mm: partial.perimeter_mm ?? 4000,
    centroid: { x: 0, y: 0 },
    orientation: "landscape",
    confidence: partial.confidence ?? 0.7,
    is_outer_candidate: partial.is_outer_candidate ?? false,
    contains_count: partial.contains_count ?? 2,
    contained_area_ratio: 0.5,
    rectangularity_score: 0.9,
    reasons: [],
    warnings: [],
    bbox: { x: 0, y: 0, width: 100, height: 50 },
  };
}

describe("associatePrimarySupportContour", () => {
  it("prefers outer candidate", () => {
    const primary = resolvePrimaryClosedContourCandidate([
      candidate({ contour_id: "inner", is_outer_candidate: false }),
      candidate({ contour_id: "outer", is_outer_candidate: true, width_mm: 1500, height_mm: 900 }),
    ]);
    expect(primary?.contour_id).toBe("outer");
  });

  it("builds mounting_solution with SVG panel dimensions", () => {
    const report = {
      closedContourCandidates: {
        schema: "closed_contour_candidates_v1",
        candidate_count: 1,
        closed_contour_count: 1,
        unit_ambiguity: true,
        mm_per_vbu_used: 1,
        mm_per_vbu_raw: 1,
        scale_correction: "viewbox_as_mm_corel_cm_guard",
        warnings: [],
        candidates: [
          candidate({
            contour_id: "cc_outer",
            is_outer_candidate: true,
            width_mm: 1500,
            height_mm: 900,
          }),
        ],
      },
    } as unknown as SvgAnalysisReport;

    const { patch, blockers } = buildAssociatePrimarySupportContourPatch({
      report,
      finishSetup: {},
      svgSourceHash: "svghash",
    });
    expect(blockers).toEqual([]);
    expect(patch?.mounting_solution).toMatchObject({
      template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
      configuration: {
        panel_width_mm: 1500,
        panel_height_mm: 900,
      },
    });
    expect(patch?.svg_support_selection).toMatchObject({
      status: "confirmed",
      role: "ALUCOBOND_CASED_PANEL",
      unit_ambiguity: true,
    });
  });
});
