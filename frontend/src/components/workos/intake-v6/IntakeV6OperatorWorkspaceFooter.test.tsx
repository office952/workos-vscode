import { cleanup, fireEvent, render, within } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import IntakeV6OperatorWorkspaceFooter from "./IntakeV6OperatorWorkspaceFooter";
import { IntakeV6WorkspaceHeaderStatusProvider, useIntakeV6WorkspaceHeaderStatus } from "./IntakeV6WorkspaceHeaderStatusContext";
import type { IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";

const EMPTY_WARNINGS: readonly string[] = [];

function baseWorkspaceState(overrides: Partial<IntakeV6WorkspaceState> = {}): IntakeV6WorkspaceState {
  return {
    workspaceId: "ws-1",
    phase: "svg_ready",
    error: null,
    loadErrorCode: null,
    currentStep: "layers",
    workspace: {
      id: "ws-1",
      workspace_code: "IV6-TEST",
      title: "Test",
      template_code: "TPL-VOLUMETRIC-LETTERS",
      status: "draft",
      readiness_status: "layer_roles_incomplete",
      updated_at: "2026-07-19T12:00:00Z",
      payload: {
        svg_source: { file_hash: "hash-a", upload_status: "analyzed" },
        svg_analysis_json: { layers: [] },
        layer_role_setup: { confirmation_status: "incomplete", layers: [] },
      },
    },
    svg: { fileName: "logo.svg", fileSizeBytes: 1200, previewSource: null },
    layerChips: [
      { layerKey: "a", displayName: "A", status: "pending" },
      { layerKey: "b", displayName: "B", status: "pending" },
    ],
    analysisRunId: 1,
    analyzerStatus: "ready",
    analyzerError: null,
    svgSource: null,
    analyzerReport: null,
    layerRoleConfirmation: null,
    localFileHash: "hash-a",
    unsavedAnalysis: false,
    ...overrides,
  } as IntakeV6WorkspaceState;
}

function OverlaySeed({
  reviewWarnings = EMPTY_WARNINGS,
  secondaryWarnings = EMPTY_WARNINGS,
  layersTotal = 2,
  layersConfirmed = 0,
}: {
  reviewWarnings?: readonly string[];
  secondaryWarnings?: readonly string[];
  layersTotal?: number;
  layersConfirmed?: number;
}) {
  const { setOverlay } = useIntakeV6WorkspaceHeaderStatus();
  useEffect(() => {
    setOverlay({ layersTotal, layersConfirmed, reviewWarnings, secondaryWarnings });
  }, [layersConfirmed, layersTotal, reviewWarnings, secondaryWarnings, setOverlay]);
  return null;
}

function renderFooter(
  overrides: Partial<Parameters<typeof IntakeV6OperatorWorkspaceFooter>[0]> = {},
  overlay: { reviewWarnings?: string[]; secondaryWarnings?: string[]; layersTotal?: number; layersConfirmed?: number } = {},
) {
  const props: Parameters<typeof IntakeV6OperatorWorkspaceFooter>[0] = {
    currentStep: "layers",
    stepIndex: 0,
    stepOrderLength: 3,
    footerBlocker: "Confirmă rolul pentru toate straturile.",
    nextDisabled: true,
    nextLabel: "Continuă la Review",
    nextButtonClassName: "test-next",
    onBack: vi.fn(),
    onNext: vi.fn(),
    persisting: false,
    workspaceState: baseWorkspaceState(),
    ...overrides,
  };

  return render(
    <IntakeV6WorkspaceHeaderStatusProvider>
      <OverlaySeed {...overlay} />
      <IntakeV6OperatorWorkspaceFooter {...props} />
    </IntakeV6WorkspaceHeaderStatusProvider>,
  );
}

describe("IntakeV6OperatorWorkspaceFooter", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows guidance spine with next action outside the collapsed drawer", () => {
    const view = renderFooter();
    const footer = within(view.container);

    expect(footer.getByTestId("intake-v6-guidance-spine")).toBeInTheDocument();
    expect(footer.getByTestId("intake-v6-guidance-next-action")).toHaveTextContent(
      /Confirmă rolul pentru toate straturile/i,
    );
    expect(footer.getByTestId("intake-v6-footer-issues-toggle")).toHaveAttribute("aria-expanded", "false");
  });

  it("keeps grouped issues collapsed until expanded", () => {
    const view = renderFooter(
      { nextDisabled: false, footerBlocker: null },
      { reviewWarnings: ["Verifică lățimea cantului."], layersTotal: 0, layersConfirmed: 0 },
    );
    const footer = within(view.container);

    expect(footer.queryByText("Verifică lățimea cantului.")).not.toBeInTheDocument();
    fireEvent.click(footer.getByTestId("intake-v6-footer-issues-toggle"));
    expect(footer.getByTestId("intake-v6-footer-issues-content")).toHaveTextContent("Verifică lățimea cantului.");
  });

  it("includes secondary analysis warnings in the collapsed footer groups", () => {
    const view = renderFooter(
      { nextDisabled: false, footerBlocker: null },
      {
        secondaryWarnings: ["2 straturi propuse ca Vector Litere — confirmă rolurile."],
        layersTotal: 0,
        layersConfirmed: 0,
      },
    );
    const footer = within(view.container);

    fireEvent.click(footer.getByTestId("intake-v6-footer-issues-toggle"));
    expect(footer.getByTestId("intake-v6-footer-group-warnings")).toHaveTextContent(/Vector Litere/i);
  });
});
