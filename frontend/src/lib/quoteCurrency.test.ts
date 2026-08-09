import { describe, expect, it } from "vitest";
import {
  extractQuoteCurrencyFromLineItems,
  formatCommercialAmount,
  formatQuoteListKpiAmount,
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

  it("returns EUR from commercial_totals when present", () => {
    const raw = JSON.stringify({
      product_definition: { template_code: "TPL-VOLUMETRIC-LETTERS" },
      commercial_totals: { currency: "EUR", total_gross: 100 },
      pricing: {},
      price: 100,
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

  it("returns null for legacy flat line items without currency (no invent)", () => {
    const raw = JSON.stringify([{ description: "Line", quantity: 1, total: 100 }]);
    expect(extractQuoteCurrencyFromLineItems(raw)).toBeNull();
  });

  it("returns null when snapshot has no currency fields", () => {
    const raw = JSON.stringify({
      product_definition: { template_code: "TPL-VOLUMETRIC-LETTERS" },
      pricing: {},
      price: 100,
    });
    expect(extractQuoteCurrencyFromLineItems(raw)).toBeNull();
  });
});

describe("formatQuoteMoney", () => {
  it("formats amount with currency code", () => {
    expect(formatQuoteMoney(768, "EUR")).toContain("768");
    expect(formatQuoteMoney(768, "EUR")).toContain("EUR");
    expect(formatQuoteMoney(768, "EUR")).not.toContain("RON");
  });
});

describe("formatCommercialAmount", () => {
  it("formats when currency is present", () => {
    expect(formatCommercialAmount(100, "EUR")).toContain("EUR");
    expect(formatCommercialAmount(100, "eur")).toContain("EUR");
  });

  it("marks unavailable currency instead of inventing RON/EUR", () => {
    expect(formatCommercialAmount(100, null)).toContain("monedă indisponibilă");
    expect(formatCommercialAmount(100, undefined)).toContain("monedă indisponibilă");
    expect(formatCommercialAmount(100, "")).toContain("monedă indisponibilă");
    expect(formatCommercialAmount(100, null)).not.toContain("RON");
    expect(formatCommercialAmount(null, "EUR")).toBe("—");
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
      label: "valori în monede diferite — total agregat indisponibil",
      mixed: true,
    });
  });
});

describe("formatQuoteListKpiAmount", () => {
  it("suppresses mixed-currency aggregates", () => {
    expect(
      formatQuoteListKpiAmount(1000, { mixed: true, label: "mixed" }, (n) => String(n)),
    ).toBe("—");
  });

  it("formats homogeneous currency totals", () => {
    expect(
      formatQuoteListKpiAmount(1000, { mixed: false, label: "EUR" }, (n) => `${n} EUR`),
    ).toBe("1000 EUR");
  });
});
