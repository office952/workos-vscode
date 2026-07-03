import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { parseSvg } from "./parseSvg";
import { analyzeGeometry } from "./analyzeGeometry";
import { detectRasterOverVectorBindings } from "./rasterOverVectorArtwork";
import { analyzeSvgString } from "./analyzeSvg";
import { extractParts } from "../part-extractor/extractParts";
import { buildAnalysisReport } from "./buildAnalysisReport";
import { analyzeColors } from "./analyzeColors";
import { analyzeLayers } from "./analyzeLayers";
import { detectWarnings } from "./detectWarnings";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");

describe("rasterOverVectorArtwork", () => {
  it("uses covered vector area estimate, not image bbox", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100">
        <rect id="face" x="10" y="10" width="40" height="20" fill="#ff0000" />
        <image id="img" x="12" y="12" width="30" height="15" href="photo.png" />
      </svg>
    `;
    const doc = parseSvg(svg, "overlap.svg", svg.length);
    const geometry = analyzeGeometry(doc);
    const bindings = detectRasterOverVectorBindings(doc, geometry);
    expect(bindings.length).toBe(1);
    const binding = bindings[0];
    expect(binding.overlappedVectorIds).toContain("face");
    expect(binding.artworkAreaSource).toBe("covered_vector_area_estimate");
    const imageGeo = geometry.elementGeometries.find((g) => g.elementId === "img");
    const vectorGeo = geometry.elementGeometries.find((g) => g.elementId === "face");
    const imageBBoxAreaM2 =
      ((imageGeo?.bbox?.width ?? 0) * (imageGeo?.bbox?.height ?? 0) * geometry.mmPerVbu ** 2) / 1_000_000;
    expect(binding.artworkAreaEstimateM2).not.toBe(imageBBoxAreaM2);
    expect(binding.artworkAreaEstimateM2).toBeGreaterThan(0);
  });

  it("image alone has no overlapped vectors", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="50mm" height="50mm" viewBox="0 0 50 50">
        <image id="solo" x="5" y="5" width="20" height="20" href="solo.png" />
      </svg>
    `;
    const doc = parseSvg(svg, "solo.svg", svg.length);
    const geometry = analyzeGeometry(doc);
    const bindings = detectRasterOverVectorBindings(doc, geometry);
    expect(bindings[0].overlappedVectorIds).toEqual([]);
    expect(bindings[0].missingExternalImageAsset).toBe(true);
  });

  it("ana-maria-gradinita detects external images and print recommendation", async () => {
    const svg = readFileSync(join(fixtureDir, "ana-maria-gradinita.svg"), "utf8");
    const { report } = analyzeSvgString(svg, "ana-maria-gradinita.svg", svg.length);
    const complexity = report.artworkComplexity;
    expect(complexity).toBeTruthy();
    expect(complexity?.has_raster_over_vector).toBe(true);
    const rasterAssessments = complexity?.assessments.filter((a) => a.has_raster_image) ?? [];
    expect(rasterAssessments.length).toBeGreaterThan(0);
    for (const row of rasterAssessments) {
      expect(row.recommended_application).toBe("print_on_vinyl_laminated");
      expect(row.artwork_role).toBe("print_overlay");
      expect(row.missing_external_image_asset).toBe(true);
      expect(row.overlapped_vector_ids.length).toBeGreaterThan(0);
    }
    const imagePartIds = report.parts.items
      .filter((part) => part.source.elementIds?.some((id) => id.includes("image")))
      .map((part) => part.partId);
    expect(imagePartIds).toEqual([]);
  });

  it("raster overlapping vector does not become volumetric child part", async () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="80mm" height="80mm" viewBox="0 0 80 80">
        <g id="letters">
          <path id="letter-a" d="M10,60 L20,10 L30,60 Z" fill="#00ff00" />
          <image id="art" x="12" y="15" width="16" height="40" href="art.png" />
        </g>
      </svg>
    `;
    const doc = parseSvg(svg, "letter-art.svg", svg.length);
    const geometry = analyzeGeometry(doc);
    const colors = analyzeColors(doc);
    const layers = analyzeLayers(doc, geometry, colors);
    const warnings = detectWarnings(doc, geometry, layers, colors);
    const core = buildAnalysisReport(doc, geometry, layers, colors, warnings);
    const parts = extractParts(core, doc);
    const imageParts = parts.items.filter((part) =>
      part.source.elementIds?.some((id) => id === "art"),
    );
    expect(imageParts).toEqual([]);
  });
});
