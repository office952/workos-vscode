import { render, screen } from "@testing-library/react";
import { useEffect } from "react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6OperatorWorkspaceFooter from "./IntakeV6OperatorWorkspaceFooter";
import { IntakeV6WorkspaceHeaderStatusProvider, useIntakeV6WorkspaceHeaderStatus } from "./IntakeV6WorkspaceHeaderStatusContext";

function OverlaySeed() {
  const { setOverlay } = useIntakeV6WorkspaceHeaderStatus();
  useEffect(() => {
    setOverlay({ layersTotal: 6, layersConfirmed: 0 });
  }, [setOverlay]);
  return null;
}

function renderFooter(overrides: Partial<Parameters<typeof IntakeV6OperatorWorkspaceFooter>[0]> = {}) {
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
    ...overrides,
  };

  return render(
    <IntakeV6WorkspaceHeaderStatusProvider>
      <OverlaySeed />
      <IntakeV6OperatorWorkspaceFooter {...props} />
    </IntakeV6WorkspaceHeaderStatusProvider>,
  );
}

describe("IntakeV6OperatorWorkspaceFooter", () => {
  it("shows Product Truth blocker summary next to disabled Continue to Review CTA", () => {
    renderFooter();

    expect(screen.getByTestId("intake-v6-footer-next")).toBeDisabled();
    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).toHaveTextContent("BLOCKED");
    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).toHaveTextContent("NEEDS_CONFIRMATION");
    expect(screen.getByTestId("intake-v6-disabled-cta-summary-title")).toHaveTextContent(
      "Product Truth incomplet",
    );
    expect(screen.getByTestId("intake-v6-disabled-cta-summary-message")).toHaveTextContent(
      /Rolurile layerelor\/grupurilor trebuie confirmate/i,
    );
    expect(screen.getByTestId("intake-v6-disabled-cta-summary-submessage")).toHaveTextContent(
      /Pricing Registry este pregătit/i,
    );
    expect(screen.getByTestId("intake-v6-disabled-cta-summary-submessage")).toHaveTextContent(
      /6 grupuri\/straturi detectate/i,
    );
    expect(screen.getByTestId("intake-v6-disabled-cta-summary-next-action")).toHaveTextContent(
      /Confirmă rolurile pentru toate grupurile detectate/i,
    );
    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).not.toHaveTextContent(/pricing not ready/i);
    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).not.toHaveTextContent(/ora|minut/i);
  });

  it("keeps real pricing coverage distinct from Product Truth blocker", () => {
    renderFooter({
      currentStep: "confirm",
      footerBlocker: "Calculul live conține linii fără tarif configurat.",
      nextDisabled: true,
    });

    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).toHaveTextContent(
      "Pricing coverage de verificat",
    );
    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).toHaveTextContent("WARNING");
    expect(screen.getByTestId("intake-v6-disabled-cta-summary")).toHaveTextContent("NEEDS_FORM_INPUT");
  });

  it("does not show disabled summary when CTA is enabled", () => {
    renderFooter({ nextDisabled: false, footerBlocker: "Confirmă rolul pentru toate straturile." });

    expect(screen.getByTestId("intake-v6-footer-next")).toBeEnabled();
    expect(screen.queryByTestId("intake-v6-disabled-cta-summary")).not.toBeInTheDocument();
  });
});
