import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6ComponentQuestionBadges from "./IntakeV6ComponentQuestionBadges";

describe("IntakeV6ComponentQuestionBadges", () => {
  it("renders support and mounting labels without changing readiness state", () => {
    render(
      <>
        <IntakeV6ComponentQuestionBadges question="supportBars" testId="support-badges" />
        <IntakeV6ComponentQuestionBadges question="mountingScope" testId="mounting-badges" />
      </>,
    );

    expect(screen.getByTestId("support-badges")).toHaveTextContent("Component: Support");
    expect(screen.getByTestId("support-badges")).toHaveTextContent(
      "Product Truth candidate when support affects offer",
    );
    expect(screen.getByTestId("support-badges")).toHaveTextContent("Optional unless detected/suggested");
    expect(screen.getByTestId("support-badges")).toHaveTextContent("Ask/select if not detected in SVG");
    expect(screen.getByTestId("support-badges")).toHaveTextContent("Quote blocker conditional");
    expect(screen.getByTestId("support-badges")).toHaveTextContent(
      "Missing UI gap: first-class support required/type/material",
    );
    expect(screen.getByTestId("support-badges")).toHaveTextContent(
      "metal_support_required means Support/Bare, not mounting method",
    );
    expect(screen.getByTestId("support-badges")).toHaveTextContent(
      "Support and mounting are separate decisions",
    );
    expect(screen.getByTestId("mounting-badges")).toHaveTextContent("Component: Mounting");
    expect(screen.getByTestId("mounting-badges")).toHaveTextContent("Product Truth candidate");
    expect(screen.getByTestId("mounting-badges")).toHaveTextContent(
      "Required for quote when mounting included/external",
    );
    expect(screen.getByTestId("mounting-badges")).toHaveTextContent(
      "mounting_system is Mounting, not Support truth",
    );
    expect(screen.getByTestId("mounting-badges")).toHaveTextContent(
      "Order/execution for site and method details",
    );
    expect(screen.getByTestId("mounting-badges")).toHaveTextContent(
      "Missing UI gap: included/external commercial scope control",
    );
    expect(screen.queryByText(/unlock|ready for quote/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/price by hour|minute pricing|lei\s*\/\s*or[ăa]/i)).not.toBeInTheDocument();
  });

  it("renders Product Truth and Pricing Registry boundary as display-only copy", () => {
    render(<IntakeV6ComponentQuestionBadges question="pricingBoundary" testId="pricing-boundary-badges" />);

    expect(screen.getByTestId("pricing-boundary-badges")).toHaveTextContent(
      "Pricing Registry does not decide Product Truth",
    );
    expect(screen.getByTestId("pricing-boundary-badges")).toHaveTextContent("Not Product Truth");
    expect(screen.getByTestId("pricing-boundary-badges")).toHaveTextContent(
      "Product Truth first; pricing coverage after truth",
    );
    expect(screen.getByTestId("pricing-boundary-badges")).toHaveTextContent("CostEngine internal-only");
    expect(screen.getByTestId("pricing-boundary-badges")).not.toHaveTextContent(/hour|minute|ora|oră|minut/i);
  });
});