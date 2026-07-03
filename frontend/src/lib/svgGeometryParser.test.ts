import { describe, expect, it } from "vitest";
import {
  PERIMETER_AREA_UNSUPPORTED_MSG,
  parseSvgGeometryFromText,
} from "@/lib/svgGeometryParser";
import {
  layer,
  SVG_HIDDEN_ELEMENTS,
  SVG_LETTERS_AND_STRUCTURE_LAYERS,
  SVG_LETTERS_WITH_INLINE_BARS,
  SVG_MM_VIEWBOX,
  SVG_MULTI_LAYER,
  SVG_PATH_LAYER,
  SVG_PX_UNITS,
  SVG_RECT_POLYGON,
  SVG_UNSUPPORTED_TRANSFORM,
  SVG_VIEWBOX_ONLY,
} from "@/lib/svgGeometryParser.fixtures";

describe("svgGeometryParser MVP", () => {
  it("extracts physical dimensions from mm width/height", () => {
    const result = parseSvgGeometryFromText(SVG_MM_VIEWBOX, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.parseOk).toBe(true);
    expect(result.units?.scaleSource).toBe("physical");
    expect(result.suggestions.assemblyWidthMm).toBeCloseTo(380, 0);
    expect(result.suggestions.assemblyHeightMm).toBeCloseTo(40, 0);
    expect(result.confidence).toBe("high");
  });

  it("converts cm units to mm", () => {
    const svg = `<svg width="40cm" height="5cm" viewBox="0 0 400 50"><g id="LITERE"><rect width="400" height="50"/></g></svg>`;
    const result = parseSvgGeometryFromText(svg, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.suggestions.assemblyWidthMm).toBeCloseTo(400, 0);
    expect(result.suggestions.assemblyHeightMm).toBeCloseTo(50, 0);
  });

  it("marks px units as low confidence", () => {
    const result = parseSvgGeometryFromText(SVG_PX_UNITS, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.confidence).toBe("low");
    expect(result.warnings.some((w) => w.includes("px"))).toBe(true);
  });

  it("detects layer bbox for rect and polygon", () => {
    const rect = parseSvgGeometryFromText(SVG_MM_VIEWBOX, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(rect.layers[0]?.bboxMm).not.toBeNull();

    const poly = parseSvgGeometryFromText(SVG_RECT_POLYGON, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(poly.suggestions.letterLayerWidthMm).toBeCloseTo(180, 0);
  });

  it("maps LITERE layer to letter suggestions", () => {
    const result = parseSvgGeometryFromText(SVG_MULTI_LAYER, [
      layer("LITERE", "LITERE", "volumetric_letters"),
      layer("DIBOND", "DIBOND", "support_panel"),
      layer("CADRU", "CADRU", "metal_frame"),
    ]);
    expect(result.suggestions.letterLayerWidthMm).toBeGreaterThan(0);
    expect(result.suggestions.supportWidthMm).toBeGreaterThan(0);
    expect(result.suggestions.frameWidthMm).toBeGreaterThan(0);
    expect(result.suggestions.letterElementCount).toBe(2);
  });

  it("excludes support/structure layers from assembly dimensions for quote", () => {
    const result = parseSvgGeometryFromText(SVG_MULTI_LAYER, [
      layer("LITERE", "LITERE", "volumetric_letters"),
      layer("DIBOND", "DIBOND", "support_panel"),
      layer("CADRU", "CADRU", "metal_frame"),
    ]);
    expect(result.suggestions.assemblyWidthMm).toBeCloseTo(500, 0);
    expect(result.suggestions.assemblyWidthMm).not.toBeCloseTo(1000, 0);
    expect(
      result.warnings.some((w) => w.includes("structura suport este exclusă"))
    ).toBe(true);
  });

  it("keeps structure bars out of letter perimeter when on a separate layer", () => {
    const result = parseSvgGeometryFromText(SVG_LETTERS_AND_STRUCTURE_LAYERS, [
      layer("LITERE", "LITERE", "volumetric_letters"),
      layer("BARE_MONTAJ", "BARE_MONTAJ", "metal_frame"),
    ]);
    expect(result.suggestions.letterPerimeterM).toBeGreaterThan(0);
    expect(result.suggestions.letterCount).toBe(2);
    expect(result.suggestions.frameWidthMm).toBeCloseTo(1200, 0);
    expect(result.suggestions.assemblyWidthMm).toBeLessThan(500);
    expect(result.suggestions.letterPerimeterM).toBeLessThan(2);
  });

  it("warns when bar-like rectangles share the letters layer", () => {
    const result = parseSvgGeometryFromText(SVG_LETTERS_WITH_INLINE_BARS, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(
      result.warnings.some((w) =>
        /structură suport în același layer cu literele/i.test(w)
      )
    ).toBe(true);
    expect(result.suggestions.letterCount).toBe(1);
  });

  it("maps DIBOND to support and CADRU to frame", () => {
    const result = parseSvgGeometryFromText(SVG_MULTI_LAYER, [
      layer("DIBOND", "DIBOND", "support_panel"),
      layer("CADRU", "CADRU", "metal_frame"),
    ]);
    expect(result.suggestions.supportAreaM2).toBeGreaterThan(0);
    expect(result.suggestions.frameHeightMm).toBeGreaterThan(0);
    expect(result.warnings.some((w) => w.includes("bounding-box"))).toBe(true);
  });

  it("parses path layer coordinate bounds", () => {
    const result = parseSvgGeometryFromText(SVG_PATH_LAYER, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.suggestions.letterLayerWidthMm).toBeCloseTo(90, 0);
    expect(result.suggestions.letterLayerHeightMm).toBeCloseTo(60, 0);
  });

  it("extracts path perimeter and area for closed letter paths", () => {
    const result = parseSvgGeometryFromText(SVG_PATH_LAYER, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.suggestions.letterPerimeterM).toBeGreaterThan(0);
    expect(result.suggestions.letterFaceAreaM2).toBeGreaterThan(0);
    expect(result.suggestions.letterCount).toBe(1);
    expect(result.unsupported).not.toContain(PERIMETER_AREA_UNSUPPORTED_MSG);
  });

  it("handles unsupported transforms with warning", () => {
    const result = parseSvgGeometryFromText(SVG_UNSUPPORTED_TRANSFORM, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.warnings.some((w) => w.includes("nesuportat"))).toBe(true);
  });

  it("ignores hidden elements in bbox", () => {
    const result = parseSvgGeometryFromText(SVG_HIDDEN_ELEMENTS, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.suggestions.assemblyWidthMm).toBeCloseTo(100, 0);
    expect(result.layers[0]?.elementCount).toBe(1);
  });

  it("falls back to svg root bbox for single confirmed letters layer without group", () => {
    const flatSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm" viewBox="0 0 200 100">
      <path d="M10 10 L190 10 L190 90 L10 90 Z"/>
    </svg>`;
    const result = parseSvgGeometryFromText(flatSvg, [
      layer("Layer 1", "Layer 1", "volumetric_letters"),
    ]);
    expect(result.parseOk).toBe(true);
    expect(result.suggestions.assemblyWidthMm).toBeGreaterThan(0);
    expect(result.warnings.some((w) => /grup dedicat|întregul SVG/i.test(w))).toBe(true);
  });

  it("does not produce mm suggestions for viewBox-only SVG", () => {
    const result = parseSvgGeometryFromText(SVG_VIEWBOX_ONLY, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.suggestions.assemblyWidthMm).toBeUndefined();
    expect(result.confidence).toBe("low");
  });

  it("rejects script in SVG", () => {
    const result = parseSvgGeometryFromText(
      '<svg><script>alert(1)</script></svg>',
      [layer("LITERE", "LITERE", "volumetric_letters")]
    );
    expect(result.parseOk).toBe(false);
  });

  it("ignores metadata sibling and computes letter path metrics", () => {
    const svg = `<svg width="300mm" height="80mm" viewBox="0 0 300 80">
      <g id="Litere">
        <metadata id="meta"/>
        <path d="M10 10 L100 10 L100 70 L10 70 Z"/>
      </g>
      <g id="Structura"><rect x="0" y="70" width="300" height="10"/></g>
    </svg>`;
    const result = parseSvgGeometryFromText(svg, [
      layer("Litere", "Litere", "volumetric_letters"),
      layer("Structura", "Structura", "metal_frame"),
    ]);
    expect(result.suggestions.letterPerimeterM).toBeGreaterThan(0);
    expect(result.suggestions.letterFaceAreaM2).toBeGreaterThan(0);
    expect(result.suggestions.frameHeightMm).toBeGreaterThan(0);
    expect(result.unsupported).not.toContain(PERIMETER_AREA_UNSUPPORTED_MSG);
  });

  it("viewBox-only path failure does not invent perimeter or area", () => {
    const svg = `<svg viewBox="0 0 100 50"><g id="LITERE"><path d=""/></g></svg>`;
    const result = parseSvgGeometryFromText(svg, [
      layer("LITERE", "LITERE", "volumetric_letters"),
    ]);
    expect(result.suggestions.letterPerimeterM).toBeUndefined();
    expect(result.suggestions.letterFaceAreaM2).toBeUndefined();
    expect(result.suggestions.assemblyWidthMm).toBeUndefined();
  });
});
