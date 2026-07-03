import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buildLayerRoleConfirmationDraft } from "./buildLayerRoleConfirmation";
import { analyzeSvgString } from "./analyzeSvg";
import { confirmAllSuggestedLayerRoles } from "@/lib/intakeV4/intakeV4LayerRoleBridge";
import { resolveQuoteGeometryForWorkspace } from "@/lib/intakeV4/intakeV4QuoteGeometry";
import {
  buildLayerRoleRowsForDisplay,
  countArtworkLayers,
  countProductionGeometryLayers,
} from "@/lib/intakeV4/intakeV4LayerRoleDisplay";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");

function analyzeFixture(fileName: string) {
  const svg = readFileSync(join(fixtureDir, fileName), "utf8");
  return analyzeSvgString(svg, fileName, svg.length);
}

const LAYERED_LETTER_NAMES = ["gradinita", "ana", "maria", "soare"];
const LAYERED_LOGO_NAMES = ["logo stanga", "logo dreapta"];

describe("ana-maria six-layer classification", () => {
  it("layered SVG detects 6 semantic layers with correct roles", () => {
    const { report } = analyzeFixture("ana-maria-gradinita.svg");
    expect(report.layers.length).toBe(6);

    for (const name of LAYERED_LETTER_NAMES) {
      const layer = report.layers.find((entry) => entry.name === name);
      expect(layer, `missing letter layer ${name}`).toBeTruthy();
      expect(layer?.layerKind).toBe("real");
      expect(layer?.autoRole).toBe("face");
      expect(layer?.autoConfidence).toBe("high");
    }

    for (const name of LAYERED_LOGO_NAMES) {
      const layer = report.layers.find((entry) => entry.name === name);
      expect(layer, `missing logo layer ${name}`).toBeTruthy();
      expect(layer?.layerKind).toBe("real");
      expect(layer?.autoRole).toBe("printed_artwork");
    }

    expect(countProductionGeometryLayers(report)).toBe(4);
    expect(countArtworkLayers(report)).toBe(2);
  });

  it("unlayered SVG generates 6 pseudo layers with semantic names", () => {
    const { report } = analyzeFixture("ana-maria-gradinita-fara-layere.svg");
    expect(report.layers.length).toBe(6);

    const pseudoLetters = report.layers.filter((layer) => layer.layerKind === "pseudo");
    const artworkLayers = report.layers.filter(
      (layer) => layer.layerKind === "raster_artwork" || layer.autoRole === "printed_artwork",
    );

    expect(pseudoLetters.length).toBe(4);
    expect(artworkLayers.length).toBe(2);
    expect(pseudoLetters.every((layer) => layer.autoRole === "face")).toBe(true);
    expect(artworkLayers.every((layer) => layer.autoRole === "printed_artwork")).toBe(true);

    expect(report.layers.some((layer) => layer.name.includes("gradinita"))).toBe(true);
    expect(report.layers.some((layer) => layer.name.includes("ana"))).toBe(true);
    expect(report.layers.some((layer) => layer.name.includes("maria"))).toBe(true);
    expect(report.layers.some((layer) => layer.name.includes("soare"))).toBe(true);
    expect(report.layers.some((layer) => layer.name.includes("logo stanga"))).toBe(true);
    expect(report.layers.some((layer) => layer.name.includes("logo dreapta"))).toBe(true);
  });

  it("unlayered stroke-only logo vectors are operator-visible artwork layers", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="20mm" viewBox="0 0 100 20">
        <g id="Layer_x0020_1">
          <path fill="#00A0E3" d="M20 2 L28 2 L28 18 L20 18 Z"/>
          <path fill="#E31E24" d="M35 2 L43 2 L43 18 L35 18 Z"/>
          <path fill="#009846" d="M50 2 L58 2 L58 18 L50 18 Z"/>
          <path fill="#EF7F1A" d="M65 2 L73 2 L73 18 L65 18 Z"/>
          <path fill="none" stroke="#2B2A29" d="M2 4 L12 4 L12 16 L2 16 Z"/>
          <path fill="none" stroke="#2B2A29" d="M88 4 L98 4 L98 16 L88 16 Z"/>
        </g>
      </svg>
    `;
    const { report } = analyzeSvgString(svg, "stroke-logo-vectors.svg", svg.length);

    expect(report.layers.length).toBe(6);
    const logoLayers = report.layers.filter(
      (layer) => layer.id === "logo-stanga" || layer.id === "logo-dreapta",
    );
    expect(logoLayers.map((layer) => layer.name).sort()).toEqual(["logo dreapta", "logo stanga"]);
    expect(logoLayers.every((layer) => layer.autoRole === "printed_artwork")).toBe(true);
    expect(logoLayers.every((layer) => layer.layerOrigin === "stroke_vector_outline")).toBe(true);
    expect(logoLayers.every((layer) => layer.pathElementCount === 1)).toBe(true);
    expect(
      logoLayers.every((layer) =>
        layer.warnings.some((warning) => warning.code === "STROKE_ONLY_VECTOR_LAYER"),
      ),
    ).toBe(true);
  });

  it("image elements are not child parts on both fixtures", () => {
    for (const file of ["ana-maria-gradinita.svg", "ana-maria-gradinita-fara-layere.svg"]) {
      const { report } = analyzeFixture(file);
      const imageParts = report.parts.items.filter((part) => part.sourceElementType === "image");
      expect(imageParts.length).toBe(0);
    }
  });

  it("confirm-all clears missing and geometry sees production layers", () => {
    for (const file of ["ana-maria-gradinita.svg", "ana-maria-gradinita-fara-layere.svg"]) {
      const { report } = analyzeFixture(file);
      const draft = buildLayerRoleConfirmationDraft(report.layers);
      const confirmed = confirmAllSuggestedLayerRoles(draft);
      expect(confirmed.confirmationStatus).toBe("complete");

      const geometry = resolveQuoteGeometryForWorkspace({
        analyzerReport: report,
        layerRoleConfirmation: confirmed,
      });
      expect(geometry.geometry_source).not.toBe("missing");
      expect((geometry.real_letters_count ?? geometry.letter_count ?? 0) > 0).toBe(true);
    }
  });

  it("artwork complexity recommends print_on_vinyl_laminated", () => {
    const { report } = analyzeFixture("ana-maria-gradinita.svg");
    expect(report.artworkComplexity?.assessments?.length).toBeGreaterThan(0);
    expect(
      report.artworkComplexity?.assessments?.some(
        (item) => item.recommended_application === "print_on_vinyl_laminated",
      ),
    ).toBe(true);
  });

  it("layer role display rows expose six operator-visible entries", () => {
    const { report } = analyzeFixture("ana-maria-gradinita.svg");
    const draft = buildLayerRoleConfirmationDraft(report.layers);
    const rows = buildLayerRoleRowsForDisplay(report, draft);
    expect(rows.length).toBe(6);
    expect(rows.filter((row) => row.selectedRoleLabel.includes("Față litere")).length).toBe(4);
    expect(rows.filter((row) => row.selectedRoleLabel.includes("Artwork")).length).toBe(2);
  });
});
