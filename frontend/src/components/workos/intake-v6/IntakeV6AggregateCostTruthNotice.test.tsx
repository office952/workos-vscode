import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { IntakeV6AggregateCostTruthNotice } from "./IntakeV6AggregateCostTruthNotice";

describe("IntakeV6AggregateCostTruthNotice", () => {
  it("states dry-run and v2_aggregate source without implying quote priced", () => {
    render(<IntakeV6AggregateCostTruthNotice />);
    const notice = screen.getByTestId("intake-v6-aggregate-cost-truth-notice");
    expect(notice).toHaveTextContent(/nu este quote priced/i);
    expect(notice).toHaveTextContent(/v2_aggregate/i);
    expect(notice).toHaveTextContent(/aprobare owner/i);
  });
});
