import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6OfferScopeReviewSummary from "./IntakeV6OfferScopeReviewSummary";

describe("IntakeV6OfferScopeReviewSummary", () => {
  it("keeps full-product scope compact without disclosure", () => {
    render(
      <IntakeV6OfferScopeReviewSummary
        payload={{
          offer_scope: {
            contract_version: "offer_scope_contract/v1",
            mode: "full_product",
            sold_modules: ["FACE", "RETURN-CANT", "BACK", "LIGHTING", "ELECTRICAL"],
          },
          offer_scope_confirmed: { confirmed: true },
        }}
      />,
    );

    expect(screen.getByTestId("intake-v6-review-offer-scope-full")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-review-offer-scope-disclosure")).not.toBeInTheDocument();
  });

  it("moves excluded components behind disclosure", () => {
    render(
      <IntakeV6OfferScopeReviewSummary
        payload={{
          offer_scope: {
            contract_version: "offer_scope_contract/v1",
            mode: "component_subset",
            sold_modules: ["FACE", "LIGHTING"],
          },
          offer_scope_confirmed: { confirmed: true },
        }}
      />,
    );

    expect(screen.queryByTestId("intake-v6-review-offer-scope-excluded")).not.toBeInTheDocument();
    const toggle = screen.getByTestId("intake-v6-review-offer-scope-disclosure");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("intake-v6-review-offer-scope-excluded")).toBeInTheDocument();
  });
});
