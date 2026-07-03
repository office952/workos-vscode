import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { IntakeV6FaceBackPrepCostDraftResponse } from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";
import IntakeV6FaceBackPrepCostDraftPanel from "./IntakeV6FaceBackPrepCostDraftPanel";

const fetchMock = vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>();

function mockDraftResponse(payload: IntakeV6FaceBackPrepCostDraftResponse): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function sampleDraft(
  overrides: Partial<IntakeV6FaceBackPrepCostDraftResponse> = {},
): IntakeV6FaceBackPrepCostDraftResponse {
  return {
    workspace_id: "ws-1",
    template_key: "TPL-VOLUMETRIC-FACE-BACK-PREP",
    version: "v1-cnc-only",
    preview_only: true,
    currency: "EUR",
    materials: [
      {
        component: "FACE_PLEXI",
        material_key: "plexiglas_3mm",
        material_label: "Plexiglas 3 mm — față litere",
        registry_code: "MAT-ACP-FATA-LITERE",
        thickness_mm: 3,
        quantity: 1.5,
        unit: "sqm",
        unit_price: 16,
        currency: "EUR",
        price_source: "prices_registry",
        cost: 24,
        status: "calculated",
      },
      {
        component: "BACK_FOREX",
        material_key: "forex_10mm",
        material_label: "Forex 10 mm — spate litere",
        registry_code: "MAT-SPATE-PVC-LITERE",
        thickness_mm: 10,
        quantity: 1.2,
        unit: "sqm",
        unit_price: 16,
        currency: "EUR",
        price_source: "prices_registry",
        cost: 19.2,
        status: "calculated",
      },
    ],
    operations: [
      {
        operation_key: "cnc_cut_face_plexi",
        label: "Debitare CNC față plexiglas 3 mm",
        component: "FACE_PLEXI",
        task_key: "CUT_FACE_PLEXI",
        quantity: 10,
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
      {
        operation_key: "cnc_shanfren_face_plexi",
        label: "Șanfren/canal CNC față plexiglas",
        component: "FACE_PLEXI",
        task_key: "SHANFREN_FACE_PLEXI",
        quantity: 10,
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
      {
        operation_key: "cnc_cut_back_forex",
        label: "Debitare CNC spate Forex 10 mm",
        component: "BACK_FOREX",
        task_key: "CUT_BACK_FOREX",
        quantity: 10,
        unit: "ml",
        unit_price: 1.5,
        pass_count: 3,
        currency: "EUR",
        price_source: "fixed_rule",
        cost: 45,
        status: "calculated",
        perimeter_source: "backing_cnc_cutting_perimeter_ml",
        perimeter_confidence: "high",
        is_vector_perimeter_source: true,
      },
    ],
    task_drafts: [
      {
        task_key: "PREPARE_CNC_FILES",
        label: "Pregătire fișiere CNC",
        station: "prepress",
        component: "GENERAL",
        order_index: 1,
        depends_on: [],
        cost_rows: [],
        creates_real_task: false,
        preview_only: true,
      },
      {
        task_key: "CUT_FACE_PLEXI",
        label: "Debitare față plexiglas 3 mm",
        station: "cnc",
        component: "FACE_PLEXI",
        order_index: 2,
        depends_on: ["PREPARE_CNC_FILES"],
        cost_rows: ["cnc_cut_face_plexi"],
        creates_real_task: false,
        preview_only: true,
      },
      {
        task_key: "SHANFREN_FACE_PLEXI",
        label: "Șanfren/canal CNC față plexiglas",
        station: "cnc",
        component: "FACE_PLEXI",
        order_index: 3,
        depends_on: ["CUT_FACE_PLEXI"],
        cost_rows: ["cnc_shanfren_face_plexi"],
        creates_real_task: false,
        preview_only: true,
      },
      {
        task_key: "CUT_BACK_FOREX",
        label: "Debitare spate Forex 10 mm",
        station: "cnc",
        component: "BACK_FOREX",
        order_index: 4,
        depends_on: ["PREPARE_CNC_FILES"],
        cost_rows: ["cnc_cut_back_forex"],
        creates_real_task: false,
        preview_only: true,
      },
      {
        task_key: "CLEAN_AND_CHECK_PARTS",
        label: "Curățare și verificare piese",
        station: "finishing",
        component: "GENERAL",
        order_index: 5,
        depends_on: ["SHANFREN_FACE_PLEXI", "CUT_BACK_FOREX"],
        cost_rows: [],
        creates_real_task: false,
        preview_only: true,
      },
      {
        task_key: "PACKAGE_FACE_BACK_PARTS",
        label: "Ambalare piese față + spate",
        station: "packing",
        component: "GENERAL",
        order_index: 6,
        depends_on: ["CLEAN_AND_CHECK_PARTS"],
        cost_rows: [],
        creates_real_task: false,
        preview_only: true,
      },
    ],
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
    ...overrides,
  };
}

describe("IntakeV6FaceBackPrepCostDraftPanel", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("shows unavailable message when analysis is not ready", () => {
    render(<IntakeV6FaceBackPrepCostDraftPanel workspaceId="ws-1" analysisReady={false} />);
    expect(screen.getByTestId("intake-v6-face-back-prep-unavailable")).toHaveTextContent(
      "Draft indisponibil: lipsesc date vectoriale.",
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fetches endpoint with shanfren_forex=false by default and displays pass counts and totals", async () => {
    fetchMock.mockResolvedValue(mockDraftResponse(sampleDraft()));

    render(<IntakeV6FaceBackPrepCostDraftPanel workspaceId="ws-1" analysisReady />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/workspaces/ws-1/volumetric-face-back-prep/cost-draft?shanfren_forex=false"),
        expect.objectContaining({ credentials: "include", cache: "no-store" }),
      );
    });

    expect(screen.getByTestId("intake-v6-face-back-prep-cost-draft-panel")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-face-back-prep-pass-count-CUT_FACE_PLEXI")).toHaveTextContent("1");
    expect(screen.getByTestId("intake-v6-face-back-prep-pass-count-CUT_BACK_FOREX")).toHaveTextContent("3");
    expect(screen.getByTestId("intake-v6-face-back-prep-totals")).toHaveTextContent("118.20 EUR");
    expect(screen.getByTestId("intake-v6-face-back-prep-task-drafts")).toHaveTextContent(
      "PREPARE_CNC_FILES → CUT_FACE_PLEXI → SHANFREN_FACE_PLEXI → CUT_BACK_FOREX",
    );
    expect(screen.getByTestId("intake-v6-face-back-prep-boundaries")).toHaveTextContent(
      "Nu creează quote",
    );
    expect(screen.queryByText(/Oracal/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/laminare/i)).not.toBeInTheDocument();
  });

  it("refetches endpoint when shanfren toggle is enabled", async () => {
    fetchMock.mockResolvedValue(mockDraftResponse(sampleDraft()));

    render(<IntakeV6FaceBackPrepCostDraftPanel workspaceId="ws-1" analysisReady />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    fetchMock.mockResolvedValue(
      mockDraftResponse(
        sampleDraft({
          operations: [
            ...sampleDraft().operations,
            {
              operation_key: "cnc_shanfren_back_forex",
              label: "Șanfren/canal CNC spate Forex",
              component: "BACK_FOREX",
              task_key: "SHANFREN_BACK_FOREX",
              quantity: 10,
              unit: "ml",
              unit_price: 1.5,
              pass_count: 2,
              currency: "EUR",
              price_source: "fixed_rule",
              cost: 30,
              status: "calculated_when_enabled",
              perimeter_source: "backing_cnc_cutting_perimeter_ml",
              perimeter_confidence: "high",
              is_vector_perimeter_source: true,
            },
          ],
        }),
      ),
    );

    fireEvent.click(screen.getByTestId("intake-v6-face-back-prep-shanfren-toggle"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenLastCalledWith(
        expect.stringContaining("/workspaces/ws-1/volumetric-face-back-prep/cost-draft?shanfren_forex=true"),
        expect.objectContaining({ credentials: "include", cache: "no-store" }),
      );
    });

    expect(screen.getByTestId("intake-v6-face-back-prep-pass-count-SHANFREN_BACK_FOREX")).toHaveTextContent(
      "2",
    );
  });

  it("shows vector perimeter warning prominently", async () => {
    fetchMock.mockResolvedValue(
      mockDraftResponse(
        sampleDraft({
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
              source: "vector_geometry",
            },
          ],
        }),
      ),
    );

    render(<IntakeV6FaceBackPrepCostDraftPanel workspaceId="ws-1" analysisReady />);

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-face-back-prep-vector-warning")).toHaveTextContent(
        "Necesită verificare perimetru",
      );
    });

    expect(screen.getByTestId("intake-v6-face-back-prep-totals-cnc")).toHaveTextContent(
      "indisponibil până la verificare perimetru",
    );
    expect(screen.getByTestId("intake-v6-face-back-prep-totals-cnc")).not.toHaveTextContent("75.06");
    expect(screen.getByTestId("intake-v6-face-back-prep-ignored-raw-cnc")).toHaveTextContent("75.06");
  });

  it("shows fetch error message", async () => {
    fetchMock.mockRejectedValue(new Error("network"));

    render(<IntakeV6FaceBackPrepCostDraftPanel workspaceId="ws-1" analysisReady />);

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-face-back-prep-error")).toHaveTextContent(
        "Nu s-a putut încărca draftul CNC față/spate.",
      );
    });
  });
});