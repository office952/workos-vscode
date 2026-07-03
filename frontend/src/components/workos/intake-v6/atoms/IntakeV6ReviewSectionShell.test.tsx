import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6ReviewSectionShell from "@/components/workos/intake-v6/atoms/IntakeV6ReviewSectionShell";

describe("IntakeV6ReviewSectionShell", () => {
  it("renders title, description, badge and content region", () => {
    render(
      <IntakeV6ReviewSectionShell
        title="Față litere"
        description="Finisaj față pe grupuri."
        testId="intake-v6-review-section-face-letters"
        badge={{ label: "Operator", tone: "action" }}
      >
        <p>child content</p>
      </IntakeV6ReviewSectionShell>,
    );

    expect(screen.getByTestId("intake-v6-review-section-face-letters")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-section-face-letters-content")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Față litere" })).toBeInTheDocument();
    expect(screen.getByText("Finisaj față pe grupuri.")).toBeInTheDocument();
    expect(screen.getByText("Operator")).toBeInTheDocument();
    expect(screen.getByText("child content")).toBeInTheDocument();
  });
});
