import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IntakeDetail from "./IntakeDetail";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import { TERRAIN_NA_COMPACT_LABEL } from "@/lib/intakeDeliverySemantics";
import { EMPTY_SITE_AUDIT } from "@/lib/intakeSiteAudit";
import VolumetricLettersWorkspace from "@/components/workos/templateIntakeWorkspace/VolumetricLettersWorkspace";
import type { TemplateWorkspaceBaseProps } from "@/components/workos/templateIntakeWorkspace/types";

const mockNavigate = vi.fn();
const mockUseBackendData = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom"
  );
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("@/api/intakeAssist", () => ({
  getMaterialSheetAssist: vi.fn().mockResolvedValue({
    status: "ok",
    data: { items: [], assist_available: false, blockers: [] },
  }),
  listProductTemplateAssist: vi.fn().mockResolvedValue({
    status: "ok",
    data: { items: [] },
  }),
  lookupFiscalProvider: vi.fn(),
  suggestProductTemplates: vi.fn().mockResolvedValue({
    status: "ok",
    data: { suggestions: [] },
  }),
}));

vi.mock("@/api/productFamilies", () => ({
  productFamiliesApi: { list: vi.fn().mockResolvedValue([]) },
}));

vi.mock("@/lib/api", () => ({
  intakesApi: { list: vi.fn().mockResolvedValue([]), update: vi.fn() },
}));

vi.mock("@/components/workos/Product001IntakeSpecEditor", () => ({
  default: () => <div data-testid="product-form">Product spec editor</div>,
}));

vi.mock("@/components/workos/VolumetricLettersQuoteFlow", () => ({
  default: () => <div data-testid="volumetric-quote-embedded">Quote</div>,
}));

vi.mock("@/components/workos/FlowBreadcrumb", () => ({
  default: () => <div data-testid="breadcrumb" />,
  intakeDetailBreadcrumb: () => [],
}));

const genericInstall = {
  id: "IR-GENERIC-INSTALL",
  client: "Generic",
  contactPerson: "—",
  channel: "email" as const,
  productFamily: "",
  description: "Unresolved",
  dimensions: "—",
  quantity: 1,
  status: "new" as const,
  assignedTo: "—",
  createdAt: "2026-06-07T00:00:00Z",
  updatedAt: "2026-06-07T00:00:00Z",
  notes: "",
  priority: "normal" as const,
  deliveryType: "delivery_install" as const,
  identity: { type: "temp" as const, tempRef: "TEMP" },
  productSpec: null,
  confirmedTemplateCode: null,
  siteAudit: null,
};

const legacySelected = {
  id: "IR-LEGACY-COURIER",
  client: "Legacy",
  contactPerson: "—",
  channel: "email" as const,
  productFamily: "Casete Luminoase",
  description: "Legacy family",
  dimensions: "100x100",
  quantity: 1,
  status: "new" as const,
  assignedTo: "Op",
  createdAt: "2026-06-07T00:00:00Z",
  updatedAt: "2026-06-07T00:00:00Z",
  notes: "",
  priority: "normal" as const,
  deliveryType: "courier" as const,
  identity: { type: "temp" as const, tempRef: "TEMP" },
  productSpec: null,
  confirmedTemplateCode: null,
  siteAudit: null,
};

function renderIntake(code: string) {
  render(
    <MemoryRouter initialEntries={[`/intake/${code}`]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeDetail delivery sync", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      intakes: [genericInstall, legacySelected],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
  });

  it("generic unresolved with install shows neutral note but no terrain audit", () => {
    renderIntake("IR-GENERIC-INSTALL");
    expect(screen.getByTestId("delivery-stage-note")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-audit-teren-section")).not.toBeInTheDocument();
  });

  it("selected non-install legacy intake hides terrain audit", () => {
    renderIntake("IR-LEGACY-COURIER");
    expect(screen.queryByTestId("intake-audit-teren-section")).not.toBeInTheDocument();
  });
});

describe("VolumetricLettersWorkspace delivery sync", () => {
  const baseProps: TemplateWorkspaceBaseProps = {
    request: {
      id: "WI-VOL-COURIER",
      client: "Vol",
      contactPerson: "—",
      channel: "email",
      productFamily: "litere_volumetrice",
      description: "Test",
      dimensions: "",
      quantity: 1,
      status: "new",
      assignedTo: "Op",
      createdAt: "",
      updatedAt: "",
      notes: "",
      priority: "normal",
      deliveryType: "courier",
      identity: { type: "temp", tempRef: "T1" },
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
    },
    source: "db",
    error: null,
    persistError: null,
    selectedDeliveryType: "courier",
    assignedTo: "Op",
    setAssignedTo: vi.fn(),
    confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
    productSpecInitial: null,
    actionSummary: {
      templateLabel: TPL_VOLUMETRIC_LETTERS,
      templateOk: true,
      productSpecLabel: "Incompletă",
      productSpecOk: false,
      terrainLabel: "N/A (fără montaj)",
      terrainOk: null,
      intakeStatusLabel: "Neîncă gata",
      intakeReady: false,
      primaryAction: "complete_spec",
      primaryActionLabel: "Completează specificația",
      primaryDisabled: false,
      showPreliminaryQuote: true,
      readinessMissing: ["Audit teren — incomplet", "Dimensiuni din specificație — width/height/depth lipsă"],
      readinessStage: "stage1_spec",
      readinessStageLabel: "Specificație începută",
      canSimulate: false,
      stagedMissingGroups: [
        {
          stage: "stage3_commercial_quote",
          label: "Gata pentru ofertă comercială",
          description: "",
          missing: ["Dimensiuni din specificație — width/height/depth lipsă"],
          ready: false,
        },
      ],
    },
    readiness: {
      canMarkReady: false,
      missing: ["Audit teren — incomplet", "Dimensiuni din specificație — width/height/depth lipsă"],
    },
    statusConflict: false,
    requiresInstallAudit: false,
    markReadyLoading: false,
    markReadyMessage: null,
    confirmingTemplate: false,
    hasFiscalIdentity: false,
    installTerrainSection: <div data-testid="terrain-audit-full">Terrain</div>,
    intakeDbId: 1,
    siteAuditJson: {
      ...EMPTY_SITE_AUDIT,
      checks: {
        ...EMPTY_SITE_AUDIT.checks,
        address_confirmed: true,
        photos_verified: false,
        power_confirmed: false,
        access_confirmed: false,
      },
    },
    onDeliveryTypeChange: vi.fn(),
    onAssignedBlur: vi.fn(),
    onSaveProductSpec: vi.fn(),
    onMarkReadyForQuote: vi.fn(),
    onConfirmTemplate: vi.fn(),
  };

  it("volumetric courier hides terrain audit and terrain blockers", () => {
    render(
      <MemoryRouter>
        <VolumetricLettersWorkspace {...baseProps} />
      </MemoryRouter>
    );
    expect(screen.getByText(TERRAIN_NA_COMPACT_LABEL)).toBeInTheDocument();
    expect(screen.queryByTestId("terrain-audit-full")).not.toBeInTheDocument();
    expect(screen.queryByText("Audit teren — incomplet")).not.toBeInTheDocument();
    expect(screen.getAllByText(/Dimensiuni din specificație/i).length).toBeGreaterThan(0);
  });

  it("volumetric install shows terrain audit section", () => {
    render(
      <MemoryRouter>
        <VolumetricLettersWorkspace
          {...baseProps}
          selectedDeliveryType="delivery_install"
          requiresInstallAudit
          actionSummary={{
            ...baseProps.actionSummary,
            terrainLabel: "0/3",
            terrainOk: false,
            readinessMissing: ["Audit teren — incomplet"],
            stagedMissingGroups: [
              {
                stage: "stage3_commercial_quote",
                label: "Gata pentru ofertă comercială",
                description: "",
                missing: ["Audit teren — incomplet"],
                ready: false,
              },
            ],
          }}
          readiness={{ canMarkReady: false, missing: ["Audit teren — incomplet"] }}
        />
      </MemoryRouter>
    );
    expect(screen.getByTestId("terrain-audit-full")).toBeInTheDocument();
    expect(screen.getByText("Audit teren — incomplet")).toBeInTheDocument();
  });
});
