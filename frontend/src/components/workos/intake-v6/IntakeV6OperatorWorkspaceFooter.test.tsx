import { fireEvent, render, screen } from "@testing-library/react";
import { useEffect } from "react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6OperatorWorkspaceFooter from "./IntakeV6OperatorWorkspaceFooter";
import { IntakeV6WorkspaceHeaderStatusProvider, useIntakeV6WorkspaceHeaderStatus } from "./IntakeV6WorkspaceHeaderStatusContext";
import type { IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";

function baseWorkspaceState(overrides: Partial<IntakeV6WorkspaceState> = {}): IntakeV6WorkspaceState {
  return {
    workspaceId: "ws-1",
    phase: "svg_ready",
    error: null,
    loadErrorCode: null,
    currentStep: "layers",
    workspace: null,
    svg: { fileName: "logo.svg", fileSizeBytes: 1200, previewSource: null },
    layerChips: [
      { layerKey: "a", displayName: "A", status: "pending" },
      { layerKey: "b", displayName: "B", status: "pending" },
      { layerKey: "c", displayName: "C", status: "pending" },
      { layerKey: "d", displayName: "D", status: "pending" },
      { layerKey: "e", displayName: "E", status: "pending" },
      { layerKey: "f", displayName: "F", status: "pending" },
    ],
    analysisRunId: 1,
    analyzerStatus: "ready",
    analyzerError: null,
    svgSource: null,
    analyzerReport: null,
    layerRoleConfirmation: null,
    localFileHash: null,
    unsavedAnalysis: false,
    ...overrides,
  };
}

function OverlaySeed({
  reviewWarnings = [],
  layersTotal = 6,
  layersConfirmed = 0,
}: {
  reviewWarnings?: string[];
  layersTotal?: number;
  layersConfirmed?: number;
}) {
  const { setOverlay } = useIntakeV6WorkspaceHeaderStatus();
  useEffect(() => {
    setOverlay({ layersTotal, layersConfirmed, reviewWarnings });
  }, [layersConfirmed, layersTotal, reviewWarnings, setOverlay]);
  return null;
}

function renderFooter(
  overrides: Partial<Parameters<typeof IntakeV6OperatorWorkspaceFooter>[0]> = {},
  reviewWarnings: string[] = [],
  overlayCounts: { layersTotal?: number; layersConfirmed?: number } = {},
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
      <OverlaySeed reviewWarnings={reviewWarnings} {...overlayCounts} />
      <IntakeV6OperatorWorkspaceFooter {...props} />
    </IntakeV6WorkspaceHeaderStatusProvider>,
  );
}

describe("IntakeV6OperatorWorkspaceFooter", () => {
  it("keeps the issues drawer collapsed next to disabled Continue to Review CTA", () => {
    renderFooter();

    expect(screen.getByTestId("intake-v6-footer-next")).toBeDisabled();
    expect(screen.getByTestId("intake-v6-footer-issues-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId("intake-v6-footer-issues-content")).not.toBeInTheDocument();
  });

  it("shows the blocker only after expanding the issues drawer", () => {
    renderFooter({
      currentStep: "confirm",
      footerBlocker: "Calculul live conține linii fără tarif configurat.",
      nextDisabled: true,
    });

    expect(screen.queryByText("Calculul live conține linii fără tarif configurat.")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-footer-issues-toggle"));
    expect(screen.getByTestId("intake-v6-footer-issues-content")).toHaveTextContent(
      "Calculul live conține linii fără tarif configurat.",
    );
  });

  it("counts review warnings in the collapsed issues title", () => {
    renderFooter(
      {
        nextDisabled: false,
        footerBlocker: null,
        workspaceState: baseWorkspaceState({ layerChips: [] }),
      },
      ["Verifica latimea cantului."],
      { layersTotal: 0, layersConfirmed: 0 },
    );

    expect(screen.getByTestId("intake-v6-footer-next")).toBeEnabled();
    expect(screen.getByTestId("intake-v6-footer-issues-toggle")).toHaveTextContent(
      "Probleme & acțiuni necesare (1)",
    );
    expect(screen.queryByText("Verifica latimea cantului.")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-footer-issues-toggle"));
    expect(screen.getByTestId("intake-v6-footer-issues-content")).toHaveTextContent(
      "Verifica latimea cantului.",
    );
  });
});
