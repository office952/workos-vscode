import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ReviewBackingFinishRow from "./IntakeV6ReviewBackingFinishRow";

describe("IntakeV6ReviewBackingFinishRow", () => {
  it("renders finisaj spate dropdown with review field styling", () => {
    render(<IntakeV6ReviewBackingFinishRow backingMode="forex_10_no_bevel" onBackingChange={vi.fn()} />);
    expect(screen.getByTestId("intake-v6-backing-finish-row")).toBeInTheDocument();
    expect(screen.getByText("Finisaj spate")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-backing-mode")).toHaveClass("h-7");
    expect(screen.getByTestId("intake-v6-backing-mode")).toHaveDisplayValue("Forex 10 mm fara sanfren");
  });

  it("calls handler on change", () => {
    const onBacking = vi.fn();
    render(<IntakeV6ReviewBackingFinishRow backingMode="forex_10_no_bevel" onBackingChange={onBacking} />);
    fireEvent.change(screen.getByTestId("intake-v6-backing-mode"), {
      target: { value: "forex_10_with_bevel" },
    });
    expect(onBacking).toHaveBeenCalledWith("forex_10_with_bevel");
  });
});
