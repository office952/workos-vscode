import { describe, expect, it } from "vitest";
import { parseSvg } from "./parseSvg";
import { analyzeGeometry } from "./analyzeGeometry";
import { analyzeLayers } from "./analyzeLayers";
import { buildArtworkComplexityReport } from "./artworkComplexityAssessment";

import { analyzeColors } from "./analyzeColors";

function assess(svg: string) {
  const doc = parseSvg(svg, "test.svg", svg.length);
  const geometry = analyzeGeometry(doc);
  const colors = analyzeColors(doc);
  const layers = analyzeLayers(doc, geometry, colors);
  return buildArtworkComplexityReport(doc, geometry, layers);
}

describe("artworkComplexityAssessment", () => {
  it(">3 colors recommends print_on_vinyl_laminated", () => {
    const report = assess(`
      <svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="40mm" viewBox="0 0 100 40">
        <g id="poly">
          <rect x="1" y="1" width="8" height="8" fill="#111111" />
          <rect x="10" y="1" width="8" height="8" fill="#222222" />
          <rect x="19" y="1" width="8" height="8" fill="#333333" />
          <rect x="28" y="1" width="8" height="8" fill="#444444" />
          <rect x="37" y="1" width="8" height="8" fill="#555555" />
        </g>
      </svg>
    `);
    const layerRow = report.assessments.find((a) => a.artwork_id.startsWith("layer:"));
    expect(layerRow?.recommended_application).toBe("print_on_vinyl_laminated");
  });

  it("gradient recommends print_on_vinyl_laminated", () => {
    const report = assess(`
      <svg xmlns="http://www.w3.org/2000/svg" width="60mm" height="60mm" viewBox="0 0 60 60">
        <defs>
          <linearGradient id="g"><stop offset="0%" stop-color="#fff"/><stop offset="100%" stop-color="#000"/></linearGradient>
        </defs>
        <g id="art-layer">
          <rect x="5" y="5" width="40" height="30" fill="url(#g)" />
        </g>
      </svg>
    `);
    const row = report.assessments.find((a) => a.has_gradient);
    expect(row?.recommended_application).toBe("print_on_vinyl_laminated");
  });

  it("1-3 flat colors may recommend vinyl_cut", () => {
    const report = assess(`
      <svg xmlns="http://www.w3.org/2000/svg" width="60mm" height="60mm" viewBox="0 0 60 60">
        <g id="flat-layer">
          <rect x="5" y="5" width="40" height="30" fill="#ff0000" />
          <rect x="5" y="35" width="40" height="10" fill="#00ff00" />
        </g>
      </svg>
    `);
    const layerRow = report.assessments.find((a) => a.source_layer_name === "flat-layer");
    expect(layerRow?.dominant_color_count).toBeLessThanOrEqual(3);
    expect(layerRow?.recommended_application).toBe("vinyl_cut");
  });

  it("image alone is manual_review", () => {
    const report = assess(`
      <svg xmlns="http://www.w3.org/2000/svg" width="40mm" height="40mm" viewBox="0 0 40 40">
        <image x="2" y="2" width="20" height="20" href="ext.png" />
      </svg>
    `);
    const row = report.assessments.find((a) => a.has_raster_image);
    expect(row?.recommended_application).toBe("manual_review");
    expect(row?.warnings).toContain("missing_external_image_asset");
  });
});
