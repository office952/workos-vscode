import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV6LayerRoleBridge";
import {
  buildIntakeV6GeometryMetricDisplay,
  isIntakeV6MaterialBreakdownEffectivelyEmpty,
  resolveIntakeV6OperatorCantPerimeterDisplay,
} from "./intakeV6GeometryMetricDisplay";
import { deriveLetterGroupsFromAnalyzer } from "./intakeV6LetterGroups";
import { resolveQuoteGeometryForWorkspace } from "./intakeV6QuoteGeometry";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../svgAnalyzer/fixtures");

function analyzeFixture(fileName: string) {
  const svg = readFileSync(join(fixtureDir, fileName), "utf8");
  const { report } = analyzeSvgString(svg, fileName, svg.length);
  const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation);
  const geometry = resolveQuoteGeometryForWorkspace({
    payload: {},
    analyzerReport: report,
    layerRoleConfirmation: confirmed,
    localFileHash: null,
  });
  const metrics = buildIntakeV6GeometryMetricDisplay({
    report,
    confirmation: confirmed,
    geometry,
    analysisBundleReady: false,
    templateCode: "TPL-VOLUMETRIC-LETTERS",
  });
  return { report, confirmed, geometry, metrics };
}

describe("intakeV6GeometryMetricDisplayBoundary — Ana Maria", () => {
  it("unlayered: keeps the full analyzer-derived metric contract on the V6 boundary", () => {
    const { report, confirmed, geometry, metrics } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
    expect(metrics.volumetricGroupCount).toBe(4);
    expect(metrics.productionPartCount).toBe(19);
    expect(metrics.artworkLayerCount).toBe(2);
    expect(metrics.corelComparableCurveLengthM).toBeCloseTo(26.747, 2);
    expect(metrics.artworkLogoVectorPerimeterM).toBeCloseTo(4.891, 2);
    expect(metrics.fullVectorPerimeterM).toBeCloseTo(31.638, 2);
    expect(metrics.ledExteriorPerimeterM).toBeCloseTo(20.8795, 3);
    expect(metrics.cncFacePerimeterM).toBeCloseTo(24.0726, 3);
    expect(metrics.cantReturnPerimeterM).toBeCloseTo(20.8795, 3);
    expect(metrics.cantPerimeterSource).toBe("outer_only");

    const letterGroups = deriveLetterGroupsFromAnalyzer(report, confirmed);
    const operatorCant = resolveIntakeV6OperatorCantPerimeterDisplay({
      geometryMetrics: metrics,
      geometry,
      letterGroups,
    });
    expect(operatorCant.letterVectorPerimeterM).toBeCloseTo(26.747, 2);
    expect(operatorCant.displayM).toBeCloseTo(31.638, 3);
    expect(operatorCant.ledExteriorPerimeterM).toBeCloseTo(20.8795, 3);
    expect(operatorCant.quoteGeometryCantM).toBeCloseTo(20.8795, 3);
    expect(metrics.artworkVectorPerimeterDiagnosticM).toBeCloseTo(4.891, 2);
    expect(metrics.artworkPerimeterIsDiagnostic).toBe(true);
    expect(metrics.artworkPerimeterIsRasterNa).toBe(false);
    expect(metrics.artworkLogoWarnings.length).toBeGreaterThan(0);
    expect(metrics.hasSoareEmblemNote).toBe(true);
    expect(metrics.analysisBundlePending).toBe(true);
  });

  it("layered: keeps logo vector perimeter available when analyzer exposes stroke geometry", () => {
    const { metrics } = analyzeFixture("ana-maria-gradinita.svg");
    expect(metrics.volumetricGroupCount).toBe(4);
    expect(metrics.productionPartCount).toBe(19);
    expect(metrics.corelComparableCurveLengthM).toBeCloseTo(26.747, 2);
    expect(metrics.artworkVectorPerimeterM).toBeCloseTo(4.891, 2);
    expect(metrics.artworkLogoVectorPerimeterM).toBeCloseTo(4.891, 2);
    expect(metrics.fullVectorPerimeterM).toBeCloseTo(31.638, 2);
    expect(metrics.artworkPerimeterIsRasterNa).toBe(false);
  });
});

describe("isIntakeV6MaterialBreakdownEffectivelyEmpty", () => {
  it("returns true for null or empty rows", () => {
    expect(isIntakeV6MaterialBreakdownEffectivelyEmpty(null)).toBe(true);
    expect(
      isIntakeV6MaterialBreakdownEffectivelyEmpty({
        material_rows: [],
        consumable_rows: [],
        operation_rows: [],
        edge_cant_operation_rows: [],
      }),
    ).toBe(true);
  });
});