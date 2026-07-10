import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import IntakeV6FinalConfigurationSummary from "./IntakeV6FinalConfigurationSummary";
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
  getIntakeV6MaterialBreakdown,
  getIntakeV6NestingPreview,
  getIntakeV6PricingInputPreview,
  getIntakeV6PricedQuoteDryRun,
  getIntakeV6ProductSystemBinding,
  getIntakeV6QuoteHandoffPreview,
} from "@/lib/intakeV6/intakeV6Api";

const mockedBinding = vi.mocked(getIntakeV6ProductSystemBinding);
const mockedBreakdown = vi.mocked(getIntakeV6MaterialBreakdown);
const mockedNesting = vi.mocked(getIntakeV6NestingPreview);
const mockedPricing = vi.mocked(getIntakeV6PricingInputPreview);
const mockedPricedDryRun = vi.mocked(getIntakeV6PricedQuoteDryRun);
const mockedHandoff = vi.mocked(getIntakeV6QuoteHandoffPreview);

const handoffReady = {
  workspace_id: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
  workspace_readiness_status: "ready_for_quote_preview",
  handoff_allowed: true,
  can_create_internal_draft_quote: true,
  status_label: "READY_FOR_INTERNAL_DRAFT_REVIEW" as const,
  blockers: [],
  fatal_blockers: [],
  review_warnings: [],
  requires_operator_confirmation: true,
  operator_confirmation_complete: true,
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
          finish_setup: { confirmed: true },
          quote_geometry: { letter_count: 10, width_mm: 1000, height_mm: 500 },
          svg_source: { file_hash: "a".repeat(64) },
        },
      },
      layerChips: [{ id: "1" }, { id: "2" }],
      svg: { fileName: "pbl-layere.svg" },
      localFileHash: "a".repeat(64),
      workspaceId: "0f300dcf-0b77-4fc1-affd-6e2a20329804",
      phase: "ready",
      currentStep: "review",
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
    material_rows: [],
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
      sheet_layouts: 0,
      roll_layouts: 0,
      active_sheet_layouts: 0,
      active_roll_layouts: 0,
      alternative_layouts: 0,
      nestable_parts: 0,
      holes_excluded: 0,
      artwork_parts: 0,
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
    production_counts: { letter_count: 10, cut_contour_count: 10, inner_hole_count: 0 },
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
    commercial_line_items: [],
    pricing_hash: "hash-123",
  });
  mockedHandoff.mockResolvedValue(handoffReady);
});

function renderSummary(hook: IntakeV6WorkspaceHook = buildHook(), withFooter = false) {
  return render(
    <MemoryRouter>
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6FinalConfigurationSummary hook={hook} />
        {withFooter ? (
          <IntakeV6OperatorWorkspaceFooter
            currentStep="confirm"
            stepIndex={2}
            stepOrderLength={3}
            footerBlocker={null}
            nextDisabled
            nextLabel=""
            nextButtonClassName=""
            onBack={() => {}}
            onNext={() => {}}
            persisting={false}
            workspaceState={hook.state}
          />
        ) : null}
      </IntakeV6WorkspaceHeaderStatusProvider>
    </MemoryRouter>,
  );
}

describe("IntakeV6FinalConfigurationSummary", () => {
  it("is collapsed by default in embedded variant", async () => {
    renderSummary();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-final-configuration-summary")).toBeInTheDocument();
    });

    expect(screen.getByTestId("intake-v6-final-configuration-summary")).toHaveAttribute(
      "data-expanded",
      "false",
    );
    expect(screen.queryByTestId("intake-v6-confirm-tile-work")).not.toBeInTheDocument();
  });

  it("expanded content shows dashboard and keeps technical details collapsed", async () => {
    renderSummary();

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-final-configuration-summary-toggle")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("intake-v6-final-configuration-summary-toggle"));

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-confirm-dashboard")).toBeInTheDocument();
      expect(screen.getByTestId("intake-v6-confirm-tile-work")).toBeInTheDocument();
    });

    expect(screen.getByTestId("intake-v6-final-configuration-technical-details")).toHaveAttribute(
      "data-expanded",
      "false",
    );
  });

  it("registers confirm footer for workspace handoff", async () => {
    renderSummary(buildHook(), true);

    await waitFor(() => {
      expect(screen.getByTestId("intake-v6-create-internal-draft")).toBeInTheDocument();
    });

    expect(screen.getByTestId("intake-v6-create-internal-draft")).toHaveTextContent("Continuă către ofertă");
  });
});
