import { describe, expect, it } from "vitest";
import {
  DEFAULT_QUOTE_CURRENCY,
  extractQuoteCurrencyFromLineItems,
  formatQuoteMoney,
  quoteCurrencyLabel,
} from "./quoteCurrency";

describe("extractQuoteCurrencyFromLineItems", () => {
  it("returns EUR from canonical snapshot cost_result", () => {
    const raw = JSON.stringify({
      product_definition: { template_code: "TPL-VOLUMETRIC-LETTERS" },
      cost_result: { currency: "EUR", total_cost: 768 },
      pricing: {},
      price: 768,
    });
    expect(extractQuoteCurrencyFromLineItems(raw)).toBe("EUR");
  });

  it("returns EUR from Shape B wrapper around canonical snapshot", () => {
    const raw = JSON.stringify({
      line_items: {
        product_definition: { template_code: "TPL-VOLUMETRIC-LETTERS" },
        cost_result: { currency: "EUR", total_cost: 768 },
        pricing: {},
        price: 768,
      },
    });
    expect(extractQuoteCurrencyFromLineItems(raw)).toBe("EUR");
  });

  it("falls back to RON for legacy flat line items", () => {
    const raw = JSON.stringify([{ description: "Line", quantity: 1, total: 100 }]);
    expect(extractQuoteCurrencyFromLineItems(raw)).toBe(DEFAULT_QUOTE_CURRENCY);
  });
});

describe("formatQuoteMoney", () => {
  it("formats amount with currency code", () => {
    expect(formatQuoteMoney(768, "EUR")).toContain("768");
    expect(formatQuoteMoney(768, "EUR")).toContain("EUR");
    expect(formatQuoteMoney(768, "EUR")).not.toContain("RON");
  });
});

describe("quoteCurrencyLabel", () => {
  it("uses single currency when all quotes share it", () => {
    expect(quoteCurrencyLabel([{ currency: "EUR" }, { currency: "EUR" }])).toEqual({
      label: "EUR (cu TVA)",
      mixed: false,
    });
  });

  it("marks mixed currencies", () => {
    expect(quoteCurrencyLabel([{ currency: "EUR" }, { currency: "RON" }])).toEqual({
      label: "valori în monede diferite",
      mixed: true,
    });
  });
});
