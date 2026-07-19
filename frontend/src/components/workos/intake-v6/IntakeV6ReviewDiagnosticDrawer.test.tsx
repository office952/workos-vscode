import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6ReviewDiagnosticDrawer from "./IntakeV6ReviewDiagnosticDrawer";

describe("IntakeV6ReviewDiagnosticDrawer", () => {
  it("keeps diagnostic content out of the document when closed", () => {
    render(
      <IntakeV6ReviewDiagnosticDrawer open={false} onOpenChange={() => undefined}>
        <p>Product Truth Promotion Planner</p>
      </IntakeV6ReviewDiagnosticDrawer>,
    );
    expect(screen.getByTestId("intake-v6-review-diagnostic-entry")).toBeInTheDocument();
    expect(screen.queryByText("Product Truth Promotion Planner")).not.toBeInTheDocument();
  });

  it("mounts content only when open", () => {
    const onOpenChange = vi.fn();
    const { rerender } = render(
      <IntakeV6ReviewDiagnosticDrawer open={false} onOpenChange={onOpenChange}>
        <p>Runtime Capture</p>
      </IntakeV6ReviewDiagnosticDrawer>,
    );
    fireEvent.click(screen.getByTestId("intake-v6-review-technical-details-toggle"));
    expect(onOpenChange).toHaveBeenCalledWith(true);

    rerender(
      <IntakeV6ReviewDiagnosticDrawer open onOpenChange={onOpenChange}>
        <p>Runtime Capture</p>
      </IntakeV6ReviewDiagnosticDrawer>,
    );
    expect(screen.getByTestId("intake-v6-review-diagnostic-drawer")).toBeInTheDocument();
    expect(screen.getByText("Runtime Capture")).toBeInTheDocument();
  });
});
