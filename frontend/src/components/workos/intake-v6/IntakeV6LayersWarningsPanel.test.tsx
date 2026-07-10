import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6LayersWarningsPanel from "./IntakeV6LayersWarningsPanel";
import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

function buildReport(): SvgAnalysisCoreReport {
  return {
    schemaName: "svg-analyzer-analysis",
    schemaVersion: "1.11.0",
    engineVersion: "test",
    createdAt: "2026-07-01T00:00:00Z",
    sourceFileName: "gradi-curat.svg",
    sourceFileSize: 123,
    file: {
      name: "gradi-curat.svg",
      sizeBytes: 123,
      detectedUnits: null,
      conversionConfidence: "high",
      physicalSizeSource: "svg width/height",
    },
    document: {
      widthMm: 100,
      heightMm: 100,
      viewBox: "0 0 100 100",
      viewBoxWidth: 100,
      viewBoxHeight: 100,
      scaleX: 1,
      scaleY: 1,
      mmPerViewBoxUnit: 1,
      boundingAreaSqm: 1,
      filledAreaSqm: 1,
      areaConfidence: "high",
      areaEstimated: false,
    },
    geometry: {
      perimeterMm: 100,
      perimeterMl: 0.1,
      perimeterConfidence: "high",
      pathElementCount: 1,
      subPathCount: 1,
      closedSubPathCount: 1,
      openSubPathCount: 0,
      shapeCount: 1,
      transformCount: 0,
    },
    layers: [
      {
        id: "pseudo:maria",
        name: "pseudo maria (blue)",
        layerKind: "pseudo",
        layerOrigin: "solid_fill_cluster",
        roleReason: "Pseudo-layer generated from solid vector fill color cluster.",
        autoRole: "face",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: {
          fills: ["#00A0E3"],
          strokes: [],
          gradientRefs: [],
          hasGradient: false,
          hasPattern: false,
          hasImage: false,
          isMulticolor: false,
          fillCount: 1,
          textElementCount: 0,
          paintKind: "solid",
        },
        productionHint: "cnc_cut",
        roleGuess: "face",
        elementCount: 1,
        pathElementCount: 1,
        subPathCount: 1,
        closedSubPathCount: 1,
        openSubPathCount: 0,
        widthMm: 10,
        heightMm: 10,
        boundingAreaSqm: 1,
        filledAreaSqm: 1,
        areaConfidence: "high",
        perimeterMm: 100,
        perimeterMl: 0.1,
        colors: ["#00A0E3"],
        warnings: ["Pseudo-layer generated from solid vector fill color cluster."],
      },
      {
        id: "logo-stanga",
        name: "logo-stanga",
        layerKind: "pseudo",
        layerOrigin: "stroke_vector_outline",
        roleReason: "Stroke-only vector isolated as logo/artwork candidate.",
        autoRole: "printed_artwork",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: {
          fills: [],
          strokes: ["#2B2A29"],
          gradientRefs: [],
          hasGradient: false,
          hasPattern: false,
          hasImage: false,
          isMulticolor: false,
          fillCount: 0,
          textElementCount: 0,
          paintKind: "none",
        },
        productionHint: "print_vinyl",
        roleGuess: "printed_artwork",
        elementCount: 1,
        pathElementCount: 1,
        subPathCount: 1,
        closedSubPathCount: 1,
        openSubPathCount: 0,
        widthMm: 10,
        heightMm: 10,
        boundingAreaSqm: 1,
        filledAreaSqm: null,
        areaConfidence: "low",
        perimeterMm: 100,
        perimeterMl: 0.1,
        colors: ["#2B2A29"],
        warnings: ["Stroke-only vector isolated as logo/artwork candidate."],
      },
    ],
    layerRoleConfirmation: {
      schemaVersion: "layer_role_confirmation_v1",
      confirmationStatus: "partial",
      layers: [],
    },
    colors: { unique: [], dominant: [], fills: [], strokes: [], byLayer: {} },
    warnings: [],
    errors: [],
    confidence: {
      dimensions: "high",
      perimeter: "high",
      area: "high",
      layers: "high",
      colors: "high",
    },
    benchmark: {
      status: "NO_REFERENCE",
      referenceSource: null,
      referencePerimeterMm: null,
      analyzerPerimeterMm: null,
      deltaMm: null,
      deltaPercent: null,
      passThresholdPercent: null,
    },
    exportMeta: {
      exportedAt: "2026-07-01T00:00:00Z",
      exportedBy: "test",
      appName: "test",
      schemaVersion: "1.11.0",
      notes: [],
    },
  } as SvgAnalysisCoreReport;
}

const confirmation: LayerRoleConfirmation = {
  schemaVersion: "layer_role_confirmation_v1",
  confirmationStatus: "partial",
  layers: [],
};

describe("IntakeV6LayersWarningsPanel", () => {
  it("shows compact analysis summaries instead of per-layer warning chips", () => {
    render(
      <IntakeV6LayersWarningsPanel
        report={buildReport()}
        confirmation={confirmation}
        scopeWarnings={[]}
      />,
    );

    expect(screen.getByTestId("intake-v6-layers-warnings-count")).toHaveTextContent("2 observații");
    expect(screen.getByTestId("intake-v6-pseudo-layer-warning-summary")).toHaveTextContent(
      "1 strat propus",
    );
    expect(screen.getByTestId("intake-v6-atypical-layer-warning-summary")).toHaveTextContent(
      "1 strat propus",
    );
    expect(screen.queryByTestId("intake-v6-warning-layer-chip-pseudo:maria")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-warning-atypical-chip-logo-stanga")).not.toBeInTheDocument();
  });
});
