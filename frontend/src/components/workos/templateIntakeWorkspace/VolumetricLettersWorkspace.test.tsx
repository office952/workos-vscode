import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import VolumetricLettersWorkspace from "./VolumetricLettersWorkspace";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import type { TemplateWorkspaceBaseProps } from "./types";

vi.mock("@/components/workos/FlowBreadcrumb", () => ({
  default: () => <div data-testid="breadcrumb" />,
  intakeDetailBreadcrumb: () => [],
}));

vi.mock("@/components/workos/Product001IntakeSpecEditor", () => ({
  default: () => <div data-testid="product-form">Editor</div>,
}));

vi.mock("@/components/workos/VolumetricLettersQuoteFlow", () => ({
  default: () => <div data-testid="volumetric-quote-embedded">Quote</div>,
}));

const baseProps: TemplateWorkspaceBaseProps = {
  request: {
    id: "WI-SMOKE-P001",
    client: "TEST Product001 smoke",
    contactPerson: "Smoke Validator",
    channel: "email",
    productFamily: "litere_volumetrice",
    description: "TEST",
    dimensions: "",
    quantity: 1,
    status: "ready_for_quote",
    assignedTo: "Smoke",
    createdAt: "",
    updatedAt: "",
    notes: "",
    priority: "low",
    deliveryType: "courier",
    identity: { type: "temp", tempRef: "T1" },
    confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
  },
  source: "db",
  error: null,
  persistError: null,
  selectedDeliveryType: "courier",
  assignedTo: "Smoke",
  setAssignedTo: vi.fn(),
  confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
  productSpecInitial: null,
  actionSummary: {
    templateLabel: "OK",
    templateOk: true,
    productSpecLabel: "OK",
    productSpecOk: true,
    terrainLabel: "N/A",
    terrainOk: null,
    intakeStatusLabel: "Gata",
    intakeReady: true,
    primaryAction: "open_preliminary_quote",
    primaryActionLabel: "Simulare",
    primaryDisabled: false,
    showPreliminaryQuote: true,
    readinessMissing: [],
    readinessStage: "stage2_simulation",
    readinessStageLabel: "Gata pentru simulare",
    canSimulate: true,
    stagedMissingGroups: [],
  },
  readiness: { canMarkReady: true, missing: [] },
  statusConflict: false,
  requiresInstallAudit: false,
  markReadyLoading: false,
  markReadyMessage: null,
  confirmingTemplate: false,
  hasFiscalIdentity: false,
  installTerrainSection: null,
  intakeDbId: 1,
  siteAuditJson: null,
  onDeliveryTypeChange: vi.fn(),
  onAssignedBlur: vi.fn(),
  onSaveProductSpec: vi.fn(),
  onMarkReadyForQuote: vi.fn(),
  onConfirmTemplate: vi.fn(),
};

function renderWorkspace() {
  return render(
    <MemoryRouter>
      <VolumetricLettersWorkspace {...baseProps} />
    </MemoryRouter>
  );
}

describe("VolumetricLettersWorkspace composition", () => {
  it("renders two-column layout with main and side regions", () => {
    renderWorkspace();
    expect(screen.getByTestId("template-workspace-layout")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-main-column")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-side-panel")).toBeInTheDocument();
  });

  it("places ProductSpecEditorSlot in main column", () => {
    renderWorkspace();
    const main = screen.getByTestId("workspace-main-column");
    const slot = screen.getByTestId("product-spec-editor-slot");
    expect(main).toContainElement(slot);
    expect(screen.getByTestId("product-form")).toBeInTheDocument();
    expect(screen.getByTestId("terrain-na")).toBeInTheDocument();
  });

  it("places context, status, and readiness in side panel", () => {
    renderWorkspace();
    const side = screen.getByTestId("workspace-side-panel");
    expect(side).toContainElement(screen.getByTestId("request-context-panel"));
    expect(side).toContainElement(screen.getByTestId("template-status-panel"));
    expect(side).toContainElement(screen.getByTestId("readiness-gate-panel"));
    expect(side).toContainElement(screen.getByTestId("sticky-workspace-actions"));
  });

  it("exposes info-hint triggers instead of long inline helper blocks in workspace", () => {
    renderWorkspace();
    expect(screen.getAllByTestId("info-hint-trigger").length).toBeGreaterThan(0);
  });

  it("keeps primary actions visible", () => {
    renderWorkspace();
    expect(screen.getByTestId("action-mark-ready")).toBeInTheDocument();
    expect(screen.getByTestId("action-open-preliminary-quote")).toBeInTheDocument();
  });

  it("embeds quote flow in main column on quote tab", () => {
    renderWorkspace();
    fireEvent.click(screen.getByTestId("volumetric-tab-quote"));
    const main = screen.getByTestId("workspace-main-column");
    const panel = screen.getByTestId("volumetric-quote-panel");
    expect(main).toContainElement(panel);
    expect(screen.getByTestId("volumetric-quote-embedded")).toBeInTheDocument();
  });
});
