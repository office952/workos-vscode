import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parseSvgGeometryFromText } from "@/lib/svgGeometryParser";
import { applySuggestedLayerRoles } from "@/lib/svgIntakeFlow";
import { parseSvgVectorText } from "@/lib/svgVectorAnalysis";
const svg = readFileSync("e2e/fixtures/lleexxaa.svg", "utf8");

describe("lleexxaa path metrics probe", () => {
  it("extracts perimeter area and letter count from letters path", () => {
    const analysis = parseSvgVectorText("lleexxaa.svg", svg);
    const layers = applySuggestedLayerRoles(analysis.layers);
    const geo = parseSvgGeometryFromText(svg, layers);

    expect(geo.parseOk).toBe(true);
    expect(geo.suggestions.assemblyWidthMm).toBeGreaterThan(3000);

    expect(geo.suggestions.letterPerimeterM).toBeGreaterThan(5);
    expect(geo.suggestions.letterFaceAreaM2).toBeGreaterThan(0.5);
    expect(geo.suggestions.letterCount).toBeGreaterThanOrEqual(6);
  });
});
