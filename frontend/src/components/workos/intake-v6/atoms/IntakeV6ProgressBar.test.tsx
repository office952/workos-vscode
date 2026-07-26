import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6ProgressBar from "./IntakeV6ProgressBar";

describe("IntakeV6ProgressBar honesty", () => {
  it("does not mark Configurare complete when readiness says incomplete", () => {
    render(
      <IntakeV6ProgressBar
        currentStep="confirm"
        isStepComplete={(step) => step === "layers"}
      />,
    );
    const review = screen.getByTestId("intake-v6-progress-step-review");
    expect(review).toHaveAttribute("data-step-complete", "false");
    expect(review).toHaveTextContent("2");
    expect(review).not.toHaveTextContent("✓");
  });

  it("marks Configurare complete only when predicate says so", () => {
    render(
      <IntakeV6ProgressBar
        currentStep="confirm"
        isStepComplete={(step) => step === "layers" || step === "review"}
      />,
    );
    expect(screen.getByTestId("intake-v6-progress-step-review")).toHaveAttribute(
      "data-step-complete",
      "true",
    );
  });
});
