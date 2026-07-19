import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6LayerStatusIcon from "./IntakeV6LayerStatusIcon";

describe("IntakeV6LayerStatusIcon", () => {
  it("renders icon-only status with accessible label", () => {
    render(<IntakeV6LayerStatusIcon state="confirmed" testId="status-confirmed" />);
    const icon = screen.getByTestId("status-confirmed");
    expect(icon).toHaveAttribute("aria-label", "Confirmat");
    expect(icon).toHaveAttribute("data-layer-status", "confirmed");
    expect(icon.textContent).toBe("");
  });

  it("defaults pending state when undefined", () => {
    render(<IntakeV6LayerStatusIcon state={undefined} />);
    expect(screen.getByTestId("intake-v6-layer-status-pending")).toHaveAttribute(
      "aria-label",
      "Necesită confirmare",
    );
  });
});
