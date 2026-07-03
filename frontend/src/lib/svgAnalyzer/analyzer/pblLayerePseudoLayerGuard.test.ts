import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buildLayerRoleConfirmationDraft } from "./buildLayerRoleConfirmation";
import { analyzeSvgString } from "./analyzeSvg";
import { confirmAllSuggestedLayerRoles } from "@/lib/intakeV4/intakeV4LayerRoleBridge";
import { resolveQuoteGeometryForWorkspace } from "@/lib/intakeV4/intakeV4QuoteGeometry";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");

function analyzePbl() {
  const source = readFileSync(join(fixtureDir, "pbl-layere.svg"), "utf8");
  return analyzeSvgString(source, "pbl-layere.svg", Buffer.byteLength(source));
}

function approx(actual: number | null | undefined, expected: number, tolerance: number): void {
  expect(actual).not.toBeNull();
  expect(Math.abs((actual ?? 0) - expected)).toBeLessThanOrEqual(tolerance);
}

describe("pbl-layere pseudo-layer regression guard", () => {
  it("preserves Corel Layer_x0020_* structure instead of ana-maria color pseudo split", () => {
    const { report } = analyzePbl();
    const layerNames = report.layers.map((layer) => layer.name);
    expect(layerNames).toEqual(
      expect.arrayContaining(["Layer_x0020_1", "Layer_x0020_2", "Layer_x0020_3"]),
    );
    expect(report.layers.some((layer) => layer.id.startsWith("pseudo:"))).toBe(false);
    expect(report.layers.length).toBe(3);
  });

  it("keeps 11 child parts (10 letters + 1 artwork)", () => {
    const { report } = analyzePbl();
    expect(report.parts?.count).toBe(11);
    expect(report.parts?.splitDiagnostics?.groupsCreated).toBe(10);
    expect(report.parts?.splitDiagnostics?.subPathCount).toBe(15);
  });

  it("preserves document size and quote geometry metrics", () => {
    const { report } = analyzePbl();
    approx(report.document.widthMm, 2700, 5);
    approx(report.document.heightMm, 350, 5);

    const draft = buildLayerRoleConfirmationDraft(report.layers);
    const confirmed = confirmAllSuggestedLayerRoles(draft);
    expect(confirmed.confirmationStatus).toBe("complete");

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
    expect(geometry.primary_letters_layer_key).toMatch(/Layer_x0020_/);
  });

  it("does not classify raster artwork layer as volumetric face child parts", () => {
    const { report } = analyzePbl();
    const artwork = (report.parts?.items ?? []).find((item) => item.source.layerName === "Layer_x0020_1");
    expect(artwork?.partExtractionMethod).toBe("layer-as-part");
    const faceParts = (report.parts?.items ?? []).filter(
      (item) => item.partExtractionMethod === "subpath-shape-grouping",
    );
    expect(faceParts.length).toBe(10);
  });
});
