import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6PricingInputPanel from "./IntakeV6PricingInputPanel";

describe("IntakeV6PricingInputPanel", () => {
  it("does not blame Pricing Registry when pricing preview is unavailable before Product Truth", () => {
    render(<IntakeV6PricingInputPanel preview={null} loading={false} />);

    const panel = screen.getByTestId("intake-v6-pricing-input-preview");
    expect(panel).toHaveTextContent(/Product Truth incomplet/i);
    expect(panel).toHaveTextContent(/confirmarea operatorului/i);
    expect(panel).not.toHaveTextContent(/Pricing Registry/i);
    expect(panel).not.toHaveTextContent(/pricing not ready/i);
    expect(panel).not.toHaveTextContent(/ora|minut/i);
  });
});
