import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "./analyzeSvg";
import { parseSvg } from "./parseSvg";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "../../../../..");
const fixtureDir = join(repoRoot, "fisiere-teste");

const POLICROMIE_GROUP_SVG = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
  <defs>
    <linearGradient id="grad1">
      <stop offset="0" stop-color="#DA2829"/>
      <stop offset="1" stop-color="#00A0E3"/>
    </linearGradient>
  </defs>
  <g id="artwork-policromie">
    <rect fill="url(#grad1)" x="5" y="5" width="90" height="40"/>
  </g>
</svg>`;

describe("non-path group layer name preservation", () => {
  it("parseSvg keeps artwork-policromie group with rect child", () => {
    const doc = parseSvg(POLICROMIE_GROUP_SVG, "artwork-policromie-rect.svg", POLICROMIE_GROUP_SVG.length);
    expect(doc.groups.some((group) => group.id === "artwork-policromie")).toBe(true);
    const rect = doc.elements.find((element) => element.type === "rect");
    expect(rect?.layerId).toBe("artwork-policromie");
    expect(rect?.layerName).toBe("artwork-policromie");
  });

  it("preserves artwork-policromie layer name through full analysis (not unassigned)", () => {
    const { report } = analyzeSvgString(
      POLICROMIE_GROUP_SVG,
      "artwork-policromie-rect.svg",
      POLICROMIE_GROUP_SVG.length,
    );
    const layer = report.layers.find((entry) => entry.id === "artwork-policromie" || entry.name === "artwork-policromie");
    expect(layer).toBeDefined();
    expect(layer?.name).toBe("artwork-policromie");
    expect(report.layers.some((entry) => entry.name === "unassigned")).toBe(false);
    expect(layer?.autoRole).toBe("printed_artwork");
    expect(layer?.paintEvidence?.paintKind).toBe("policromie");
  });

  it("preserves regression-v6-policromie-only fixture layer name", () => {
    const svg = readFileSync(join(fixtureDir, "regression-v6-policromie-only.svg"), "utf8");
    const { report } = analyzeSvgString(svg, "regression-v6-policromie-only.svg", svg.length);
    expect(report.layers.some((entry) => entry.name === "unassigned")).toBe(false);
    expect(report.layers.some((entry) => entry.id === "artwork-policromie")).toBe(true);
  });
});
