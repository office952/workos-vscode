import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6LayersOperatorPanel from "./IntakeV6LayersOperatorPanel";
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
      widthMm: 5087,
      heightMm: 600,
      viewBox: "0 0 519.77 61.30",
      viewBoxWidth: 519.77,
      viewBoxHeight: 61.3,
      scaleX: 1,
      scaleY: 1,
      mmPerViewBoxUnit: 1,
      boundingAreaSqm: 1,
      filledAreaSqm: 1,
      areaConfidence: "high",
      areaEstimated: false,
    },
    geometry: {
      perimeterMm: 1000,
      perimeterMl: 1,
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
        warnings: [],
      },
    ],
    layerRoleConfirmation: {
      schemaVersion: "layer_role_confirmation_v1",
      confirmationStatus: "complete",
      layers: [],
    },
    colors: {
      unique: ["#00A0E3"],
      dominant: ["#00A0E3"],
      fills: ["#00A0E3"],
      strokes: [],
      byLayer: { "pseudo maria (blue)": ["#00A0E3"] },
    },
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

function buildConfirmation(): LayerRoleConfirmation {
  return {
    schemaVersion: "layer_role_confirmation_v1",
    confirmationStatus: "complete",
    layers: [
      {
        layerKey: "pseudo:maria",
        layerId: "pseudo:maria",
        layerName: "pseudo maria (blue)",
        autoRole: "face",
        autoConfidence: "high",
        autoRoleCandidates: [],
        confirmedRole: "face",
        confirmationState: "confirmed",
        operatorNote: null,
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
      },
    ],
  };
}

describe("IntakeV6LayersOperatorPanel", () => {
  it("hides the redundant status badge when all layers are already confirmed", () => {
    render(
      <IntakeV6LayersOperatorPanel
        analyzing={false}
        canImportSvg
        workspaceReady
        report={buildReport()}
        confirmation={buildConfirmation()}
        layerStats={{ total: 1, confirmed: 1, pending: 0 }}
        parseWarning={null}
        scopeWarnings={[]}
        onImportFile={vi.fn()}
        onConfirmAllRoles={vi.fn()}
      />,
    );

    expect(screen.getByTestId("intake-v6-layers-all-confirmed")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-layers-status-badge")).not.toBeInTheDocument();
    expect(screen.getByText("Rezumat straturi")).toBeInTheDocument();
  });

  it("aligns analysis warnings with the owner layer role taxonomy", () => {
    const report = buildReport();
    report.layers = [
      {
        ...report.layers[0],
        warnings: ["Pseudo-layer generated from solid vector fill color cluster."],
      },
      {
        ...report.layers[0],
        id: "logo-stanga",
        name: "logo-stanga",
        layerKind: "pseudo",
        layerOrigin: "stroke_vector_outline",
        autoRole: "printed_artwork",
        roleGuess: "printed_artwork",
        roleReason: "Stroke-only vector isolated as logo/artwork candidate.",
        warnings: ["Stroke-only vector isolated as logo/artwork candidate."],
      },
    ];
    const confirmation = buildConfirmation();
    confirmation.layers = [
      {
        ...confirmation.layers[0],
        layerKey: "pseudo:maria",
        layerId: "pseudo:maria",
        layerName: "pseudo maria (blue)",
        autoRole: "face",
        confirmedRole: "face",
      },
      {
        ...confirmation.layers[0],
        layerKey: "logo-stanga",
        layerId: "logo-stanga",
        layerName: "logo-stanga",
        autoRole: "printed_artwork",
        confirmedRole: "printed_artwork",
      },
    ];

    render(
      <IntakeV6LayersOperatorPanel
        analyzing={false}
        canImportSvg
        workspaceReady
        report={report}
        confirmation={confirmation}
        layerStats={{ total: 2, confirmed: 2, pending: 0 }}
        parseWarning={null}
        scopeWarnings={[]}
        onImportFile={vi.fn()}
        onConfirmAllRoles={vi.fn()}
      />,
    );

    const panel = screen.getByTestId("intake-v6-layers-warnings");
    expect(panel).toHaveTextContent(/observa/i);
    expect(screen.getByTestId("intake-v6-layers-warnings-open-footer")).toBeInTheDocument();
    expect(panel).not.toHaveTextContent("Atenție analiză");
    expect(panel).not.toHaveTextContent("stroke-only");
    expect(panel).not.toHaveTextContent("artwork candidate");
  });
});
