import { describe, expect, it } from "vitest";
import {
  applyVectorFileChangeToSpec,
  getEffectiveQuoteGeometrySpec,
  invalidateVectorDerivedGeometry,
  isSameVectorFileIdentity,
  isVectorGeometryCurrentForQuote,
  markVectorGeometryConfirmedForFile,
} from "./vectorGeometryInvalidation";
import { mapProductSpecToVolumetricQuotePrefill } from "./volumetricQuoteInput";
import { buildInitialVolumetricQuoteFlowState } from "./volumetricQuoteFlowState";

const svgAConfirmed = {
  vector_file_name: "hotel_lexa.svg",
  vector_file_selected_at: "2026-06-07T10:00:00.000Z",
  vector_layer_mapping_confirmed: true,
  vector_geometry_analyzed: true,
  vector_metrics_source: "svg_analysis" as const,
  geometry_source: "svg_suggestion_confirmed" as const,
  geometry_confirmed_for_file_name: "hotel_lexa.svg",
  width_mm: 40000,
  height_mm: 5000,
  letter_perimeter_m: 185.797,
  letter_face_area_m2: 101.8419,
  letter_count: 11,
  vector_suggested_letter_perimeter_m: 185.797,
  return_depth_mm: 80,
};

describe("vectorGeometryInvalidation", () => {
  it("detects file identity change by name or selectedAt", () => {
    expect(
      isSameVectorFileIdentity(svgAConfirmed, "hotel_lexa.svg", "2026-06-07T10:00:00.000Z")
    ).toBe(true);
    expect(
      isSameVectorFileIdentity(svgAConfirmed, "lleexxaa.svg", "2026-06-07T11:00:00.000Z")
    ).toBe(false);
    expect(
      isSameVectorFileIdentity(svgAConfirmed, "hotel_lexa.svg", "2026-06-07T12:00:00.000Z")
    ).toBe(false);
  });

  it("clears SVG-derived metrics when a new file is picked", () => {
    const next = applyVectorFileChangeToSpec(
      svgAConfirmed,
      "lleexxaa.svg",
      "2026-06-07T11:00:00.000Z"
    );
    expect(next.geometry_stale).toBe(true);
    expect(next.vector_layer_mapping_confirmed).toBe(false);
    expect(next.vector_geometry_analyzed).toBe(false);
    expect(next.width_mm).toBeUndefined();
    expect(next.letter_perimeter_m).toBeUndefined();
    expect(next.vector_suggested_letter_perimeter_m).toBeUndefined();
    expect(next.geometry_confirmed_for_file_name).toBeUndefined();
    expect(next.return_depth_mm).toBe(80);
  });

  it("marks geometry current only for matching confirmed file", () => {
    expect(isVectorGeometryCurrentForQuote(svgAConfirmed)).toBe(true);
    const stale = invalidateVectorDerivedGeometry(svgAConfirmed);
    expect(isVectorGeometryCurrentForQuote(stale)).toBe(false);
    const marked = markVectorGeometryConfirmedForFile({
      ...stale,
      vector_file_name: "lleexxaa.svg",
      letter_perimeter_m: 12,
      vector_layer_mapping_confirmed: true,
      vector_geometry_analyzed: true,
    });
    expect(isVectorGeometryCurrentForQuote(marked)).toBe(true);
  });

  it("strips stale metrics from classic quote prefill", () => {
    const stale = applyVectorFileChangeToSpec(
      svgAConfirmed,
      "lleexxaa.svg",
      "2026-06-07T11:00:00.000Z"
    );
    const prefill = mapProductSpecToVolumetricQuotePrefill(stale);
    expect(prefill.width_mm).toBeUndefined();
    expect(prefill.letter_perimeter_m).toBeUndefined();
    expect(prefill.return_depth_mm).toBe("80");

    const flow = buildInitialVolumetricQuoteFlowState(stale);
    expect(flow.widthMm).toBe(1000);
    expect(flow.quoteInput.letter_perimeter_m).toBeUndefined();
  });
});
