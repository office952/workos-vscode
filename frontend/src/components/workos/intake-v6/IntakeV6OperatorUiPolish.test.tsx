import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import IntakeV6MaterialBreakdownPanel from "@/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel";
import IntakeV6ReviewLetterGroupsSection from "@/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection";
import IntakeV6ReviewSectionShell from "@/components/workos/intake-v6/atoms/IntakeV6ReviewSectionShell";
import IntakeV6Header from "@/components/workos/intake-v6/atoms/IntakeV6Header";
import IntakeV6OperatorWorkspace from "@/components/workos/intake-v6/IntakeV6OperatorWorkspace";
import { IntakeV6WorkspaceHeaderStatusProvider } from "@/components/workos/intake-v6/IntakeV6WorkspaceHeaderStatusContext";
import IntakeV6SvgPreviewCanvas from "@/components/workos/intake-v6/IntakeV6SvgPreviewCanvas";
import type { IntakeV6MaterialBreakdownResponse } from "@/lib/intakeV6/intakeV6Api";

function breakdownWithMixedOperations(): IntakeV6MaterialBreakdownResponse {
  return {
    workspace_id: "ws-1",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    breakdown_scope: "quote_material_cost_estimate",
    nesting_rows: [],
    material_rows: [],
    consumable_rows: [],
    operation_rows: [
      {
        key: "cnc_face_cutting_plexiglas_3mm",
        display_name: "Debitare CNC față Plexiglas 3 mm",
        operation_type: "cutting",
        quantity: 25.02,
        unit: "ml",
        passes: 1,
        pricing_status: "missing_rate",
      },
      {
        key: "logo-dreapta_print_vinyl_op",
        display_name: "Imprimare autocolant — logo dreapta",
        operation_type: "print_vinyl",
        quantity: 0.45,
        unit: "m2",
        passes: 1,
        pricing_status: "missing_rate",
      },
      {
        key: "logo-dreapta_laminate_op",
        display_name: "Laminare autocolant — logo dreapta",
        operation_type: "lamination",
        quantity: 0.45,
        unit: "m2",
        passes: 1,
        pricing_status: "missing_rate",
      },
    ],
    edge_cant_operation_rows: [],
    totals: {
      material_cost_total: 0,
      estimated_cost_total: 0,
      currency: "EUR",
      contains_estimates: false,
      contains_missing_prices: true,
    },
    warnings: [],
  };
}

describe("IntakeV6OperatorUiPolish", () => {
  it("separates CNC and print/laminare sections", () => {
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdownWithMixedOperations()} loading={false} />);
    expect(screen.getByTestId("intake-v6-cnc-operation-rows")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-print-operation-rows")).toBeInTheDocument();
    expect(screen.getByText("Operații print / laminare / colantare — preview ofertare")).toBeInTheDocument();
    expect(screen.queryByText("Imprimare autocolant — logo dreapta")).toBeInTheDocument();
    expect(screen.getByText(/25\.02 m/)).toBeInTheDocument();
    expect(screen.queryByText(/25\.02 ml/)).not.toBeInTheDocument();
  });

  it("shows material estimate disclaimer not final quote wording", () => {
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdownWithMixedOperations()} loading={false} />);
    expect(screen.getByText(/Estimare internă materiale — informativ/)).toBeInTheDocument();
    expect(screen.getAllByText(/Nu este preț final ofertă/).length).toBeGreaterThan(0);
    expect(screen.queryByText("Total estimat materiale \(ofertă\)")).not.toBeInTheDocument();
  });

  it("shows controlled missing raster placeholder on SVG preview", () => {
    render(<IntakeV6SvgPreviewCanvas source="<svg></svg>" missingExternalRaster />);
    expect(screen.getByTestId("intake-v6-svg-preview-missing-raster-banner")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-svg-preview-raster-placeholder")).toBeInTheDocument();
    expect(screen.getByText(/Preview incomplet: SVG-ul face referire la imagini externe/)).toBeInTheDocument();
    expect(screen.getByText("Imagine externă lipsă — preview geometric disponibil")).toBeInTheDocument();
  });

  it("does not expose raw internal ids in operation labels", () => {
    const breakdown = breakdownWithMixedOperations();
    breakdown.operation_rows![1].display_name = "Imprimare autocolant — _2209257786352";
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} />);
    expect(screen.queryByText(/_2209257786352/)).not.toBeInTheDocument();
    expect(screen.getByText(/Imprimare autocolant — artwork layer/)).toBeInTheDocument();
  });

  it("keeps face and cant in unified layer cards for review", () => {
    const groups = [
      {
        group_key: "a",
        layer_name: "Strat A",
        face_finish_type: "oracal_651",
        return_finish_type: "white_aluminum",
        return_depth_mm: 60,
        confirmed: false,
      },
    ];
    render(
      <IntakeV6ReviewSectionShell title="Finisaje pe layer" testId="intake-v6-review-section-face-letters">
        <IntakeV6ReviewLetterGroupsSection groups={groups} onChange={() => undefined} />
      </IntakeV6ReviewSectionShell>,
    );
    expect(screen.getByTestId("intake-v6-review-section-face-letters")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-face-finishes")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-cant-finishes")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-letter-group-header-a"));
    expect(screen.getByTestId("intake-v6-face-letter-zone-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-cant-letter-zone-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-header-a")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-letter-group-face-a")).not.toBeInTheDocument();
  });

  it("uses workspace shell header with single status badge", () => {
    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6Header
          state={{
            phase: "svg_ready",
            currentStep: "review",
            analyzerStatus: "idle",
            layerChips: [],
            workspace: {
              workspace_code: "IV6-TEST",
              template_code: "TPL-VOLUMETRIC-LETTERS",
            },
          } as never}
        />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );
    expect(screen.getByTestId("intake-v6-header")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-workspace-status-badge")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-status-bar")).not.toBeInTheDocument();
    expect(screen.queryByText("SVG ready")).not.toBeInTheDocument();
  });

  it("uses full-width workspace main shell for all steps", () => {
    render(
      <MemoryRouter initialEntries={["/intake-v6/ws/operator"]}>
        <IntakeV6WorkspaceHeaderStatusProvider>
          <IntakeV6OperatorWorkspace
            hook={{
              state: {
                phase: "svg_ready",
                currentStep: "layers",
                analyzerStatus: "idle",
                layerChips: [],
                workspace: { workspace_code: "IV6-TEST", template_code: "TPL-VOLUMETRIC-LETTERS" },
              },
              trySetStep: () => undefined,
              canAccessStep: () => true,
              continueFromAnalyzer: async () => undefined,
              canContinueFromAnalyzer: false,
              canContinueFromReview: false,
              firstBlocker: null,
            } as never}
          />
        </IntakeV6WorkspaceHeaderStatusProvider>
      </MemoryRouter>,
    );
    const main = screen.getByTestId("intake-v6-workspace-main");
    expect(main.className).toContain("max-w-none");
    expect(main.className).not.toContain("max-w-[920px]");
    expect(main.className).toContain("pb-[var(--intake-v6-footer-safe-area)]");
    expect(screen.getByTestId("intake-v6-layers-layout")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layers-operator-panel")).toBeInTheDocument();
  });
});