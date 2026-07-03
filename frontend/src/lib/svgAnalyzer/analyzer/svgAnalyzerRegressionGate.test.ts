/**
 * SVG analyzer regression gate — run this file before any analyzer / layer-role change.
 * Canonical fixtures: PBL (stable), Ana Maria layered, Ana Maria unlayered.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buildLayerRoleConfirmationDraft } from "./buildLayerRoleConfirmation";
import { analyzeSvgString } from "./analyzeSvg";
import { confirmAllSuggestedLayerRoles } from "@/lib/intakeV4/intakeV4LayerRoleBridge";
import {
  countArtworkLayers,
  countProductionGeometryLayers,
} from "@/lib/intakeV4/intakeV4LayerRoleDisplay";
import { resolveQuoteGeometryForWorkspace } from "@/lib/intakeV4/intakeV4QuoteGeometry";
import { buildAnaMariaPerimeterDiagnostic } from "./anaMariaPerimeterDiagnostic";
import { COREL_ANA_MARIA_REFERENCE } from "./corelAnaMariaReference";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");

function analyzeFixture(fileName: string) {
  const svg = readFileSync(join(fixtureDir, fileName), "utf8");
  return analyzeSvgString(svg, fileName, svg.length);
}

function approx(actual: number | null | undefined, expected: number, tolerance: number): void {
  expect(actual).not.toBeNull();
  expect(Math.abs((actual ?? 0) - expected)).toBeLessThanOrEqual(tolerance);
}

function expectConfirmAllComplete(report: ReturnType<typeof analyzeFixture>["report"]) {
  const draft = buildLayerRoleConfirmationDraft(report.layers);
  const confirmed = confirmAllSuggestedLayerRoles(draft);
  expect(confirmed.confirmationStatus).toBe("complete");
  return confirmed;
}

describe("SVG analyzer regression gate", () => {
  describe("PBL canonical stable fixture (pbl-layere.svg)", () => {
    it("preserves geometry metrics, child parts, and confirmable Corel layers", () => {
      const { report } = analyzeFixture("pbl-layere.svg");

      expect(report.layers.some((layer) => layer.id.startsWith("pseudo:"))).toBe(false);
      expect(report.layers.map((layer) => layer.name)).toEqual(
        expect.arrayContaining(["Layer_x0020_1", "Layer_x0020_2", "Layer_x0020_3"]),
      );

      expect(report.parts?.count).toBe(11);
      expect(report.parts?.splitDiagnostics?.groupsCreated).toBe(10);
      expect(report.parts?.splitDiagnostics?.subPathCount).toBe(15);

      approx(report.document.widthMm, 2700, 5);
      approx(report.document.heightMm, 350, 5);

      const confirmed = expectConfirmAllComplete(report);
      const geometry = resolveQuoteGeometryForWorkspace({
        analyzerReport: report,
        layerRoleConfirmation: confirmed,
      });

      expect(geometry.real_letters_count).toBe(10);
      approx(geometry.face_area_m2, 0.691, 0.02);
      approx(geometry.led_perimeter_ml ?? geometry.letter_perimeter_m, 11.63, 0.15);
      approx(geometry.cutting_perimeter_ml ?? geometry.face_cutting_perimeter_ml, 13.62, 0.2);
      expect(geometry.inner_holes_count).toBe(5);
      expect(geometry.cutting_contours_count).toBe(15);

      const imageParts = report.parts?.items.filter((part) => part.sourceElementType === "image") ?? [];
      expect(imageParts.length).toBe(0);
    });
  });

  describe("Ana Maria layered (ana-maria-gradinita.svg)", () => {
    it("detects six semantic layers with confirm-all complete", () => {
      const { report } = analyzeFixture("ana-maria-gradinita.svg");
      expect(report.layers.length).toBe(6);
      expect(countProductionGeometryLayers(report)).toBe(4);
      expect(countArtworkLayers(report)).toBe(2);
      expectConfirmAllComplete(report);
    });
  });

  describe("Ana Maria unlayered (ana-maria-gradinita-fara-layere.svg)", () => {
    it("generates six pseudo/raster entities with confirm-all complete", () => {
      const { report } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
      expect(report.layers.length).toBe(6);
      expect(countProductionGeometryLayers(report)).toBe(4);
      expect(countArtworkLayers(report)).toBe(2);
      expectConfirmAllComplete(report);

      const pseudoLetters = report.layers.filter((layer) => layer.layerKind === "pseudo");
      const artworkLayers = report.layers.filter(
        (layer) => layer.layerKind === "raster_artwork" || layer.autoRole === "printed_artwork",
      );
      expect(pseudoLetters.length).toBe(4);
      expect(artworkLayers.length).toBe(2);
    });

    it("excludes defs clipPath subpaths from production parts (no orphan split_layer_N_M)", () => {
      const { report } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
      const orphanSplit =
        report.parts?.items.filter((part) => /^split_layer_\d+_\d+$/.test(part.id)) ?? [];
      expect(orphanSplit).toEqual([]);
    });

    it("matches CorelDRAW reference volumetric letter perimeter (±5%)", () => {
      const { report } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
      const confirmed = expectConfirmAllComplete(report);
      const diagnostic = buildAnaMariaPerimeterDiagnostic(
        report,
        confirmed,
        "ana-maria-gradinita-fara-layere.svg",
      );

      expect(diagnostic.comparison.passApproximate || diagnostic.comparison.passWithWarning).toBe(true);
      expect(Math.abs(diagnostic.comparison.lettersDeltaPercent ?? 99)).toBeLessThanOrEqual(
        COREL_ANA_MARIA_REFERENCE.warningTolerancePercent,
      );
      expect(diagnostic.applicationMetrics.volumetricLettersPerimeterM).toBeCloseTo(
        COREL_ANA_MARIA_REFERENCE.volumetricLettersPerimeterM,
        1,
      );
    });
  });
});
