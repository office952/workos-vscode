import { describe, expect, it } from "vitest";
import {
  estimateOrderRonFromEurQuote,
  extractOrderCommercialHandoff,
  roundCommercialTotalEur,
} from "./orderCurrency";

describe("orderCurrency", () => {
  it("rounds EUR commercial totals to whole euros", () => {
    expect(roundCommercialTotalEur(1412.15)).toBe(1412);
  });

  it("estimates RON order total from EUR quote and settings rate", () => {
    expect(estimateOrderRonFromEurQuote(1412.15, 5)).toBe(7060);
  });

  it("extracts commercial handoff from order snapshot JSON", () => {
    const handoff = extractOrderCommercialHandoff(
      JSON.stringify({
        commercial_currency_handoff: {
          commercial_currency: "EUR",
          base_currency: "RON",
          commercial_total_eur: 1412,
          exchange_rate_eur_ron: 5,
          base_total_ron: 7060,
        },
      })
    );
    expect(handoff?.base_total_ron).toBe(7060);
    expect(handoff?.commercial_total_eur).toBe(1412);
  });
});
