import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { IntakeV6FaceBackPrepCostDraftResponse } from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";
import IntakeV6FaceBackPrepCostDraftSummaryCard from "./IntakeV6FaceBackPrepCostDraftSummaryCard";
import { useIntakeV6FaceBackPrepCostDraft } from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";

const fetchMock = vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>();

function mockDraftResponse(payload: IntakeV6FaceBackPrepCostDraftResponse): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function sampleDraft(): IntakeV6FaceBackPrepCostDraftResponse {
  return {
    workspace_id: "ws-1",
    template_key: "TPL-VOLUMETRIC-FACE-BACK-PREP",
    version: "v1-cnc-only",
    preview_only: true,
    currency: "EUR",
    materials: [],
    operations: [
      {
        operation_key: "cnc_cut_face_plexi",
        label: "Debitare CNC față plexiglas 3 mm",
        component: "FACE_PLEXI",
        task_key: "CUT_FACE_PLEXI",
        quantity: 26.747,
        unit: "ml",
        unit_price: 1.5,
        pass_count: 1,
        currency: "EUR",
        price_source: "fixed_rule",
        cost: 15,
        status: "calculated",
        perimeter_source: "cnc_cutting_perimeter_ml",
        perimeter_confidence: "high",
        is_vector_perimeter_source: true,
      },
    ],
    task_drafts: [],
    totals: {
      material_cost: 43.2,
      operation_cost: 75,
      total_internal_cost: 118.2,
      currency: "EUR",
    },
    missing_prices: [],
    manual_inputs_required: [],
    warnings: [],
    creates_real_tasks: false,
    consumes_stock: false,
    creates_quote: false,
    cnc_rate_eur_per_ml: 1.5,
  };
}

function SummaryHarness({ analysisReady }: { analysisReady: boolean }) {
  const viewModel = useIntakeV6FaceBackPrepCostDraft("ws-1", analysisReady);
  return <IntakeV6FaceBackPrepCostDraftSummaryCard analysisReady={analysisReady} viewModel={viewModel} />;
}

describe("IntakeV6FaceBackPrepCostDraftSummaryCard", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("shows compact totals and shanfren toggle default false", async () => {
    fetchMock.mockResolvedValue(mockDraftResponse(sampleDraft()));

    render(<SummaryHarness analysisReady />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/workspaces/ws-1/volumetric-face-back-prep/cost-draft?shanfren_forex=false"),
        expect.objectContaining({ credentials: "include", cache: "no-store" }),
      );
    });

    expect(screen.getByTestId("intake-v6-face-back-prep-summary-card")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-status-badge")).toHaveTextContent(
      "calculabil",
    );
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-perimeter")).toHaveTextContent(/26\.747/);
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-materials")).toHaveTextContent("43.20 EUR");
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-cnc")).toHaveTextContent("75.00 EUR");
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-total-internal")).toHaveTextContent(
      "118.20 EUR",
    );
    expect(screen.queryByTestId("intake-v6-face-back-prep-summary-verification-alert")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-face-back-prep-operations")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-face-back-prep-materials")).not.toBeInTheDocument();
  });

  it("shows coherent unavailable CNC state when perimeter verification is required", async () => {
    fetchMock.mockResolvedValue(
      mockDraftResponse({
        ...sampleDraft(),
        totals: { material_cost: 43.2, operation_cost: 75.06, total_internal_cost: null, currency: "EUR" },
        operations: sampleDraft().operations.map((row) => ({
          ...row,
          cost: null,
          status: "manual_required" as const,
        })),
        warnings: [
          {
            code: "vector_perimeter_missing_or_low_confidence",
            message: "Perimetru vectorial CNC față lipsă",
            severity: "warning",
          },
        ],
      }),
    );

    render(<SummaryHarness analysisReady />);

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-face-back-prep-summary-status-badge")).toHaveTextContent(
        "Necesită verificare perimetru",
      );
    });

    expect(screen.getByTestId("intake-v6-face-back-prep-summary-verification-alert")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-materials")).toHaveTextContent("43.20 EUR");
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-cnc")).toHaveTextContent(
      "indisponibil până la verificare perimetru",
    );
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-total-internal")).toHaveTextContent(
      "indisponibil",
    );
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-cnc")).not.toHaveTextContent("75.06");

    fireEvent.click(screen.getByTestId("intake-v6-face-back-prep-summary-technical-toggle"));
    expect(screen.getByTestId("intake-v6-face-back-prep-summary-ignored-raw-cnc")).toHaveTextContent(
      "75.06 EUR",
    );
  });

  it("refetches when shanfren toggle is enabled", async () => {
    fetchMock.mockResolvedValue(mockDraftResponse(sampleDraft()));

    render(<SummaryHarness analysisReady />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByTestId("intake-v6-face-back-prep-summary-shanfren-toggle"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenLastCalledWith(
        expect.stringContaining("/workspaces/ws-1/volumetric-face-back-prep/cost-draft?shanfren_forex=true"),
        expect.objectContaining({ credentials: "include", cache: "no-store" }),
      );
    });
  });
});