import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6ConfirmHandoffPanel from "./IntakeV6ConfirmHandoffPanel";

const baseProps = {
  finishSetupIncomplete: false,
  confirmDraftBoundary: false,
  showHandoffCheckboxes: true,
  canResolveInternalDraftConfirmation: true,
  savingInternalConfirmation: false,
  allFatalBlockers: [] as string[],
  showBlockerList: false,
  resultMessage: null as string | null,
  errorMessage: null as string | null,
  fallbackBlockerMessage: null as string | null,
  onInternalDraftChange: vi.fn(),
  onDraftBoundaryChange: vi.fn(),
};

describe("IntakeV6ConfirmHandoffPanel confirmation hydration", () => {
  it("hydrates checked when persisted confirmation is true", () => {
    render(
      <IntakeV6ConfirmHandoffPanel
        {...baseProps}
        operatorConfirmationComplete
        confirmInternalDraft
        confirmationHydrationPending={false}
      />,
    );
    expect(screen.getByTestId("intake-v6-confirm-internal-draft")).toBeChecked();
  });

  it("hydrates unchecked when persisted confirmation is false", () => {
    render(
      <IntakeV6ConfirmHandoffPanel
        {...baseProps}
        operatorConfirmationComplete={false}
        confirmInternalDraft={false}
        confirmationHydrationPending={false}
      />,
    );
    expect(screen.getByTestId("intake-v6-confirm-internal-draft")).not.toBeChecked();
  });

  it("does not present unchecked as settled truth while hydration is pending", () => {
    render(
      <IntakeV6ConfirmHandoffPanel
        {...baseProps}
        operatorConfirmationComplete={false}
        confirmInternalDraft={false}
        confirmationHydrationPending
      />,
    );
    const checkbox = screen.getByTestId("intake-v6-confirm-internal-draft");
    expect(checkbox).toBeDisabled();
    expect(checkbox).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("Se verifică confirmarea persistată…")).toBeInTheDocument();
  });

  it("shows load error without assuming confirmation is false", () => {
    render(
      <IntakeV6ConfirmHandoffPanel
        {...baseProps}
        operatorConfirmationComplete={false}
        confirmInternalDraft={false}
        confirmationHydrationPending={false}
        confirmationLoadError="Failed to fetch"
      />,
    );
    expect(screen.getByTestId("intake-v6-confirmation-load-error")).toBeInTheDocument();
  });
});
