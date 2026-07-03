import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buildLayerRoleConfirmationDraft } from "./buildLayerRoleConfirmation";
import { analyzeSvgString } from "./analyzeSvg";
import { confirmAllSuggestedLayerRoles } from "@/lib/intakeV4/intakeV4LayerRoleBridge";
import { countArtworkLayers, countProductionGeometryLayers } from "@/lib/intakeV4/intakeV4LayerRoleDisplay";
import { buildAnaMariaPerimeterDiagnostic } from "./anaMariaPerimeterDiagnostic";
import { COREL_ANA_MARIA_REFERENCE } from "./corelAnaMariaReference";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");
const FIXTURE = "ana-maria-gradinita-fara-layere.svg";

function analyzeUnlayered() {
  const svg = readFileSync(join(fixtureDir, FIXTURE), "utf8");
  const { report } = analyzeSvgString(svg, FIXTURE, svg.length);
  const draft = buildLayerRoleConfirmationDraft(report.layers);
  const confirmed = confirmAllSuggestedLayerRoles(draft);
  return { report, confirmed };
}

describe("ana-maria Corel reference perimeter diagnostic", () => {
  it("extracts layer structure and perimeter metrics for comparison", () => {
    const { report, confirmed } = analyzeUnlayered();
    expect(confirmed.confirmationStatus).toBe("complete");
    expect(report.layers.length).toBe(6);
    expect(countProductionGeometryLayers(report)).toBe(4);
    expect(countArtworkLayers(report)).toBe(2);

    const diagnostic = buildAnaMariaPerimeterDiagnostic(report, confirmed, FIXTURE);

    expect(diagnostic.widthMm).toBeGreaterThan(0);
    expect(diagnostic.heightMm).toBeGreaterThan(0);
    expect(diagnostic.productionGeometryLayerCount).toBe(4);
    expect(diagnostic.artworkLayerCount).toBe(2);
    expect(diagnostic.applicationMetrics.volumetricLettersPerimeterM).toBeGreaterThan(0);

    expect(diagnostic.comparison).toMatchObject({
      lettersDeltaPercent: expect.any(Number),
      passApproximate: expect.any(Boolean),
      reasonIfMismatch: expect.any(Array),
    });

    // Diagnostic output for operators / CI logs when investigating Corel deltas.
    console.info("[ana-maria-corel-perimeter]", JSON.stringify(diagnostic, null, 2));
  });

  it("volumetric letters perimeter within tolerance or documents mismatch reason", () => {
    const { report, confirmed } = analyzeUnlayered();
    const diagnostic = buildAnaMariaPerimeterDiagnostic(report, confirmed, FIXTURE);
    const { comparison, applicationMetrics } = diagnostic;

    const lettersM = applicationMetrics.volumetricLettersPerimeterM;
    expect(lettersM).not.toBeNull();
    expect(lettersM!).toBeGreaterThan(0);

    if (comparison.passApproximate) {
      expect(comparison.lettersDeltaPercent).not.toBeNull();
      expect(Math.abs(comparison.lettersDeltaPercent!)).toBeLessThanOrEqual(
        COREL_ANA_MARIA_REFERENCE.tolerancePercent,
      );
      return;
    }

    if (comparison.passWithWarning) {
      expect(Math.abs(comparison.lettersDeltaPercent ?? 0)).toBeLessThanOrEqual(
        COREL_ANA_MARIA_REFERENCE.warningTolerancePercent,
      );
      expect(comparison.operatorMessage).toBeTruthy();
      return;
    }

    expect(
      comparison.reasonIfMismatch.length,
      comparison.operatorMessage ?? "perimeter mismatch without reason",
    ).toBeGreaterThan(0);
    expect(comparison.operatorMessage).toMatch(/Corel măsoară/i);
  });

  it("logo perimeter comparison skipped when raster artwork has no vector perimeter", () => {
    const { report, confirmed } = analyzeUnlayered();
    const diagnostic = buildAnaMariaPerimeterDiagnostic(report, confirmed, FIXTURE);

    if (diagnostic.applicationMetrics.artworkLogoPerimeterM == null) {
      expect(diagnostic.comparison.logoDeltaPercent).toBeNull();
      expect(diagnostic.comparison.reasonIfMismatch).toContain("logo_excluded_as_artwork");
    }
  });
});
