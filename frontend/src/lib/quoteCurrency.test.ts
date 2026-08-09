import { describe, expect, it } from "vitest";
import {
  extractQuoteCurrency,
  extractQuoteCurrencyFromLineItems,
  extractQuoteCurrencyFromNotes,
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

describe("extractQuoteCurrencyFromNotes", () => {
  it("returns EUR from commercial_adjustment_trace", () => {
    const raw = JSON.stringify({
      commercial_adjustment_trace: { currency: "EUR", markup_percent: 0 },
    });
    expect(extractQuoteCurrencyFromNotes(raw)).toBe("EUR");
  });

  it("returns null when notes lack currency provenance", () => {
    expect(extractQuoteCurrencyFromNotes(JSON.stringify({ human_summary: "x" }))).toBeNull();
  });
});

describe("extractQuoteCurrency", () => {
  it("prefers line_items then falls back to notes", () => {
    expect(
      extractQuoteCurrency(
        JSON.stringify([{ description: "Line", total: 1 }]),
        JSON.stringify({ commercial_adjustment_trace: { currency: "EUR" } }),
      ),
    ).toBe("EUR");
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

  it("uses neutral em dash when currency missing — no invent, no technical jargon", () => {
    expect(formatCommercialAmount(100, null)).toBe("—");
    expect(formatCommercialAmount(100, undefined)).toBe("—");
    expect(formatCommercialAmount(100, "")).toBe("—");
    expect(formatCommercialAmount(100, null)).not.toContain("RON");
    expect(formatCommercialAmount(100, null)).not.toContain("EUR");
    expect(formatCommercialAmount(100, null)).not.toMatch(/monedă|currency|indisponibil/i);
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

  it("uses neutral em dash when no quote has proven currency", () => {
    expect(quoteCurrencyLabel([{ currency: null }, { currency: undefined }])).toEqual({
      label: "—",
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
