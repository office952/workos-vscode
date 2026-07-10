import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6TechnicalDetailsAccordion from "./IntakeV6TechnicalDetailsAccordion";

describe("IntakeV6TechnicalDetailsAccordion", () => {
  it("renders renamed title, count, and stays collapsed by default", () => {
    render(
      <IntakeV6TechnicalDetailsAccordion
        title="Detalii tehnice și diagnostic"
        itemCount={4}
        hint="Pentru verificare avansată"
        testId="intake-v6-review-technical-details"
      >
        <p data-testid="raw-code">SELECTED_LAYER_REFS_MISSING</p>
      </IntakeV6TechnicalDetailsAccordion>,
    );

    expect(screen.getByText("Detalii tehnice și diagnostic")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-technical-details-count")).toHaveTextContent("4 elemente");
    expect(screen.getByTestId("intake-v6-review-technical-details")).toHaveAttribute("data-expanded", "false");
    expect(screen.queryByTestId("raw-code")).not.toBeInTheDocument();
    expect(screen.getByText("Pentru verificare avansată")).toBeInTheDocument();
  });

  it("shows raw content after expand and supports controlled open state", () => {
    const onOpenChange = vi.fn();
    render(
      <IntakeV6TechnicalDetailsAccordion
        title="Detalii tehnice și diagnostic"
        open={false}
        onOpenChange={onOpenChange}
        itemCount={2}
        testId="intake-v6-review-technical-details"
      >
        <p data-testid="raw-code">SELECTED_LAYER_REFS_MISSING</p>
      </IntakeV6TechnicalDetailsAccordion>,
    );

    fireEvent.click(screen.getByTestId("intake-v6-review-technical-details-toggle"));
    expect(onOpenChange).toHaveBeenCalledWith(true);
    expect(screen.queryByTestId("raw-code")).not.toBeInTheDocument();
  });

  it("shows content when controlled open is true", () => {
    render(
      <IntakeV6TechnicalDetailsAccordion
        title="Detalii tehnice și diagnostic"
        open
        itemCount={1}
        testId="intake-v6-review-technical-details"
      >
        <p data-testid="raw-code">SELECTED_LAYER_REFS_MISSING</p>
      </IntakeV6TechnicalDetailsAccordion>,
    );

    expect(screen.getByTestId("raw-code")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-technical-details")).toHaveAttribute("data-expanded", "true");
  });
});
