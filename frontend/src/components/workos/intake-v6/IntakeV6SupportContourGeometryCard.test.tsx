import { describe, expect, it } from "vitest";
import { resolvePrimaryClosedContourCandidate } from "./IntakeV6SupportContourGeometryCard";
import type { ClosedContourCandidate } from "@/lib/svgAnalyzer";

function candidate(partial: Partial<ClosedContourCandidate> & { contour_id: string }): ClosedContourCandidate {
  return {
    contour_id: partial.contour_id,
    element_id: partial.element_id ?? partial.contour_id,
    source_element_type: "path",
    source_index: 0,
    source_subpath_index: null,
    is_closed: true,
    closure_method: "explicit_z",
    geometry_hash: partial.geometry_hash ?? "h",
    width_mm: partial.width_mm ?? 100,
    height_mm: partial.height_mm ?? 50,
    area_mm2: partial.area_mm2 ?? 5000,
    perimeter_mm: partial.perimeter_mm ?? 300,
    centroid: { x: 0, y: 0 },
    orientation: "landscape",
    confidence: partial.confidence ?? 0.4,
    is_outer_candidate: partial.is_outer_candidate ?? false,
    contains_count: partial.contains_count ?? 0,
    contained_area_ratio: 0,
    rectangularity_score: 0.5,
    reasons: partial.reasons ?? [],
    warnings: [],
    bbox: partial.bbox ?? { x: 0, y: 0, width: 100, height: 50 },
    overlay_d: partial.overlay_d ?? null,
    overlay_points: partial.overlay_points ?? null,
  };
}

describe("resolvePrimaryClosedContourCandidate", () => {
  it("prefers outer candidate over higher-area non-outer", () => {
    const primary = resolvePrimaryClosedContourCandidate([
      candidate({ contour_id: "inner", confidence: 0.9, is_outer_candidate: false, area_mm2: 9000 }),
      candidate({ contour_id: "outer", confidence: 0.6, is_outer_candidate: true, area_mm2: 8000 }),
    ]);
    expect(primary?.contour_id).toBe("outer");
  });

  it("falls back to first candidate when no outer flag", () => {
    const primary = resolvePrimaryClosedContourCandidate([
      candidate({ contour_id: "a", confidence: 0.3 }),
      candidate({ contour_id: "b", confidence: 0.2 }),
    ]);
    expect(primary?.contour_id).toBe("a");
  });
});
