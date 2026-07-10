import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import IntakeV6ConfirmStep from "./steps/IntakeV6ConfirmStep";
import IntakeV6OperatorWorkspaceFooter from "./IntakeV6OperatorWorkspaceFooter";
import { IntakeV6WorkspaceHeaderStatusProvider } from "./IntakeV6WorkspaceHeaderStatusContext";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";

vi.mock("@/lib/intakeV6/useModularFormContract", () => ({
  useModularFormContract: () => ({
    contract: {
      summary: {
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        active_module_count: 2,
        field_binding_count: 0,
        warnings: [],
      },
      modules: [],
      field_bindings: [],
      trigger_alignments: [],
    },
    loading: false,
    error: null,
    templateCode: "TPL-VOLUMETRIC-LETTERS",
  }),
}));

vi.mock("@/lib/intakeV6/intakeV6Api", () => ({
  getIntakeV6ProductSystemBinding: vi.fn(),
  getIntakeV6MaterialBreakdown: vi.fn(),
  getIntakeV6NestingPreview: vi.fn(),
  getIntakeV6PricingInputPreview: vi.fn(),
  getIntakeV6PricedQuoteDryRun: vi.fn(),
  getIntakeV6QuoteHandoffPreview: vi.fn(),
  saveIntakeV6InternalDraftQuoteConfirmation: vi.fn(),
  createIntakeV6DraftQuote: vi.fn(),
  handoffIntakeV6ToOffer: vi.fn(),
}));

import {
  createIntakeV6DraftQuote,
  getIntakeV6PricedQuoteDryRun,
  getIntakeV6MaterialBreakdown,
  getIntakeV6NestingPreview,
  getIntakeV6PricingInputPreview,
  getIntakeV6ProductSystemBinding,
  getIntakeV6QuoteHandoffPreview,
  handoffIntakeV6ToOffer,
  saveIntakeV6InternalDraftQuoteConfirmation,
} from "@/lib/intakeV6/intakeV6Api";
import type { IntakeV6WorkspaceResponse } from "@/lib/intakeV6/intakeV6Api";

const mockedBinding = vi.mocked(getIntakeV6ProductSystemBinding);
const mockedBreakdown = vi.mocked(getIntakeV6MaterialBreakdown);
const mockedNesting = vi.mocked(getIntakeV6NestingPreview);
const mockedPricing = vi.mocked(getIntakeV6PricingInputPreview);
const mockedPricedDryRun = vi.mocked(getIntakeV6PricedQuoteDryRun);
const mockedHandoff = vi.mocked(getIntakeV6QuoteHandoffPreview);
const mockedSaveInternal = vi.mocked(saveIntakeV6InternalDraftQuoteConfirmation);
const mockedCreateQuote = vi.mocked(createIntakeV6DraftQuote);
const mockedPricedHandoff = vi.mocked(handoffIntakeV6ToOffer);

const handoffWithArtworkWarning = {
  workspace_id: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
  workspace_readiness_status: "ready_for_quote_preview",
  handoff_allowed: true,
  can_create_internal_draft_quote: true,
  status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW" as const,
  blockers: ["artwork_execution_undecided:Layer_x0020_1"],
  fatal_blockers: [],
  review_warnings: ["artwork_execution_undecided:Layer_x0020_1"],
  requires_operator_confirmation: true,
  operator_confirmation_complete: false,
  client_send_allowed: false,
  accept_allowed: false,
  convert_to_order_allowed: false,
  production_allowed: false,
  preview_only: true,
};

function buildHook(overrides: Partial<IntakeV6WorkspaceHook> = {}): IntakeV6WorkspaceHook {
  return {
    state: {
      workspace: {
        id: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
        workspace_code: "IV4-4B172FD4",
        title: "PBL",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        readiness_status: "ready_for_quote_preview",
        payload: {
          finish_setup: {
            face_finish_type: "none",
            return_finish_type: "standard_aluminum",
            return_depth_mm: 60,
            illuminated: true,
            emblem_lighting_mode: "area_lit",
            led_module_power_w: 1.44,
            confirmed: true,
            artwork_finishes: [
              {
                layer_key: "Layer_x0020_1",
                layer_name: "Layer_x0020_1",
                execution_type: "needs_decision",
                return_finish_type: "standard_aluminum",
              },
            ],
          },
          quote_geometry: {
            letter_perimeter_m: 11.6139,
            total_letter_perimeter_ml: 11.6139,
            face_area_m2: 0.6907,
            letter_count: 10,
            real_letters_count: 10,
            inner_holes_count: 5,
            return_material_perimeter_ml: 15.47,
            face_cutting_perimeter_ml: 13.62,
            artwork_piece_count: 1,
            artwork_boxes: [],
            letter_return_perimeter_ml: 15.47,
            artwork_return_perimeter_ml: null,
            led_perimeter_ml: 11.6139,
            volumetric_piece_count: 10,
          },
          svg_source: { file_hash: "a".repeat(64) },
        },
      },
      layerChips: [{ id: "1" }, { id: "2" }, { id: "3" }],
      svg: { fileName: "pbl-layere.svg" },
      localFileHash: "a".repeat(64),
      workspaceId: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
      phase: "ready",
      currentStep: "confirm",
      analyzerStatus: "ready",
    },
    isReadyForQuotePreview: true,
    firstBlocker: null,
    setStep: vi.fn(),
    trySetStep: vi.fn(),
    canAccessStep: vi.fn(),
    importSvgFile: vi.fn(),
    updateLayerRole: vi.fn(),
    confirmAllLayerRoles: vi.fn(),
    continueFromAnalyzer: vi.fn(),
    saveFinishSetup: vi.fn(),
    canImportSvg: true,
    canContinueFromAnalyzer: true,
    canContinueFromReview: true,
    ...overrides,
  } as IntakeV6WorkspaceHook;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedBinding.mockResolvedValue({
    workspace_id: "ws",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    template_label: "Litere volumetrice",
    template_active: true,
    operation_count: 10,
    component_count: 5,
    module_links: [],
    blockers: [],
  });
  mockedBreakdown.mockResolvedValue({
    workspace_id: "ws",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    breakdown_scope: "quote_estimate",
    stock_consumption: false,
    nesting_rows: [],
    material_rows: [
      {
        material_key: "plexiglas_face",
        display_name: "Plexiglas față",
        category: "material",
        quantity: 0.5834,
        unit: "m2",
        quantity_source: "nesting",
        quantity_quality: "estimate",
        quantity_with_waste: 0.5834,
        currency: "RON",
        price_source: "registry",
        warnings: [],
        priced_quantity: 0.5834,
      },
    ],
    consumable_rows: [],
    operation_rows: [],
    edge_cant_operation_rows: [],
    totals: {
      material_cost_total: 0,
      estimated_cost_total: 0,
      currency: "RON",
      contains_estimates: false,
      contains_missing_prices: false,
    },
    warnings: [],
  });
  mockedNesting.mockResolvedValue({
    preview_mode: "bounding_box_mvp",
    preview_only: true,
    mutates_inventory: false,
    uses_stock: false,
    source: "intake_v6",
    disclaimer: "",
    active_sheet_config_id: "sheet-1",
    breakdown_uses_single_active_layout: true,
    boundary: {
      preview_only: true,
      mutates_inventory: false,
      uses_stock: false,
      creates_execution_plan: false,
      creates_execution_tasks: false,
      consumes_stock: false,
      used_for_stock_reservation: false,
    },
    summary: {
      sheet_layouts: 1,
      roll_layouts: 0,
      active_sheet_layouts: 1,
      active_roll_layouts: 0,
      alternative_layouts: 0,
      nestable_parts: 10,
      holes_excluded: 5,
      artwork_parts: 1,
    },
    sheets: [],
    rolls: [],
    parts: [],
    material_traces: [],
    warnings: [],
  });
  mockedPricing.mockResolvedValue({
    workspace_id: "ws",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    is_ready_for_quote: true,
    adapter_status: "ready_for_internal_quote_preview",
    adapter_blockers: [],
    adapter_warnings: [],
    quote_input_payload: {},
    operation_flags: {},
    production_counts: {
      letter_count: 10,
      cut_contour_count: 10,
      inner_hole_count: 5,
    },
    finish_summary: {},
    readiness_status: "ready_for_quote_preview",
    requires_grouped_finish_review: false,
    preview_only: true,
  });
  mockedPricedDryRun.mockResolvedValue({
    pricing_status: "V6_PRICED_DRY_RUN_READY",
    workspace_id: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
    pricing_source: "intake_v6_backend_priced_dry_run",
    commercial_totals: {
      subtotal_net: 1000,
      vat_rate: 21,
      vat_amount: 210,
      total_gross: 1210,
      currency: "RON",
    },
    blockers: [],
    commercial_line_items: [{ code: "face", total: 1000 }],
    pricing_hash: "hash-123",
  });
  mockedHandoff.mockResolvedValue(handoffWithArtworkWarning);
  const savedWorkspace: IntakeV6WorkspaceResponse = {
    id: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
    workspace_code: "IV4-4B172FD4",
    title: "PBL",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    status: "ready_for_quote_preview",
    readiness_status: "ready_for_quote_preview",
    created_at: null,
    updated_at: null,
    payload: {},
  };
  mockedSaveInternal.mockResolvedValue(savedWorkspace);
});

function renderConfirmStep(hook: IntakeV6WorkspaceHook = buildHook()) {
  return render(
    <MemoryRouter>
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6ConfirmStep hook={hook} />
        <IntakeV6OperatorWorkspaceFooter
          currentStep="review"
          stepIndex={1}
          stepOrderLength={2}
          footerBlocker={null}
          nextDisabled
          nextLabel=""
          nextButtonClassName=""
          onBack={() => {}}
          onNext={() => {}}
          persisting={false}
          workspaceState={hook.state}
        />
      </IntakeV6WorkspaceHeaderStatusProvider>
    </MemoryRouter>,
  );
}

describe("IntakeV6ConfirmStep", () => {
  it("shows owner-facing summary labels with legacy page title expanded by default", async () => {
    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-tile-work")).toBeInTheDocument();
    });

    expect(screen.getByText("Confirmare draft intern")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-confirm-dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-confirm-tile-verdict")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-confirm-tile-geometry")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-confirm-handoff-summary-above-fold")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-price-spine-bar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-confirm-consolidated-status")).not.toBeInTheDocument();

    expect(screen.queryByText("Piese producție")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-final-configuration-technical-details-toggle")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("intake-v6-final-configuration-technical-details-toggle"));
    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-operational-technical-details-toggle")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("intake-v6-confirm-operational-technical-details-toggle"));
    await waitFor(() => {
      expect(
        screen.getByTestId("intake-v6-confirm-work-summary-technical-production-parts"),
      ).toHaveTextContent("10");
    });
  });

  it("shows inline status and artwork warning when only review warnings exist", async () => {
    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-final-config-status")).toBeInTheDocument();
    });

    expect(screen.getByTestId("intake-v6-confirm-tile-verdict")).toBeInTheDocument();
    expect(screen.getAllByTestId("intake-v6-create-internal-draft")).toHaveLength(1);
    expect(screen.getByTestId("intake-v6-create-internal-draft")).toBeDisabled();
    expect(screen.getByTestId("intake-v6-confirm-internal-draft")).toBeEnabled();
  });

  it("keeps internal confirmation enabled when operator confirmation itself blocks handoff", async () => {
    mockedHandoff.mockResolvedValue({
      ...handoffWithArtworkWarning,
      handoff_allowed: false,
      can_create_internal_draft_quote: false,
      status_label: "QUOTE_HANDOFF_BLOCKED",
      blockers: ["operator_confirmation_missing", "unclassified_vector_artwork_requires_decision"],
      fatal_blockers: ["operator_confirmation_missing"],
      review_warnings: ["unclassified_vector_artwork_requires_decision"],
      operator_confirmation_complete: false,
    });

    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-internal-draft")).toBeEnabled();
    });

    expect(screen.getByTestId("intake-v6-confirm-consolidated-observations")).toHaveTextContent(
      /Confirmă finisajele/i,
    );
    expect(screen.getByTestId("intake-v6-create-internal-draft")).toBeDisabled();
  });

  it("enables create draft after operator internal confirmation and boundary checkbox", async () => {
    mockedHandoff
      .mockResolvedValueOnce(handoffWithArtworkWarning)
      .mockResolvedValueOnce({
        ...handoffWithArtworkWarning,
        operator_confirmation_complete: true,
      });

    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-internal-draft")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("intake-v6-confirm-internal-draft"));
    await waitFor(() => {
      expect(mockedSaveInternal).toHaveBeenCalledWith("0f300dcf-0b77-4fc1-affd-6e2a20329804", {
        confirmed: true,
      });
    });

    fireEvent.click(screen.getByTestId("intake-v6-confirm-draft-boundary"));

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-create-internal-draft")).toBeEnabled();
    });
  });

  it("hides internal confirmation when finish setup is incomplete", async () => {
    mockedHandoff.mockResolvedValue({
      ...handoffWithArtworkWarning,
      handoff_allowed: false,
      can_create_internal_draft_quote: false,
      status_label: "QUOTE_HANDOFF_BLOCKED",
      fatal_blockers: ["finish_setup_not_confirmed"],
      review_warnings: [],
      blockers: ["finish_setup_not_confirmed"],
    });

    renderConfirmStep(
      buildHook({
        isReadyForQuotePreview: false,
        firstBlocker: "Finish setup is not confirmed.",
        state: {
          ...buildHook().state,
          workspace: {
            ...buildHook().state.workspace!,
            readiness_status: "finish_setup_incomplete",
          },
        },
      }),
    );

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-finish-setup-incomplete")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("intake-v6-confirm-internal-draft")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-create-internal-draft")).toBeDisabled();
  });

  it("keeps create draft disabled for fatal blockers", async () => {
    mockedHandoff.mockResolvedValue({
      ...handoffWithArtworkWarning,
      handoff_allowed: false,
      can_create_internal_draft_quote: false,
      status_label: "QUOTE_HANDOFF_BLOCKED",
      fatal_blockers: ["missing_face_oracal_color:group-1"],
      review_warnings: [],
      blockers: ["missing_face_oracal_color:group-1"],
    });

    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-final-config-status")).toHaveAttribute(
        "data-status-tier",
        "blocked",
      );
    });
    expect(screen.getByTestId("intake-v6-create-internal-draft")).toBeDisabled();
    expect(mockedCreateQuote).not.toHaveBeenCalled();
  });

  it("creates draft quote on success path", async () => {
    mockedHandoff
      .mockResolvedValueOnce(handoffWithArtworkWarning)
      .mockResolvedValueOnce({
        ...handoffWithArtworkWarning,
        operator_confirmation_complete: true,
      });
    mockedCreateQuote.mockResolvedValue({
      quote_id: 99,
      quote_code: "Q-TEST-99",
      quote_input_payload: { ok: true },
    });

    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-internal-draft")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("intake-v6-confirm-internal-draft"));
    await waitFor(() => {
      expect(mockedSaveInternal).toHaveBeenCalled();
    });
    fireEvent.click(screen.getByTestId("intake-v6-confirm-draft-boundary"));
    fireEvent.click(screen.getByTestId("intake-v6-create-internal-draft"));

    await waitFor(() => {
      expect(mockedCreateQuote).toHaveBeenCalled();
      expect(screen.getByTestId("intake-v6-quote-created")).toHaveTextContent("Q-TEST-99");
    });
  });

  it("creates priced quote through V6 handoff after explicit confirmation", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    mockedHandoff
      .mockResolvedValueOnce(handoffWithArtworkWarning)
      .mockResolvedValueOnce({
        ...handoffWithArtworkWarning,
        operator_confirmation_complete: true,
      });
    mockedPricedHandoff.mockResolvedValue({
      status: "V6_PRICED_QUOTE_WRITTEN",
      quote_created: true,
      quote_id: 101,
      quote_code: "Q-V6-IV6-PRICED-1",
      quote_status: "priced",
      source_workspace_id: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
      blockers: [],
      warnings: [],
      can_create_quote_snapshot: true,
      next_route: "/quotes/Q-V6-IV6-PRICED-1",
    });

    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-internal-draft")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("intake-v6-confirm-internal-draft"));
    await waitFor(() => {
      expect(mockedSaveInternal).toHaveBeenCalled();
    });
    fireEvent.click(screen.getByTestId("intake-v6-confirm-draft-boundary"));

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-create-priced-quote")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("intake-v6-create-priced-quote"));

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith(expect.stringContaining("nu creeaza comanda"));
      expect(mockedPricedHandoff).toHaveBeenCalledWith("0f300dcf-0b77-4fc1-affd-6e2a20329804", {
        client_analysis_hash: "a".repeat(64),
        expected_total_gross: 1210,
        expected_pricing_hash: "hash-123",
        operator_confirmation: true,
      });
    });

    confirmSpy.mockRestore();
  });

  it("shows inline configuration status with recap tile", async () => {
    mockedHandoff.mockResolvedValue({
      ...handoffWithArtworkWarning,
      operator_confirmation_complete: true,
    });

    renderConfirmStep();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-final-config-status")).toBeInTheDocument();
    });

    expect(screen.getByTestId("intake-v6-confirm-tile-recap-note")).toBeInTheDocument();
  });
});
