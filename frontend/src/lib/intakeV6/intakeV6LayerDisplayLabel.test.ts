import { describe, expect, it } from "vitest";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import {
  buildIntakeV6LayerDisplayLabel,
  resolveIntakeV6LetterGroupDisplayLabel,
  resolveIntakeV6SourceLayerNameFromPayload,
  resolveIntakeV6StoredLayerDisplayLabel,
  stripIntakeV6PseudoDisplayLabel,
} from "./intakeV6LayerDisplayLabel";

const basePaintEvidence = {
  fills: [],
  strokes: [],
  gradientRefs: [],
  hasGradient: false,
  hasPattern: false,
  hasImage: false,
  isMulticolor: false,
  fillCount: 1,
  textElementCount: 0,
  paintKind: "solid",
} as const;

function makeReport(): SvgAnalysisCoreReport {
  return {
    layers: [
      {
        id: "Layer_x0020_1",
        name: "Layer_x0020_1",
        layerKind: "real",
        autoRole: "reference",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: basePaintEvidence,
        productionHint: "none",
        roleGuess: "reference",
        elementCount: 1,
        pathElementCount: 1,
        subPathCount: 1,
        closedSubPathCount: 1,
        openSubPathCount: 0,
        widthMm: null,
        heightMm: null,
        boundingAreaSqm: null,
        filledAreaSqm: null,
        areaConfidence: "high",
        perimeterMm: null,
        perimeterMl: null,
        colors: ["#64748b"],
        warnings: [],
      },
      {
        id: "pseudo:maria",
        name: "pseudo:maria",
        layerKind: "pseudo",
        autoRole: "face",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: { ...basePaintEvidence, fills: ["#00a0e3"] },
        productionHint: "cnc_cut",
        roleGuess: "face",
        elementCount: 1,
        pathElementCount: 1,
        subPathCount: 1,
        closedSubPathCount: 1,
        openSubPathCount: 0,
        widthMm: null,
        heightMm: null,
        boundingAreaSqm: null,
        filledAreaSqm: null,
        areaConfidence: "high",
        perimeterMm: null,
        perimeterMl: null,
        colors: ["#00a0e3"],
        warnings: [],
      },
    ],
  } as SvgAnalysisCoreReport;
}

describe("buildIntakeV6LayerDisplayLabel", () => {
  it("turns pseudo:maria into operator-friendly display without changing the internal identity", () => {
    const report = makeReport();
    const layer = report.layers[1];
    const display = buildIntakeV6LayerDisplayLabel(layer, 0, report);

    expect(layer.id).toBe("pseudo:maria");
    expect(display.primaryLabel).toBe("Element 1 — albastru");
    expect(display.secondaryLabel).toBe("Grup detectat: maria");
    expect(display.sourceLabel).toBe("Layer sursă: Layer_x0020_1");
    expect(display.technicalKey).toBe("pseudo:maria");
  });

  it("does not surface pseudo fill-* tokens in primary or secondary labels", () => {
    const report = makeReport();
    const fillLayer = {
      ...report.layers[1],
      id: "pseudo:fill-c5c6c6",
      name: "pseudo fill-c5c6c6",
      colors: ["#c5c6c6"],
      paintEvidence: { ...report.layers[1].paintEvidence, fills: ["#c5c6c6"] },
    };
    report.layers[1] = fillLayer;
    const display = buildIntakeV6LayerDisplayLabel(fillLayer, 0, report);
    expect(display.primaryLabel).toMatch(/^Element 1/);
    expect(display.primaryLabel).not.toMatch(/pseudo|fill-c5c6c6/i);
    expect(display.secondaryLabel).not.toMatch(/pseudo|fill-c5c6c6/i);
    expect(display.secondaryLabel).toMatch(/Grup culoare detectat/i);
    expect(display.technicalKey).toBe("pseudo:fill-c5c6c6");
  });

  it("strips technical pseudo prefixes from display labels", () => {
    expect(stripIntakeV6PseudoDisplayLabel("pseudo:maria")).toBe("maria");
    expect(stripIntakeV6PseudoDisplayLabel("pseudo maria (blue)")).toBe("maria");
  });

  it("reads the native source layer from existing path geometry payload", () => {
    expect(
      resolveIntakeV6SourceLayerNameFromPayload({
        path_geometry_summary: {
          drawable_layers: [{ layer_key: "Layer_x0020_1", display_name: "Layer_x0020_1" }],
        },
      }),
    ).toBe("Layer_x0020_1");
  });
});

describe("resolveIntakeV6StoredLayerDisplayLabel", () => {
  it("uses the same Page 1 helper when report layer is found", () => {
    const report = makeReport();
    const label = resolveIntakeV6StoredLayerDisplayLabel({
      layerKey: "pseudo:maria",
      layerName: "pseudo:maria",
      index: 0,
      report,
    });
    expect(label).toBe("Element 1 — albastru");
    expect(label).not.toMatch(/pseudo/i);
  });

  it("never surfaces pseudo fill-* without a report", () => {
    const label = resolveIntakeV6StoredLayerDisplayLabel({
      layerKey: "pseudo:fill-c5c6c6",
      layerName: "pseudo fill-c5c6c6",
      index: 1,
      sourceFillColor: "#c5c6c6",
    });
    expect(label).toMatch(/^Element 2/);
    expect(label).not.toMatch(/pseudo|fill-c5c6c6/i);
  });

  it("uses neutral label for unknown screaming tokens", () => {
    expect(
      resolveIntakeV6StoredLayerDisplayLabel({
        layerName: "GROUP_PATH_001",
        index: 0,
      }),
    ).toBe("Element personalizat");
  });

  it("letter-group adapter matches stored-layer helper", () => {
    const report = makeReport();
    expect(
      resolveIntakeV6LetterGroupDisplayLabel(
        { group_key: "pseudo:maria", layer_name: "pseudo:maria", source_fill_color: "#00a0e3" },
        0,
        report,
      ),
    ).toBe(
      resolveIntakeV6StoredLayerDisplayLabel({
        layerKey: "pseudo:maria",
        layerName: "pseudo:maria",
        index: 0,
        report,
        sourceFillColor: "#00a0e3",
      }),
    );
  });
});
