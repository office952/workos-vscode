import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV6LayerRoleBridge";
import {
  ANA_MARIA_V6_COREL_LOGO_VECTOR_REFERENCE_M,
  INTAKE_V6_COREL_LOGO_VECTOR_REFERENCE_MISMATCH,
  INTAKE_V6_LOGO_RASTER_EXTERNAL_MISSING_WARNING,
  buildIntakeV6ArtworkLogoDiagnostic,
} from "./intakeV6ArtworkLogoDiagnostic";
import { buildIntakeV6GeometryMetricDisplay } from "./intakeV6GeometryMetricDisplay";
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

describe("intakeV6ArtworkLogoDiagnosticBoundary — Ana Maria", () => {
  it("layered + unlayered: external raster href triggers preview warning on the V6 boundary", () => {
    for (const fileName of ["ana-maria-gradinita.svg", "ana-maria-gradinita-fara-layere.svg"]) {
      const { report, metrics } = analyzeFixture(fileName);
      const diagnostic = buildIntakeV6ArtworkLogoDiagnostic(report, {
        artworkVectorPerimeterDiagnosticM: metrics.artworkVectorPerimeterDiagnosticM,
        artworkPerimeterIsRasterNa: metrics.artworkPerimeterIsRasterNa,
      });
      expect(metrics.artworkLayerCount).toBe(2);
      expect(metrics.volumetricGroupCount).toBe(4);
      expect(diagnostic.hasMissingExternalRasterAsset).toBe(true);
      expect(diagnostic.artworkLogoWarnings).toContain(INTAKE_V6_LOGO_RASTER_EXTERNAL_MISSING_WARNING);
      expect(metrics.artworkLogoWarnings).toContain(INTAKE_V6_LOGO_RASTER_EXTERNAL_MISSING_WARNING);
    }
  });

  it("raster logo remains printed_artwork and does not become child parts", () => {
    const { report, confirmed } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
    const logoLayers = report.layers.filter((layer) => /logo/i.test(layer.name));
    expect(logoLayers.length).toBeGreaterThanOrEqual(2);
    for (const layer of logoLayers) {
      const entry = confirmed.layers.find((row) => row.layerKey === layer.id || row.layerName === layer.name);
      expect(entry?.autoRole === "printed_artwork" || entry?.confirmedRole === "printed_artwork").toBe(true);
    }
    const imageParts = report.parts.items.filter((part) =>
      part.source.elementIds?.some((id) => id.toLowerCase().includes("image") || id.toLowerCase().includes("logo")),
    );
    expect(imageParts).toEqual([]);
  });

  it("unlayered: stroke outline diagnostic matches the Corel logo reference without mismatch warning", () => {
    const { metrics } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
    expect(metrics.artworkVectorPerimeterDiagnosticM).toBeCloseTo(ANA_MARIA_V6_COREL_LOGO_VECTOR_REFERENCE_M, 2);
    expect(metrics.artworkLogoWarnings).not.toContain(INTAKE_V6_COREL_LOGO_VECTOR_REFERENCE_MISMATCH);
  });

  it("layered: vector logo perimeter stays on artwork layers and out of production part count", () => {
    const { metrics, geometry, report } = analyzeFixture("ana-maria-gradinita.svg");
    expect(metrics.artworkVectorPerimeterM).toBeCloseTo(ANA_MARIA_V6_COREL_LOGO_VECTOR_REFERENCE_M, 2);
    expect(metrics.productionPartCount).toBe(19);
    expect((geometry.led_perimeter_ml ?? geometry.letter_perimeter_m ?? 0)).toBeGreaterThan(20);
    const imageParts = report.parts.items.filter((part) =>
      part.source.elementIds?.some((id) => id.toLowerCase().includes("image")),
    );
    expect(imageParts).toEqual([]);
  });
});

describe("intakeV6ArtworkLogoDiagnosticBoundary — raster-only SVG", () => {
  it("shows Corel mismatch when raster has no vector outline", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm" viewBox="0 0 100 50">
        <image id="logo" x="5" y="5" width="20" height="20" href="missing/logo.png" />
      </svg>
    `;
    const { report } = analyzeSvgString(svg, "solo-logo.svg", svg.length);
    const diagnostic = buildIntakeV6ArtworkLogoDiagnostic(report, {
      artworkVectorPerimeterDiagnosticM: null,
      artworkPerimeterIsRasterNa: true,
    });
    expect(diagnostic.showCorelReferenceMismatch).toBe(true);
    expect(diagnostic.artworkLogoWarnings).toContain(INTAKE_V6_COREL_LOGO_VECTOR_REFERENCE_MISMATCH);
  });

  it("returns a clean empty diagnostic when no analyzer report is available", () => {
    const diagnostic = buildIntakeV6ArtworkLogoDiagnostic(null);
    expect(diagnostic.hasRasterArtwork).toBe(false);
    expect(diagnostic.hasMissingExternalRasterAsset).toBe(false);
    expect(diagnostic.hasExternalRasterHref).toBe(false);
    expect(diagnostic.artworkLogoWarnings).toEqual([]);
    expect(diagnostic.showCorelReferenceMismatch).toBe(false);
  });
});