import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { IntakeV6AggregateCostTruthNotice } from "./IntakeV6AggregateCostTruthNotice";

describe("IntakeV6AggregateCostTruthNotice", () => {
  it("separates Ofertă client from Cost intern estimativ without implying order/tasks", () => {
    render(<IntakeV6AggregateCostTruthNotice />);
    const notice = screen.getByTestId("intake-v6-aggregate-cost-truth-notice");
    expect(notice).toHaveTextContent(/Ofertă client/i);
    expect(notice).toHaveTextContent(/Cost intern estimativ/i);
    expect(notice).toHaveTextContent(/nu creează comandă/i);
    expect(notice).toHaveTextContent(/Product Compiler/i);
    expect(notice).toHaveTextContent(/Registr/i);
  });

  it("compact mode keeps offer vs internal cost boundary", () => {
    render(<IntakeV6AggregateCostTruthNotice compact />);
    const notice = screen.getByTestId("intake-v6-aggregate-cost-truth-notice");
    expect(notice).toHaveTextContent(/Ofertă client/i);
    expect(notice).toHaveTextContent(/Cost intern estimativ/i);
  });
});
