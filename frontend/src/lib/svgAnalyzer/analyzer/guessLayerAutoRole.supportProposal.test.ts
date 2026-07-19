import { readFileSync, existsSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "./analyzeSvg";
import { buildLayerRoleConfirmationDraft } from "./buildLayerRoleConfirmation";
import { guessLayerAutoRole } from "./guessLayerAutoRole";
import { refineLayerRoleProposalsWithGeometry } from "./refineLayerRoleProposalsWithGeometry";
import type { LayerAnalysis } from "./types";

const DESKTOP = "C:/Users/offic/Desktop/fisiere-teste-svg";

function paintSolid() {
  return {
    fills: ["#cccccc"],
    strokes: [],
    gradientRefs: [],
    hasGradient: false,
    hasPattern: false,
    hasImage: false,
    isMulticolor: false,
    fillCount: 1,
    textElementCount: 0,
    paintKind: "solid" as const,
  };
}

describe("support role proposal truth", () => {
  it("does not short-circuit every pseudo fill to confirmed-looking face", () => {
    const result = guessLayerAutoRole("pseudo:fill-cccccc", paintSolid(), {
      pathCount: 0,
      rectCount: 2,
      polygonCount: 0,
      subPathCount: 0,
    }, "pseudo:fill-cccccc");
    expect(result.autoRole).not.toBe("face");
    expect(result.autoRoleCandidates.some((c) => c.role === "support_panel")).toBe(true);
  });

  it("proposes face for multi-shape solid fills via metrics", () => {
    const result = guessLayerAutoRole("pseudo:fill-e31e24", paintSolid(), {
      pathCount: 1,
      rectCount: 0,
      polygonCount: 0,
      subPathCount: 14,
    }, "pseudo:fill-e31e24");
    expect(result.autoRole).toBe("face");
  });

  it("ACM segmented fixture: grey support_panel proposal, red face, neither confirmed", () => {
    const path = `${DESKTOP}/litere-cu-fundal-acm-segmentat.svg`;
    if (!existsSync(path)) return;
    const svg = readFileSync(path, "utf8");
    const { report } = analyzeSvgString(svg, "litere-cu-fundal-acm-segmentat.svg", svg.length);
    const grey = report.layers.find((l) => l.id === "pseudo:fill-c5c6c6");
    const red = report.layers.find((l) => l.id === "pseudo:fill-e31e24");
    expect(grey?.autoRole).toBe("support_panel");
    expect(red?.autoRole).toBe("face");
    const draft = buildLayerRoleConfirmationDraft(report.layers);
    expect(draft.layers.every((l) => l.confirmationState === "pending")).toBe(true);
    expect(draft.layers.every((l) => l.confirmedRole == null)).toBe(true);
  });

  it("crossing fixture keeps support proposal + letter face", () => {
    const path = `${DESKTOP}/litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg`;
    if (!existsSync(path)) return;
    const svg = readFileSync(path, "utf8");
    const { report } = analyzeSvgString(svg, "crossing.svg", svg.length);
    expect(report.layers.find((l) => l.id === "pseudo:fill-c5c6c6")?.autoRole).toBe("support_panel");
    expect(report.layers.find((l) => l.id === "pseudo:fill-e31e24")?.autoRole).toBe("face");
  });

  it("simple letters fixture does not invent support_panel", () => {
    const path = `${DESKTOP}/litere-vol-1-layer.svg`;
    if (!existsSync(path)) return;
    const svg = readFileSync(path, "utf8");
    const { report } = analyzeSvgString(svg, "litere-vol-1-layer.svg", svg.length);
    expect(report.layers.some((l) => l.autoRole === "support_panel")).toBe(false);
    expect(report.layers.some((l) => l.autoRole === "face")).toBe(true);
  });

  it("ambiguous equal support-shaped pseudos without outer evidence stay unknown", () => {
    const mk = (id: string, area: number): LayerAnalysis =>
      ({
        id,
        name: id,
        layerKind: "pseudo",
        autoRole: "face",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: paintSolid(),
        productionHint: "cnc_cut",
        roleGuess: "face",
        elementCount: 1,
        pathElementCount: 0,
        subPathCount: 0,
        closedSubPathCount: 0,
        openSubPathCount: 0,
        widthMm: 500,
        heightMm: 200,
        boundingAreaSqm: area,
        filledAreaSqm: area,
        areaConfidence: "high",
        perimeterMm: 1000,
        perimeterMl: 1,
        colors: [],
        warnings: [],
      }) as LayerAnalysis;

    const refined = refineLayerRoleProposalsWithGeometry([mk("pseudo:a", 0.2), mk("pseudo:b", 0.21)], {
      candidate_count: 0,
      unit_ambiguity: false,
      candidates: [],
    } as never);
    expect(refined.every((l) => l.autoRole === "unknown")).toBe(true);
  });
});
