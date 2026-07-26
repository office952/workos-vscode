import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6ConfirmConsolidatedStatusPanel from "./IntakeV6ConfirmConsolidatedStatusPanel";
import { buildIntakeV6ConfirmConsolidatedStatus } from "@/lib/intakeV6/intakeV6ConfirmConsolidatedStatus";

describe("IntakeV6ConfirmConsolidatedStatusPanel", () => {
  it("renders consolidated status panel with tier metadata", () => {
    const status = buildIntakeV6ConfirmConsolidatedStatus({
      loading: false,
      finishSetupIncomplete: false,
      effectiveHandoffAllowed: true,
      bindingBlockers: [],
      allFatalBlockers: [],
      artworkNeedsDecision: false,
      reviewWarnings: [],
      containsMissingPrices: false,
      operatorConfirmationComplete: true,
      confirmInternalDraft: true,
      confirmDraftBoundary: true,
      showHandoffCheckboxes: true,
      checklistProgress: { done: 3, total: 3 },
      modularPendingCount: 0,
    });

    render(<IntakeV6ConfirmConsolidatedStatusPanel status={status} />);

    expect(screen.getByTestId("intake-v6-confirm-consolidated-status")).toHaveAttribute(
      "data-status-tier",
      "ready",
    );
    expect(screen.getByTestId("intake-v6-confirm-consolidated-headline")).toHaveTextContent(
      /Pregătit pentru confirmare/i,
    );
  });
});
