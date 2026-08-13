import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6PricingInputPanel from "./IntakeV6PricingInputPanel";
import type { IntakeV6MaterialBreakdownResponse, IntakeV6PricingInputPreviewResponse } from "@/lib/intakeV6/intakeV6Api";

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

  it("does not crash when EUR internal estimate has null company EUR/RON rate", () => {
    const preview: IntakeV6PricingInputPreviewResponse = {
      workspace_id: "ws-p0",
      adapter_status: "ready",
      is_ready_for_quote: true,
      readiness_status: "ready",
      requires_grouped_finish_review: false,
      production_counts: { letter_count: 1 },
      quote_input_payload: {},
      adapter_blockers: [],
      adapter_warnings: [],
    };
    const breakdown = {
      material_rows: [],
      consumable_rows: [],
      operation_rows: [],
      edge_cant_operation_rows: [],
      totals: {
        material_cost_total: 10,
        estimated_cost_total: 10,
        contains_missing_prices: false,
        currency: "EUR",
      },
    } as IntakeV6MaterialBreakdownResponse;

    expect(() =>
      render(
        <IntakeV6PricingInputPanel
          preview={preview}
          loading={false}
          breakdown={breakdown}
          eurToRonRate={null}
          variant="commercialSliders"
        />,
      ),
    ).not.toThrow();
    expect(screen.getByTestId("intake-v6-pricing-input-preview")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-offer-eur-ron-rate")).not.toBeInTheDocument();
  });
});
