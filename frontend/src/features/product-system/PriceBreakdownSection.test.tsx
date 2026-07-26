import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { PriceBreakdownSection } from "./PriceBreakdownSection";

vi.mock("@/api/productPriceBreakdown", () => ({
  productPriceBreakdownApi: {
    postBreakdown: vi.fn(),
  },
}));

import { productPriceBreakdownApi } from "@/api/productPriceBreakdown";

const mockBreakdown = {
  schema_version: "1.0.0",
  template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  configuration_id: "vl_letters_demo_v1",
  fixture_id: "vl_letters_demo_v1",
  currency: "RON",
  ownership_note_ro: "Desfășurătorul explică CPP și EIC.",
  operational_readiness: "ACTIVE_WITH_AI_DEFAULTS",
  uses_ai_defaults: true,
  configuration_summary: { has_quote_input: true },
  lines: [
    {
      line_id: "vl::commercial::debitare_fata",
      line_group: "machine" as const,
      resource_code: "debitare_fata",
      display_name: "Debitare față",
      formula_display: "12.5 ml × 25 RON/ml",
      quantity: 12.5,
      unit: "ml",
      base_value: 25,
      currency: "RON",
      source_type: "catalog",
      commercial_value: 312.5,
      internal_cost: null,
      configurable: false,
      warning: null,
    },
    {
      line_id: "vl::ai::AI_LED_PER_MODULE",
      line_group: "ai_decision" as const,
      resource_code: "LED_ASSEMBLY",
      display_name: "Montaj LED",
      formula_display: "letter_led_module_count × rate_per_module",
      source_type: "AI_DECISION",
      base_value: 0.35,
      currency: "EUR",
      configurable: true,
      warning: "Valoare AI activă",
    },
  ],
  group_totals: [
    {
      line_group: "machine" as const,
      line_count: 1,
      commercial_subtotal: 312.5,
      internal_subtotal: null,
      currency: "RON",
    },
  ],
  totals: {
    commercial_total: 1061,
    internal_total: 923.2,
    currency: "RON",
    cpp_total_matches: true,
    eic_total_matches: true,
    no_duplicate_commercial_codes: true,
    no_duplicate_internal_codes: true,
    ai_contribution_note_ro: "4 decizii AI",
  },
  ai_decisions: [],
  calibration_hooks: [],
  warnings: [],
  blockers: [],
  eic_provenance: [],
  cpp_provenance: [],
};

describe("PriceBreakdownSection", () => {
  beforeEach(() => {
    vi.mocked(productPriceBreakdownApi.postBreakdown).mockResolvedValue(
      mockBreakdown as never,
    );
  });

  it("renders Desfășurător preț with totals and lines", async () => {
    render(<PriceBreakdownSection templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    await waitFor(() => {
      expect(screen.getByTestId("price-breakdown-section")).toBeInTheDocument();
    });
    expect(screen.getByText(/Desfășurător preț/i)).toBeInTheDocument();
    expect(screen.getByTestId("price-breakdown-totals")).toHaveTextContent("1061.00");
    expect(screen.getByTestId("price-breakdown-fixture")).toHaveTextContent(
      "vl_letters_demo_v1",
    );
    expect(screen.getByText("Debitare față")).toBeInTheDocument();
    expect(screen.getByText(/12\.5 ml × 25 RON\/ml/)).toBeInTheDocument();
  });
});
