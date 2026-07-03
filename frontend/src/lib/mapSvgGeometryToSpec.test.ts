import { describe, expect, it } from "vitest";
import {
  applySvgGeometrySuggestionsToSpec,
  mapSvgGeometrySuggestionsToSpec,
} from "@/lib/mapSvgGeometryToSpec";
import type { SvgGeometryParseResult } from "@/lib/svgGeometryParser";

const sampleResult: SvgGeometryParseResult = {
  parseOk: true,
  units: null,
  layers: [],
  suggestions: {
    assemblyWidthMm: 4800,
    assemblyHeightMm: 600,
    letterElementCount: 9,
    supportAreaM2: 2.88,
  },
  warnings: ["test warning"],
  unsupported: [],
  confidence: "high",
};

describe("mapSvgGeometryToSpec", () => {
  it("stores suggestions without overwriting quote-critical fields", () => {
    const spec = mapSvgGeometrySuggestionsToSpec(
      { width_mm: 100, letter_perimeter_m: 18, letter_face_area_m2: 2.88 },
      sampleResult
    );
    expect(spec.vector_geometry_analyzed).toBe(true);
    expect(spec.vector_suggested_assembly_width_mm).toBe(4800);
    expect(spec.width_mm).toBe(100);
    expect(spec.letter_perimeter_m).toBe(18);
    expect(spec.letter_face_area_m2).toBe(2.88);
  });

  it("applies dimensions only after explicit operator action", () => {
    const withSuggestions = mapSvgGeometrySuggestionsToSpec({}, sampleResult);
    const applied = applySvgGeometrySuggestionsToSpec(withSuggestions, "dimensions");
    expect(applied.width_mm).toBe(4800);
    expect(applied.height_mm).toBe(600);
    expect(applied.geometry_source).toBe("svg_suggestion_confirmed");
    expect(applied.letter_perimeter_m).toBeUndefined();
    expect(applied.letter_face_area_m2).toBeUndefined();
  });

  it("prefers letter layer width over full assembly width for quote metrics", () => {
    const withSuggestions = mapSvgGeometrySuggestionsToSpec({}, {
      ...sampleResult,
      suggestions: {
        assemblyWidthMm: 1000,
        assemblyHeightMm: 200,
        letterLayerWidthMm: 400,
        letterLayerHeightMm: 160,
        letterPerimeterM: 12,
        letterFaceAreaM2: 1.2,
        letterCount: 5,
      },
    });
    const applied = applySvgGeometrySuggestionsToSpec(withSuggestions, "quote_metrics");
    expect(applied.width_mm).toBe(400);
    expect(applied.height_mm).toBe(160);
  });

  it("applies quote metrics (perimeter, area, count, dimensions)", () => {
    const withSuggestions = mapSvgGeometrySuggestionsToSpec({}, {
      ...sampleResult,
      suggestions: {
        ...sampleResult.suggestions,
        letterPerimeterM: 18.5,
        letterFaceAreaM2: 2.88,
        letterCount: 8,
      },
    });
    const applied = applySvgGeometrySuggestionsToSpec(withSuggestions, "quote_metrics");
    expect(applied.width_mm).toBe(4800);
    expect(applied.letter_perimeter_m).toBe(18.5);
    expect(applied.letter_face_area_m2).toBe(2.88);
    expect(applied.letter_count).toBe(8);
    expect(applied.vector_metrics_source).toBe("svg_analysis");
  });
});
