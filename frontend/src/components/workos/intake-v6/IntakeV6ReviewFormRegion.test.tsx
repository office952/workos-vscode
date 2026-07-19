import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6ReviewFormRegion from "./IntakeV6ReviewFormRegion";

describe("IntakeV6ReviewFormRegion", () => {
  it("connects tab chrome and form body as one unit", () => {
    render(
      <IntakeV6ReviewFormRegion
        tabNav={<div data-testid="intake-v6-review-tabs">tabs</div>}
        attention={<button type="button">! 2</button>}
      >
        <p>form fields</p>
      </IntakeV6ReviewFormRegion>,
    );
    expect(screen.getByTestId("intake-v6-review-form-region")).toHaveAttribute(
      "data-form-leads",
      "true",
    );
    expect(screen.getByTestId("intake-v6-review-form-body")).toHaveTextContent("form fields");
    expect(screen.getByTestId("intake-v6-review-attention-slot")).toBeInTheDocument();
  });
});
