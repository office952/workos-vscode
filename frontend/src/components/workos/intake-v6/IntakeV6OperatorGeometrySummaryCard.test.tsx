import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import IntakeV6OperatorGeometrySummaryCard from "@/components/workos/intake-v6/IntakeV6OperatorGeometrySummaryCard";
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
  return { geometry, metrics, report };
}

describe("IntakeV6OperatorGeometrySummaryCard", () => {
  it("shows width, height and full vector perimeter only", () => {
    const { geometry, metrics, report } = anaMariaUnlayeredContext();
    render(
      <IntakeV6OperatorGeometrySummaryCard
        geometry={geometry}
        metrics={metrics}
        widthMm={report.document.widthMm}
        heightMm={report.document.heightMm}
      />,
    );

    expect(screen.getByText("Dimensiune lucrare")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-operator-geometry-width")).toHaveTextContent(/mm/);
    expect(screen.getByTestId("intake-v6-operator-geometry-height")).toHaveTextContent(/mm/);
    expect(screen.getByTestId("intake-v6-operator-geometry-vector-perimeter")).toHaveTextContent(/31\.638/);
  });

  it("does not show production-only perimeter as the summary total", () => {
    const { geometry, metrics, report } = anaMariaUnlayeredContext();
    render(
      <IntakeV6OperatorGeometrySummaryCard
        geometry={geometry}
        metrics={metrics}
        widthMm={report.document.widthMm}
        heightMm={report.document.heightMm}
      />,
    );

    const summaryPerimeter = screen.getByTestId("intake-v6-operator-geometry-vector-perimeter").textContent ?? "";
    expect(summaryPerimeter).toMatch(/31\.638/);
    expect(summaryPerimeter).not.toMatch(/26\.747/);
  });

  it("does not show technical perimeter labels or character count", () => {
    const { geometry, metrics, report } = anaMariaUnlayeredContext();
    render(
      <IntakeV6OperatorGeometrySummaryCard
        geometry={geometry}
        metrics={metrics}
        widthMm={report.document.widthMm}
        heightMm={report.document.heightMm}
      />,
    );

    expect(screen.queryByText(/Perimetru LED/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Perimetru CNC față/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Cant \/ volum/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Artwork logo perimeter/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Caractere text/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Geometrie quote/i)).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-geometry-led-perimeter")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-geometry-cutting-perimeter")).not.toBeInTheDocument();
  });
});