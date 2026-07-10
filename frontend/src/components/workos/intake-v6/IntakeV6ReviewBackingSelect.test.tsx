import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ReviewBackingSelect from "./IntakeV6ReviewBackingSelect";

describe("IntakeV6ReviewBackingSelect", () => {
  it("shows compact backing select without a no-backing option", () => {
    render(<IntakeV6ReviewBackingSelect backingMode="forex_10_no_bevel" onBackingChange={vi.fn()} />);
    expect(screen.getByTestId("intake-v6-backing-section")).toBeInTheDocument();
    expect(screen.getByText("Spate litere")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-backing-mode")).toHaveDisplayValue("Forex 10 mm fara sanfren");
    expect(screen.queryByRole("option", { name: /Fara spate|Fără spate/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/60 module LED/)).not.toBeInTheDocument();
  });

  it("calls handler on change", () => {
    const onBacking = vi.fn();
    render(<IntakeV6ReviewBackingSelect backingMode="forex_10_no_bevel" onBackingChange={onBacking} />);
    fireEvent.change(screen.getByTestId("intake-v6-backing-mode"), {
      target: { value: "forex_10_with_bevel" },
    });
    expect(onBacking).toHaveBeenCalledWith("forex_10_with_bevel");
  });

  it("renders embedded row with finisaje field styling", () => {
    render(<IntakeV6ReviewBackingSelect backingMode="forex_10_no_bevel" onBackingChange={vi.fn()} embedded />);
    expect(screen.getByTestId("intake-v6-backing-finish-row")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-backing-section")).not.toBeInTheDocument();
    expect(screen.getByText("Spate litere")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-backing-mode")).toHaveClass("h-7");
  });
});