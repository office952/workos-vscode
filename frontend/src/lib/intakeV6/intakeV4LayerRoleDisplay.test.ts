import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { buildLayerRoleConfirmationDraft } from "@/lib/svgAnalyzer";
import {
  buildLayerRoleRowsForDisplay,
  countArtworkLayers,
  countProductionGeometryLayers,
} from "./intakeV4LayerRoleDisplay";
import { confirmAllSuggestedLayerRoles } from "./intakeV4LayerRoleBridge";

const fixtureDir = join(
  dirname(fileURLToPath(import.meta.url)),
  "../svgAnalyzer/fixtures",
);

function analyzeFixture(fileName: string) {
  const svg = readFileSync(join(fixtureDir, fileName), "utf8");
  return analyzeSvgString(svg, fileName, svg.length).report;
}

describe("intakeV4LayerRoleDisplay six rows", () => {
  it("layered fixture shows six rows with volumetric and artwork labels", () => {
    const report = analyzeFixture("ana-maria-gradinita.svg");
    const draft = buildLayerRoleConfirmationDraft(report.layers);
    const rows = buildLayerRoleRowsForDisplay(report, draft);

    expect(rows.length).toBe(6);
    expect(rows.map((row) => row.layerName)).toEqual(
      expect.arrayContaining(["gradinita", "ana", "maria", "soare", "logo stanga", "logo dreapta"]),
    );
    expect(rows.filter((row) => row.kindLabel === "Corel layer").length).toBe(6);
    expect(rows.filter((row) => row.selectedRoleLabel === "Față litere / geometrie volumetrică").length).toBe(4);
    expect(rows.filter((row) => row.selectedRoleLabel === "Artwork / print / autocolant").length).toBe(2);
  });

  it("unlayered fixture shows pseudo and raster source labels", () => {
    const report = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
    const draft = buildLayerRoleConfirmationDraft(report.layers);
    const rows = buildLayerRoleRowsForDisplay(report, draft);

    expect(rows.length).toBe(6);
    expect(rows.filter((row) => row.kindLabel === "Pseudo-layer").length).toBe(4);
    expect(rows.filter((row) => row.kindLabel === "Raster artwork").length).toBe(2);
    expect(rows.every((row) => row.hint)).toBe(true);
  });

  it("confirm all auto roles clears missing for six confirmable layers", () => {
    const report = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
    const draft = buildLayerRoleConfirmationDraft(report.layers);
    const confirmed = confirmAllSuggestedLayerRoles(draft);
    expect(confirmed.confirmationStatus).toBe("complete");
    expect(countProductionGeometryLayers(report)).toBe(4);
    expect(countArtworkLayers(report)).toBe(2);
  });
});
