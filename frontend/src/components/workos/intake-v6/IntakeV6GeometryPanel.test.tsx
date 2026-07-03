import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import IntakeV6GeometryPanel from "@/components/workos/intake-v6/IntakeV6GeometryPanel";
import { confirmAllSuggestedLayerRoles } from "@/lib/intakeV6/intakeV6LayerRoleBridge";
import { buildIntakeV6GeometryMetricDisplay } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import { resolveQuoteGeometryForWorkspace } from "@/lib/intakeV6/intakeV6QuoteGeometry";
import { analyzeSvgString } from "@/lib/svgAnalyzer/analyzer/analyzeSvg";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../../../lib/svgAnalyzer/fixtures");
const UNLAYERED = "ana-maria-gradinita-fara-layere.svg";

function anaMariaUnlayeredContext() {
  const svg = readFileSync(join(fixtureDir, UNLAYERED), "utf8");
  const analyzed = analyzeSvgString(svg, UNLAYERED, svg.length);
  const report = analyzed.report as unknown as SvgAnalysisCoreReport;
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
  return { geometry, metrics };
}

describe("IntakeV6GeometryPanel Ana Maria metrics", () => {
  it("does not show bare production count as litere without context", () => {
    const { geometry, metrics } = anaMariaUnlayeredContext();
    render(<IntakeV6GeometryPanel geometry={geometry} metrics={metrics} scopeWarnings={[]} />);

    expect(screen.queryByText("Litere / piese reale")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-geometry-production-parts")).toHaveTextContent("19");
    expect(screen.getByTestId("intake-v6-geometry-volumetric-groups")).toHaveTextContent("4");
    expect(screen.getByTestId("intake-v6-geometry-character-count")).toHaveTextContent("n/a");
    expect(screen.getByTestId("intake-v6-geometry-artwork-count")).toHaveTextContent("2");
  });

  it("shows Corel-comparable, LED, CNC, cant and raster artwork perimeter labels", () => {
    const { geometry, metrics } = anaMariaUnlayeredContext();
    render(<IntakeV6GeometryPanel geometry={geometry} metrics={metrics} scopeWarnings={[]} />);

    expect(screen.getByTestId("intake-v6-geometry-full-vector-perimeter").textContent).toMatch(/31\.638/);
    expect(screen.getByTestId("intake-v6-geometry-corel-curve-length").textContent).toMatch(/26\.747/);
    expect(screen.getByTestId("intake-v6-geometry-led-perimeter").textContent).toMatch(/20\.880/);
    expect(screen.getByTestId("intake-v6-geometry-cutting-perimeter").textContent).toMatch(/24\.073/);
    expect(screen.getByTestId("intake-v6-geometry-return-perimeter")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-geometry-artwork-perimeter")).toHaveTextContent(/4\.891/);
    expect(screen.getByTestId("intake-v6-geometry-artwork-perimeter-diagnostic-note")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-logo-warnings")).toBeInTheDocument();
  });

  it("shows cant section and analysis-bundle pending on analyzer step", () => {
    const { geometry, metrics } = anaMariaUnlayeredContext();
    render(<IntakeV6GeometryPanel geometry={geometry} metrics={metrics} scopeWarnings={[]} />);

    expect(screen.getByTestId("intake-v6-geometry-cant-section")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-geometry-cant-pending")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-geometry-soare-note")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-geometry-analysis-bundle-pending")).toBeInTheDocument();
  });

  it("shows LED separately from cant calculated when enriched", () => {
    const geometry = {
      letter_perimeter_m: 11.63,
      total_letter_perimeter_ml: 11.63,
      return_material_perimeter_ml: 15.47,
      face_cutting_perimeter_ml: 13.62,
      cutting_perimeter_ml: 13.62,
      hole_perimeter_ml: 1.84,
      face_area_m2: 0.69,
      artwork_area_m2: null,
      artwork_boxes: [],
      letter_count: 10,
      real_letters_count: 10,
      inner_holes_count: 5,
      cutting_contours_count: 15,
      material_piece_count: 10,
      letter_return_perimeter_ml: 15.47,
      artwork_return_perimeter_ml: null,
      led_perimeter_ml: 11.63,
      artwork_piece_count: null,
      volumetric_piece_count: 10,
      part_classification_confidence: "high" as const,
      primary_letters_layer_key: "Layer_x0020_1",
      width_mm: 2700,
      height_mm: 350,
      geometry_source: "nest2_face_parts_outer" as const,
      confirmed: true,
    };

    render(
      <IntakeV6GeometryPanel
        geometry={geometry}
        metrics={buildIntakeV6GeometryMetricDisplay({
          report: null,
          confirmation: null,
          geometry,
          analysisBundleReady: true,
          finishSetup: {
            return_finish_type: "white_aluminum",
            return_depth_mm: 60,
            letter_group_finishes: [{ group_key: "a", layer_name: "a" }],
          },
        })}
        scopeWarnings={[]}
      />,
    );

    expect(screen.getByTestId("intake-v6-geometry-led-perimeter")).toHaveTextContent("11.630 m");
    expect(screen.getByTestId("intake-v6-geometry-return-perimeter")).toHaveTextContent("15.470 m");
    expect(screen.getByText("Perimetru LED litere — exterior only")).toBeInTheDocument();
    expect(screen.getByText(/Cant \/ volum litere/)).toBeInTheDocument();
  });
});