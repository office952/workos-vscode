import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { analyzeSvgString } from "@/lib/svgAnalyzer/analyzer/analyzeSvg";
import { confirmAllSuggestedLayerRoles } from "@/lib/intakeV6/intakeV6LayerRoleBridge";
import IntakeV6SvgAnalyzerStep from "@/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep";
import { IntakeV6WorkspaceHeaderStatusProvider } from "@/components/workos/intake-v6/IntakeV6WorkspaceHeaderStatusContext";
import IntakeV6Header from "@/components/workos/intake-v6/atoms/IntakeV6Header";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../../../../lib/svgAnalyzer/fixtures");
const SEMANTIC_FIXTURE = "ana-maria-gradinita-fara-layere.svg";

function analyzeSemanticFixture() {
  const svg = readFileSync(join(fixtureDir, SEMANTIC_FIXTURE), "utf8");
  return analyzeSvgString(svg, SEMANTIC_FIXTURE, svg.length).report as unknown as SvgAnalysisCoreReport;
}

function mockSingleLayerReport(): SvgAnalysisCoreReport {
  const semantic = analyzeSemanticFixture();
  const baseLayer = semantic.layers[0]!;
  return {
    ...semantic,
    layers: [
      {
        ...baseLayer,
        id: "layer-1",
        name: "Layer_x0020_1",
        layerKind: "real",
        colors: ["#00A651", "#0066CC", "#E30613", "#F39200"],
        paintEvidence: {
          ...baseLayer.paintEvidence,
          paintKind: "solid",
          isMulticolor: true,
        },
      },
    ],
    colors: {
      unique: ["#00A651", "#0066CC", "#E30613", "#F39200", "#000000"],
      dominant: ["#00A651"],
      fills: ["#00A651", "#0066CC", "#E30613", "#F39200"],
      strokes: ["#000000"],
      byLayer: {},
    },
    geometry: {
      ...semantic.geometry,
      closedSubPathCount: 36,
    },
  };
}

function buildHook(
  report: SvgAnalysisCoreReport,
  fileName: string,
  confirmation?: LayerRoleConfirmation,
  previewSource?: string,
) {
  const resolvedConfirmation = confirmation ?? confirmAllSuggestedLayerRoles(report.layerRoleConfirmation);
  const svgSource =
    previewSource ??
    "<svg viewBox='0 0 100 20'><rect width='100' height='20'/></svg>";
  return {
    state: {
      phase: "svg_ready",
      currentStep: "layers",
      analyzerStatus: "ready",
      analyzerReport: report,
      layerRoleConfirmation: resolvedConfirmation,
      workspace: {
        id: "ws-test",
        workspace_code: "IV6-TEST",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        payload: {},
      },
      svg: {
        fileName,
        previewSource: svgSource,
      },
      layerChips: [],
    },
    importSvgFile: vi.fn(),
    updateLayerRole: vi.fn(),
    confirmAllLayerRoles: vi.fn(),
    canImportSvg: true,
  };
}

describe("IntakeV6SvgAnalyzerStep full-width layout", () => {
  it("uses full-width layers grid with preview column and operator panel", () => {
    const report = analyzeSemanticFixture();
    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE) as never} />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );

    const layout = screen.getByTestId("intake-v6-layers-layout");
    expect(layout.className).toContain("lg:grid-cols");
    expect(screen.getByTestId("intake-v6-layers-main-column")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layers-preview-panel")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layers-operator-panel")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-svg-preview")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layers-metrics-hero")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-open-preview-inspect")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-file-confirm-chip")).toHaveTextContent(SEMANTIC_FIXTURE);
  });

  it("shows semantic layers mode for multi pseudo-layer SVG", () => {
    const report = analyzeSemanticFixture();
    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE) as never} />);

    expect(screen.getByTestId("intake-v6-layers-layout")).toHaveAttribute(
      "data-intake-v6-layers-layout-mode",
      "semantic-layers",
    );
    expect(screen.getByTestId("intake-v6-layer-table")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layer-card-grid")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-layers-color-breakdown")).not.toBeInTheDocument();
    expect(screen.getAllByText(/pseudo maria/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByTestId("intake-v6-layers-warnings")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-pseudo-layer-warning-group")).toBeInTheDocument();
  });

  it("shows single-layer color breakdown when one structural layer is detected", () => {
    const report = mockSingleLayerReport();
    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, "gradi-curat.svg") as never} />);

    expect(screen.getByTestId("intake-v6-layers-layout")).toHaveAttribute(
      "data-intake-v6-layers-layout-mode",
      "single-color",
    );
    expect(screen.getByTestId("intake-v6-layers-color-breakdown")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layer-table")).toBeInTheDocument();
  });

  it("uses clear metric labels for vector and LED perimeter in advanced accordion", () => {
    const report = analyzeSemanticFixture();
    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE) as never} />);

    fireEvent.click(screen.getByTestId("intake-v6-layers-metrics-advanced-toggle"));

    expect(screen.getByText("Perimetru vectorial total")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layers-metric-vector-perimeter")).toHaveTextContent(/31\.638/);
    expect(screen.getByText("Perimetru LED / litere")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layers-metric-led-perimeter")).toHaveTextContent(/20\.880/);
  });

  it("opens inspect dialog with layer legend from preview button", () => {
    const report = analyzeSemanticFixture();
    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE) as never} />);

    fireEvent.click(screen.getByTestId("intake-v6-open-preview-inspect"));

    expect(screen.getByTestId("intake-v6-preview-inspect-dialog")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-preview-inspect-canvas")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layer-legend")).toBeInTheDocument();
    expect(screen.getAllByTestId(/intake-v6-layer-role-/).length).toBeGreaterThan(0);
  });

  it("highlights main grid preview when hovering a layer card", () => {
    const svg = readFileSync(join(fixtureDir, SEMANTIC_FIXTURE), "utf8");
    const report = analyzeSemanticFixture();
    const mariaLayer = report.layers.find((layer) => layer.name.toLowerCase().includes("maria"));
    expect(mariaLayer).toBeTruthy();

    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE, undefined, svg) as never} />);

    const mariaEntry = report.layerRoleConfirmation.layers.find((entry) =>
      entry.layerName?.toLowerCase().includes("maria"),
    );
    const mariaKey = mariaEntry?.layerKey ?? mariaLayer!.id;
    fireEvent.mouseEnter(screen.getByTestId(`intake-v6-layer-row-${mariaKey}`));

    const canvas = screen.getByTestId("intake-v6-svg-preview-canvas");
    const previewSvg = canvas.querySelector("svg");
    expect(previewSvg).toHaveAttribute("data-intake-v6-layer-highlight");
    expect(previewSvg?.querySelector(".intake-v6-svg-layer-active")).toBeTruthy();
    expect(previewSvg?.querySelector(".intake-v6-svg-layer-dim")).toBeTruthy();
  });

  it("highlights preview geometry when hovering a layer legend row", () => {
    const svg = readFileSync(join(fixtureDir, SEMANTIC_FIXTURE), "utf8");
    const report = analyzeSemanticFixture();
    const mariaLayer = report.layers.find((layer) => layer.name.toLowerCase().includes("maria"));
    expect(mariaLayer).toBeTruthy();

    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE, undefined, svg) as never} />);
    fireEvent.click(screen.getByTestId("intake-v6-open-preview-inspect"));

    const mariaEntry = report.layerRoleConfirmation.layers.find((entry) =>
      entry.layerName?.toLowerCase().includes("maria"),
    );
    const mariaKey = mariaEntry?.layerKey ?? mariaLayer!.id;
    fireEvent.mouseEnter(screen.getByTestId(`intake-v6-layer-legend-${mariaKey}`));

    const canvas = screen.getByTestId("intake-v6-preview-inspect-canvas-canvas");
    const previewSvg = canvas.querySelector("svg");
    expect(previewSvg).toHaveAttribute("data-intake-v6-layer-highlight");
    expect(previewSvg?.querySelector(".intake-v6-svg-layer-active")).toBeTruthy();
    expect(previewSvg?.querySelector(".intake-v6-svg-layer-dim")).toBeTruthy();
  });

  it("highlights left and right logo layers independently", () => {
    const svg = readFileSync(join(fixtureDir, SEMANTIC_FIXTURE), "utf8");
    const report = analyzeSemanticFixture();
    const leftLayer = report.layers.find((layer) => layer.name.toLowerCase().includes("logo stanga"));
    const rightLayer = report.layers.find((layer) => layer.name.toLowerCase().includes("logo dreapta"));
    expect(leftLayer).toBeTruthy();
    expect(rightLayer).toBeTruthy();

    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE, undefined, svg) as never} />);
    fireEvent.click(screen.getByTestId("intake-v6-open-preview-inspect"));

    const resolveKey = (layerName: string) =>
      report.layerRoleConfirmation.layers.find((entry) =>
        entry.layerName?.toLowerCase().includes(layerName),
      )?.layerKey ?? layerName;

    const leftKey = resolveKey("logo stanga");
    const rightKey = resolveKey("logo dreapta");
    const canvas = () => screen.getByTestId("intake-v6-preview-inspect-canvas-canvas");
    const activeCount = () => canvas().querySelectorAll(".intake-v6-svg-layer-active").length;

    fireEvent.mouseEnter(screen.getByTestId(`intake-v6-layer-legend-${leftKey}`));
    expect(activeCount()).toBeGreaterThan(0);
    const leftHighlight = canvas().querySelector("svg")?.getAttribute("data-intake-v6-layer-highlight");
    expect(leftHighlight).toBeTruthy();

    fireEvent.mouseEnter(screen.getByTestId(`intake-v6-layer-legend-${rightKey}`));
    const rightHighlight = canvas().querySelector("svg")?.getAttribute("data-intake-v6-layer-highlight");
    expect(rightHighlight).toBeTruthy();
    expect(rightHighlight).not.toBe(leftHighlight);
    expect(activeCount()).toBeGreaterThan(0);
  });

  it("keeps compact workspace header with single status badge", () => {
    const report = analyzeSemanticFixture();
    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6Header
          state={{
            phase: "svg_ready",
            currentStep: "layers",
            analyzerStatus: "idle",
            layerChips: [],
            workspace: {
              workspace_code: "IV6-TEST",
              template_code: "TPL-VOLUMETRIC-LETTERS",
            },
          } as never}
        />
        <IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE) as never} />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );

    expect(screen.getByTestId("intake-v6-header")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-workspace-status-badge")).toBeInTheDocument();
    expect(screen.queryByText("SVG ready")).not.toBeInTheDocument();
  });

  it("paginates layer cards when more than four layers are detected", () => {
    const report = analyzeSemanticFixture();
    expect(report.layers.length).toBeGreaterThan(4);

    render(<IntakeV6SvgAnalyzerStep hook={buildHook(report, SEMANTIC_FIXTURE) as never} />);

    expect(screen.getByTestId("intake-v6-layer-card-pagination")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layer-card-pagination-page")).toHaveTextContent("1/2");
    expect(screen.getAllByTestId(/intake-v6-layer-row-/).length).toBe(4);

    fireEvent.click(screen.getByTestId("intake-v6-layer-card-pagination-next"));

    expect(screen.getByTestId("intake-v6-layer-card-pagination-page")).toHaveTextContent("2/2");
    expect(screen.getAllByTestId(/intake-v6-layer-row-/).length).toBe(2);
  });

  it("exposes confirm-all and layer role controls without changing upload API", () => {
    const report = analyzeSemanticFixture();
    const pendingConfirmation = {
      ...report.layerRoleConfirmation,
      confirmationStatus: "pending" as const,
      layers: report.layerRoleConfirmation.layers.map((layer) => ({
        ...layer,
        confirmationState: "pending" as const,
      })),
    };

    render(
      <IntakeV6SvgAnalyzerStep
        hook={buildHook(report, SEMANTIC_FIXTURE, pendingConfirmation) as never}
      />,
    );

    expect(screen.getByTestId("intake-v6-confirm-all-roles")).toBeInTheDocument();
    expect(screen.getAllByTestId(/intake-v6-layer-role-/).length).toBeGreaterThan(0);
    expect(screen.getByTestId("intake-v6-layers-confirmation-summary")).toBeInTheDocument();
  });
});
