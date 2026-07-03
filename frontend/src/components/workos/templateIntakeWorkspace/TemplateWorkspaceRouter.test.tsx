import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import TemplateWorkspaceRouter from "./TemplateWorkspaceRouter";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import type { TemplateWorkspaceBaseProps } from "./types";

vi.mock("./VolumetricLettersWorkspace", () => ({
  default: () => <div data-testid="volumetric-letters-workspace">Volumetric workspace</div>,
}));

const baseProps: TemplateWorkspaceBaseProps = {
  request: {
    id: "WI-SMOKE-P001",
    client: "TEST",
    contactPerson: "Smoke",
    channel: "email",
    productFamily: "litere_volumetrice",
    description: "smoke",
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
  productSpecInitial: { width_mm: 4800 },
  actionSummary: {
    templateLabel: "OK",
    templateOk: true,
    productSpecLabel: "OK",
    productSpecOk: true,
    terrainLabel: "N/A",
    terrainOk: null,
    intakeStatusLabel: "Ready",
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

describe("TemplateWorkspaceRouter", () => {
  it("routes volumetric template to VolumetricLettersWorkspace", () => {
    render(<TemplateWorkspaceRouter enabled {...baseProps} />);
    expect(screen.getByTestId("volumetric-letters-workspace")).toBeInTheDocument();
  });

  it("returns null when disabled", () => {
    const { container } = render(
      <TemplateWorkspaceRouter enabled={false} {...baseProps} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows unsupported fallback instead of blank for non-volumetric family", () => {
    render(
      <TemplateWorkspaceRouter
        enabled
        {...baseProps}
        confirmedTemplateCode={null}
        request={{
          ...baseProps.request,
          productFamily: "Totemuri / Pyloni",
          confirmedTemplateCode: null,
        }}
      />
    );
    expect(screen.getByTestId("unsupported-template-workspace")).toBeInTheDocument();
  });
});
