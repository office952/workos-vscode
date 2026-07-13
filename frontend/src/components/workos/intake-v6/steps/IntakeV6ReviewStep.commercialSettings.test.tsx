import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import IntakeV6ReviewStep from "./IntakeV6ReviewStep";

vi.mock("@/lib/intakeV6/intakeV6Api", () => ({
  getIntakeV6AiInformationalAssistCandidate: vi.fn(),
  getIntakeV6LogicalListReadModel: vi.fn(),
  getIntakeV6MaterialBreakdown: vi.fn(),
  getIntakeV6OrderBoundTaskReadiness: vi.fn(),
  getIntakeV6PricedQuoteDryRun: vi.fn(),
  getIntakeV6PricingInputPreview: vi.fn(),
  getIntakeV6ProductionHandoffPreview: vi.fn(),
  getIntakeV6ProductionTaskDryRun: vi.fn(),
  getIntakeV6ProductSystemBinding: vi.fn(),
  getIntakeV6ProductTruthPromotionPlanner: vi.fn(),
  getIntakeV6QuoteHandoffPreview: vi.fn(),
  getIntakeV6RuntimeCaptureReadModel: vi.fn(),
  getIntakeV6TaskGenerationDryRun: vi.fn(),
  getIntakeV6TaskPreview: vi.fn(),
  getIntakeV6Workspace: vi.fn(),
}));

vi.mock("@/lib/intakeV6/preOrderTechnicalPreviewApi", () => ({
  getPreOrderTechnicalPreview: vi.fn(),
}));

vi.mock("@/api/productDefinitionPreview", () => ({
  getProductDefinitionPreview: vi.fn(),
  ProductDefinitionPreviewNotFoundError: class ProductDefinitionPreviewNotFoundError extends Error {},
}));

vi.mock("@/hooks/useCompanyCommercialSettings", () => ({
  useCompanyCommercialSettings: () => ({
    vatPct: 21,
    eurToRonRate: 5,
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

const templateContractMock = {
  defaultFaceFinish: "oracal_651",
  faceFinishOptions: [
    { value: "oracal_651", label: "Oracal 651" },
    { value: "print_laminate", label: "Print + laminate" },
  ],
  allowedReturnDepthMm: [40, 60, 80],
  allowedLightingSystems: ["led_modules"],
  allowedLightColors: ["neutral"],
  allowedLedModulePowerW: [0.75],
  allowedEmblemLightingModes: ["area_lit"],
  allowedMountingTemplateMaterials: [{ value: "forex", label: "Forex" }],
  allowedMountingSystems: [{ value: "direct_wall", label: "Direct wall" }],
  allowedMountingBarProfiles: ["30x30x1.5"],
  allowedPsuWatts: [100, 160],
  allowedVinylRollWidths: [{ value: 1000, label: "1000 mm" }],
  intended_form_authority: "product_system_dossier",
  current_runtime_authority: "intake_v6_review",
  alignment_status: "aligned",
  warnings: [],
  variant_fields: [],
};

vi.mock("@/lib/intakeV6/useTemplateFormContract", () => ({
  useTemplateFormContract: () => ({
    contract: templateContractMock,
    loading: false,
    error: null,
    ...templateContractMock,
  }),
}));

vi.mock("@/lib/intakeV6/useModularFormContract", () => ({
  useModularFormContract: () => ({ contract: null, loading: false, error: null, templateCode: null }),
}));

vi.mock("@/lib/intakeV6/useModularFormAwareness", () => ({
  useModularFormAwareness: () => ({ warnings: [], requiredAttention: [], summary: null }),
}));

vi.mock("@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft", () => ({
  useIntakeV6FaceBackPrepCostDraft: () => ({ draft: null, loading: false, error: null }),
}));

vi.mock("@/lib/intakeV6/intakeV6AnalysisIdentity", () => ({
  getAnalysisIdentityKey: () => "analysis-key",
  isAnalysisReadyForReview: () => true,
}));

vi.mock("@/components/ui/sonner", () => ({
  toast: { error: vi.fn() },
}));

vi.mock("../IntakeV6ArtworkFinishSection", () => ({
  default: () => <div data-testid="mock-intake-v6-artwork-finish-section" />,
}));
vi.mock("../IntakeV6ArtworkComplexityCard", () => ({ default: () => null }));
vi.mock("../IntakeV6AiSemanticAssistPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6ReviewBackingSelect", () => ({ default: () => null }));
vi.mock("../IntakeV6ReviewLightingSection", () => ({ default: () => null }));
vi.mock("../IntakeV6ReviewSaveFooter", () => ({ default: () => null }));
vi.mock("../IntakeV6FaceBackPrepCostDraftPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6GeometryPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6ReviewLetterGroupsSection", () => ({ default: () => null }));
vi.mock("../IntakeV6MaterialBreakdownPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6ProductionHandoffPreviewPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6TaskGenerationDryRunPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6OrderBoundTaskReadinessPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6QuoteCommercialSpinePanel", () => ({ default: () => null }));
vi.mock("../FormSystemBackboneAwarenessPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6ReturnCantBlockedStateAwarenessPanel", () => ({
  default: () => <div data-testid="mock-return-cant-blocked-awareness" />,
}));
vi.mock("../PreOrderTechnicalPreviewPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6ReturnCantFields", () => ({ default: () => null }));
vi.mock("../IntakeV6ProductionTaskDryRunPanel", () => ({ default: () => null }));
vi.mock("../IntakeV6ReviewTabNav", () => ({ default: () => null }));
vi.mock("../IntakeV6LiveCalculationSummary", () => ({ default: () => null }));
vi.mock("../IntakeV6OperatorWorkSummaryTechnicalDetails", () => ({ default: () => null }));
vi.mock("../IntakeV6ArtworkOnlyDecisionPanel", () => ({
  default: () => <div data-testid="mock-intake-v6-artwork-only-decision-panel" />,
}));
vi.mock("../atoms/IntakeV6ReviewSectionShell", () => ({
  default: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("../atoms/IntakeV6TechnicalDetailsAccordion", () => ({
  default: () => null,
}));
vi.mock("../IntakeV6WorkspaceHeaderStatusContext", () => ({
  useIntakeV6WorkspaceHeaderStatus: () => ({ setOverlay: vi.fn(), setHandlers: vi.fn() }),
}));

import {
  getIntakeV6AiInformationalAssistCandidate,
  getIntakeV6LogicalListReadModel,
  getIntakeV6MaterialBreakdown,
  getIntakeV6OrderBoundTaskReadiness,
  getIntakeV6PricedQuoteDryRun,
  getIntakeV6PricingInputPreview,
  getIntakeV6ProductionHandoffPreview,
  getIntakeV6ProductionTaskDryRun,
  getIntakeV6ProductSystemBinding,
  getIntakeV6ProductTruthPromotionPlanner,
  getIntakeV6QuoteHandoffPreview,
  getIntakeV6RuntimeCaptureReadModel,
  getIntakeV6TaskGenerationDryRun,
  getIntakeV6TaskPreview,
  getIntakeV6Workspace,
} from "@/lib/intakeV6/intakeV6Api";
import { getProductDefinitionPreview } from "@/api/productDefinitionPreview";
import { toast } from "@/components/ui/sonner";

const mockedAiAssist = vi.mocked(getIntakeV6AiInformationalAssistCandidate);
const mockedLogicalList = vi.mocked(getIntakeV6LogicalListReadModel);
const mockedBreakdown = vi.mocked(getIntakeV6MaterialBreakdown);
const mockedOrderBound = vi.mocked(getIntakeV6OrderBoundTaskReadiness);
const mockedPricedDryRun = vi.mocked(getIntakeV6PricedQuoteDryRun);
const mockedPricingPreview = vi.mocked(getIntakeV6PricingInputPreview);
const mockedProductionHandoff = vi.mocked(getIntakeV6ProductionHandoffPreview);
const mockedProductionDryRun = vi.mocked(getIntakeV6ProductionTaskDryRun);
const mockedBinding = vi.mocked(getIntakeV6ProductSystemBinding);
const mockedPromotionPlanner = vi.mocked(getIntakeV6ProductTruthPromotionPlanner);
const mockedQuoteHandoff = vi.mocked(getIntakeV6QuoteHandoffPreview);
const mockedRuntimeCapture = vi.mocked(getIntakeV6RuntimeCaptureReadModel);
const mockedTaskGeneration = vi.mocked(getIntakeV6TaskGenerationDryRun);
const mockedTaskPreview = vi.mocked(getIntakeV6TaskPreview);
const mockedWorkspace = vi.mocked(getIntakeV6Workspace);
const mockedProductDefinitionPreview = vi.mocked(getProductDefinitionPreview);

function buildWorkspacePayload(overrides?: Record<string, unknown>) {
  return {
    finish_setup: {
      face_finish_type: "oracal_651",
      face_vinyl_roll_width_mm: 1000,
      return_finish_type: "white_aluminum",
      volum_aluminum_module_template_code: null,
      return_depth_mm: 60,
      illuminated: true,
      lighting_system_type: "led_modules",
      light_color: "neutral",
      led_module_power_w: 0.75,
      led_strip_power_w_per_ml: 5,
      psu_configuration: [160],
      selected_psu_watts: 160,
      backing_mode: "forex_10_no_bevel",
      back_bevel_enabled: false,
      mounting_template_enabled: true,
      mounting_template_material_type: "forex",
      mounting_system: "direct_wall",
      mounting_bar_profile: "30x30x1.5",
      emblem_lighting_mode: "area_lit",
      confirmed: false,
      letter_group_finishes: [],
      artwork_finishes: [],
      artwork_complexity_decisions: [],
      commercial_inputs: {
        markup_percent: 35,
        discount_percent: 0,
        vat_percent: 21,
        manual_adjustment_ron: 0,
      },
      ...overrides,
    },
    quote_geometry: {
      letter_perimeter_m: 12,
      total_letter_perimeter_ml: 12,
      face_area_m2: 1.2,
      letter_count: 10,
      real_letters_count: 10,
      inner_holes_count: 0,
      return_material_perimeter_ml: 12,
      face_cutting_perimeter_ml: 12,
      artwork_piece_count: 0,
      artwork_boxes: [],
      letter_return_perimeter_ml: 12,
      artwork_return_perimeter_ml: null,
      led_perimeter_ml: 12,
      volumetric_piece_count: 10,
    },
    product_binding: { template_code: "TPL-VOLUMETRIC-LETTERS" },
    svg_source: { file_hash: "a".repeat(64) },
  };
}

function buildHook(
  workspace: Record<string, unknown>,
  saveFinishSetup: IntakeV6WorkspaceHook["saveFinishSetup"],
): IntakeV6WorkspaceHook {
  return {
    state: {
      workspace,
      workspaceId: "3c494f9f-4507-497a-912f-4f45fe709642",
      phase: "ready",
      currentStep: "review",
      analyzerStatus: "ready",
      analyzerReport: null,
      analyzerError: null,
      layerRoleConfirmation: { confirmationStatus: "complete", layers: [] },
      layerChips: [],
      svg: { fileName: "gradi-curat.svg", fileSizeBytes: 10, previewSource: null },
      svgSource: "<svg />",
      localFileHash: "a".repeat(64),
      unsavedAnalysis: false,
      analysisRunId: 1,
      error: null,
      loadErrorCode: null,
    },
    setStep: vi.fn(),
    trySetStep: vi.fn(() => true),
    canAccessStep: vi.fn(() => true),
    importSvgFile: vi.fn(),
    updateLayerRole: vi.fn(),
    confirmAllLayerRoles: vi.fn(),
    continueFromAnalyzer: vi.fn(),
    saveFinishSetup,
    canImportSvg: true,
    canContinueFromAnalyzer: true,
    canContinueFromReview: true,
    isReadyForQuotePreview: true,
    firstBlocker: null,
  } as unknown as IntakeV6WorkspaceHook;
}

beforeEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();

  mockedBinding.mockResolvedValue({
    workspace_id: "ws",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    template_label: "Litere volumetrice",
    template_active: true,
    operation_count: 1,
    component_count: 1,
    module_links: [],
    blockers: [],
  } as never);
  mockedPromotionPlanner.mockResolvedValue({
    workspace_id: "ws",
    blockers: [],
    blocked_entries: [],
    ready_entries: [],
    warnings: [],
  } as never);
  mockedRuntimeCapture.mockResolvedValue({
    read_only: true,
    workspace_id: "ws",
    fields: [],
    blockers: [],
    downstream_write_intent: {},
    notes: [],
  } as never);
  mockedBreakdown.mockResolvedValue({
    workspace_id: "ws",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    breakdown_scope: "review",
    nesting_rows: [],
    material_rows: [],
    consumable_rows: [],
    operation_rows: [],
    edge_cant_operation_rows: [],
    totals: {
      material_cost_total: 1000,
      estimated_cost_total: 1000,
      currency: "EUR",
      contains_estimates: false,
      contains_missing_prices: false,
    },
    warnings: [],
  } as never);
  mockedPricingPreview.mockResolvedValue({
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
  } as never);
  mockedPricedDryRun.mockResolvedValue({
    pricing_status: "V6_PRICED_DRY_RUN_READY",
    workspace_id: "ws",
    pricing_source: "intake_v6_backend_priced_dry_run",
    commercial_totals: {
      subtotal_net: 6750,
      vat_rate: 21,
      vat_amount: 1417.5,
      total_gross: 8167.5,
      currency: "RON",
    },
    commercial_proposal_trace: {
      cost_plus_inputs: {
        internal_cost_total: 1000,
        internal_cost_currency: "EUR",
        eur_to_ron_rate: 5,
        commercial_inputs: {
          markup_percent: 35,
          discount_percent: 0,
          vat_percent: 21,
          manual_adjustment_ron: 0,
        },
      },
    },
  } as never);
  mockedTaskPreview.mockResolvedValue({ items: [] } as never);
  mockedLogicalList.mockResolvedValue(null as never);
  mockedAiAssist.mockResolvedValue(null as never);
  mockedProductionHandoff.mockResolvedValue(null as never);
  mockedProductionDryRun.mockResolvedValue(null as never);
  mockedTaskGeneration.mockResolvedValue(null as never);
  mockedOrderBound.mockResolvedValue(null as never);
  mockedQuoteHandoff.mockResolvedValue(null as never);
  mockedWorkspace.mockResolvedValue({ payload: buildWorkspacePayload() } as never);
  mockedProductDefinitionPreview.mockResolvedValue({
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    linked_template_runtime_segments: {
      root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      segments: [],
    },
    selected_modules: [],
    optional_modules: [],
    inactive_modules: [],
    components: [],
    material_roles: [],
    operation_roles: [],
    canonical_values: {},
    geometry_inputs: {},
    validation: { readiness_status: "partial", missing_required_fields: [], invalid_combinations: [], unresolved_warnings: [] },
    provenance: [],
    warnings: [],
    notes: [],
    preview_version: "1.0.0",
    source_context: { template_code: "TPL-VOLUMETRIC-LETTERS_v2", workspace_id: "ws", source_payload_type: "workspace_payload" },
  } as never);
});

afterEach(() => cleanup());

function renderReviewStepHarness() {
  const saveBodies: Array<Record<string, unknown>> = [];
  const saveFinishSetup = vi.fn();
  const initialWorkspace = {
    id: "3c494f9f-4507-497a-912f-4f45fe709642",
    workspace_code: "IV6-0EFC6C31",
    title: "gradi-curat",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    readiness_status: "ready_for_quote_preview",
    payload: buildWorkspacePayload(),
  };

  function Harness() {
    const [workspace, setWorkspace] = useState(initialWorkspace);
    const hook = buildHook(
      workspace as unknown as Record<string, unknown>,
      (async (body) => {
        saveBodies.push(body as unknown as Record<string, unknown>);
        const nextWorkspace = {
          ...workspace,
          payload: {
            ...(workspace.payload as Record<string, unknown>),
            finish_setup: body,
          },
        };
        setWorkspace(nextWorkspace);
        saveFinishSetup(body);
        return nextWorkspace;
      }) as IntakeV6WorkspaceHook["saveFinishSetup"],
    );
    return <IntakeV6ReviewStep hook={hook} />;
  }

  render(
    <MemoryRouter>
      <Harness />
    </MemoryRouter>,
  );

  return { saveBodies, saveFinishSetup };
}

describe("IntakeV6ReviewStep commercial settings regression", () => {
  it("keeps the artwork decision panel and artwork editor visible together for artwork-only review", async () => {
    const analyzerReport = {
      document: {
        widthMm: 1500.2,
        heightMm: 1500.2,
      },
      layers: [
        {
          id: "logo-dreapta",
          name: "logo dreapta",
          elementCount: 1,
          pathElementCount: 0,
          closedSubPathCount: 0,
          subPathCount: 0,
          layerKind: "regular",
          autoRole: "printed_artwork",
          paintEvidence: { paintKind: "policromie", hasGradient: false, hasPattern: false, hasImage: false },
          colors: [],
        },
      ],
    };
    const workspace = {
      id: "logo-ws",
      workspace_code: "IV6-LOGO",
      title: "logo",
      template_code: "TPL-VOLUMETRIC-LETTERS",
      readiness_status: "finish_setup_incomplete",
      payload: buildWorkspacePayload({
        artwork_finishes: [
          {
            layer_key: "logo-dreapta",
            layer_name: "logo dreapta",
            execution_type: "print_laminate",
            color_mode: "polychrome",
            return_finish_type: "white_aluminum",
            return_depth_mm: 60,
            confirmed: false,
          },
        ],
      }),
    };
    const hook = buildHook(workspace as unknown as Record<string, unknown>, vi.fn() as never);
    hook.state.analyzerReport = analyzerReport as never;
    hook.state.layerRoleConfirmation = {
      confirmationStatus: "complete",
      layers: [
        {
          layerKey: "logo-dreapta",
          layerName: "logo dreapta",
          autoRole: "printed_artwork",
          confirmedRole: "printed_artwork",
          confirmationState: "confirmed",
        },
      ],
    } as never;

    render(
      <MemoryRouter>
        <IntakeV6ReviewStep hook={hook} />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId("mock-intake-v6-artwork-only-decision-panel")).toBeInTheDocument());
    expect(screen.getByTestId("mock-intake-v6-artwork-finish-section")).toBeInTheDocument();
  });

  it("completes autosave without ReferenceError and refreshes preview once", async () => {
    const { saveFinishSetup } = renderReviewStepHarness();

    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-markup")).toHaveValue(35));

    fireEvent.change(screen.getByTestId("intake-v6-offer-markup"), { target: { value: "42" } });
    fireEvent.blur(screen.getByTestId("intake-v6-offer-markup"));

    await waitFor(() => expect(saveFinishSetup).toHaveBeenCalledTimes(1), { timeout: 3000 });

    expect(toast.error).not.toHaveBeenCalled();
    expect(screen.queryByText(/setPayload is not defined/i)).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-markup")).toHaveValue(42));
    await waitFor(() => expect(mockedBreakdown).toHaveBeenCalled(), { timeout: 3000 });
    expect(mockedBreakdown).toHaveBeenCalledTimes(1);
  });

  it("persists markup 35 -> 50 and does not reset it after blur/save", async () => {
    const { saveBodies, saveFinishSetup } = renderReviewStepHarness();

    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-markup")).toHaveValue(35));

    fireEvent.change(screen.getByTestId("intake-v6-offer-markup"), { target: { value: "50" } });
    fireEvent.blur(screen.getByTestId("intake-v6-offer-markup"));
    expect(screen.getByTestId("intake-v6-offer-markup")).toHaveValue(50);

    await waitFor(() => expect(saveFinishSetup).toHaveBeenCalledTimes(1), { timeout: 2500 });
    expect(saveBodies[0]?.commercial_inputs).toMatchObject({
      markup_percent: 50,
      discount_percent: 0,
      vat_percent: 21,
      manual_adjustment_ron: 0,
    });
    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-markup")).toHaveValue(50));
  });

  it("hydrates persisted markup instead of keeping the stale default 35", async () => {
    const workspace = {
      id: "ws-persisted",
      workspace_code: "IV6-PERSISTED",
      title: "persisted",
      template_code: "TPL-VOLUMETRIC-LETTERS",
      readiness_status: "ready_for_quote_preview",
      payload: buildWorkspacePayload({
        commercial_inputs: {
          markup_percent: 15,
          discount_percent: 10,
          vat_percent: 21,
          manual_adjustment_ron: 100,
        },
      }),
    };
    const hook = buildHook(workspace as unknown as Record<string, unknown>, vi.fn() as never);

    render(
      <MemoryRouter>
        <IntakeV6ReviewStep hook={hook} />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-markup")).toHaveValue(15));
    expect(screen.getByTestId("intake-v6-offer-discount")).toHaveValue(10);
    expect(screen.getByTestId("intake-v6-offer-manual-adjustment")).toHaveValue(100);
  });

  it("persists discount 0 -> 10 in the commercial payload", async () => {
    const { saveBodies, saveFinishSetup } = renderReviewStepHarness();

    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-discount")).toHaveValue(0));
    fireEvent.change(screen.getByTestId("intake-v6-offer-discount"), { target: { value: "10" } });
    fireEvent.blur(screen.getByTestId("intake-v6-offer-discount"));

    await waitFor(() => expect(saveFinishSetup).toHaveBeenCalledTimes(1), { timeout: 2500 });
    expect(saveBodies[0]?.commercial_inputs).toMatchObject({
      markup_percent: 35,
      discount_percent: 10,
      vat_percent: 21,
      manual_adjustment_ron: 0,
    });
  });

  it("persists manual adjustment 0 -> 100 and keeps VAT read-only", async () => {
    const { saveBodies, saveFinishSetup } = renderReviewStepHarness();

    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-manual-adjustment")).toHaveValue(0));
    expect(screen.getByTestId("intake-v6-offer-vat")).toHaveValue(21);
    expect(screen.getByTestId("intake-v6-offer-vat")).toBeDisabled();
    expect(screen.getByTestId("intake-v6-offer-vat")).toHaveAttribute("readonly");

    fireEvent.change(screen.getByTestId("intake-v6-offer-manual-adjustment"), { target: { value: "100" } });
    fireEvent.blur(screen.getByTestId("intake-v6-offer-manual-adjustment"));

    await waitFor(() => expect(saveFinishSetup).toHaveBeenCalledTimes(1), { timeout: 2500 });
    expect(saveBodies[0]?.commercial_inputs).toMatchObject({
      markup_percent: 35,
      discount_percent: 0,
      vat_percent: 21,
      manual_adjustment_ron: 100,
    });
    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-manual-adjustment")).toHaveValue(100));
  });

  it("mounts the return/cant blocked awareness panel in review without ready-state claims", async () => {
    renderReviewStepHarness();

    await waitFor(() => {
      expect(screen.getByTestId("mock-return-cant-blocked-awareness")).toBeInTheDocument();
    });
    expect(screen.queryByText(/preview ready/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/calculation ready/i)).not.toBeInTheDocument();
  });
});