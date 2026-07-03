import { describe, expect, it } from "vitest";
import type { Quote } from "./mockData";
import { buildQuoteSummaryText, generateQuotePDF } from "./quotePdfGenerator";

const eurQuote: Quote = {
  id: "QT-EUR-001",
  intakeId: "",
  client: "Client EUR",
  contactPerson: "Test",
  assignedTo: "Op",
  status: "priced",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 640,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 640,
  vat: 128,
  grandTotal: 768,
  marginPct: 30,
  currency: "EUR",
  lineItems: [
    {
      description: "Litere volumetrice",
      productCode: "LV",
      quantity: 1,
      unitPrice: 640,
      unitCost: 500,
      total: 640,
    },
  ],
  notes: "",
};

describe("quotePdfGenerator currency", () => {
  it("buildQuoteSummaryText labels EUR totals, not RON", () => {
    const text = buildQuoteSummaryText(eurQuote);
    expect(text).toContain("EUR");
    expect(text).toContain("768");
    expect(text).not.toMatch(/768\s*RON/i);
    expect(text).not.toContain("lei");
  });

  it("generateQuotePDF succeeds for EUR quote (client fallback path)", () => {
    const { filename } = generateQuotePDF(eurQuote);
    expect(filename).toContain("QT-EUR-001");
  });
});
