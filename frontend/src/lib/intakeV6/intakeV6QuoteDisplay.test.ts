import { describe, expect, it } from "vitest";
import {
  formatV6QuoteTotalLabel,
  isIntakeV6Quote,
  isUnpricedIntakeV6Quote,
} from "./intakeV6QuoteDisplay";
import type { Quote } from "@/lib/mockData";

const baseQuote: Quote = {
  id: "Q-V6-IV6-BB8EE3F8-1782910533",
  dbId: 6,
  intakeId: "IV6-c8dda47f-e2a7-4fea-800c-2dc01b2be5a3",
  status: "draft",
  grandTotal: 0,
  subtotal: 0,
  totalBeforeVAT: 0,
  vat: 0,
  client: "Client Test",
  contactPerson: "Operator",
  lineItems: [],
  marginPct: 0,
  discountPct: 0,
  discount: 0,
  version: 1,
  validUntil: "2026-08-01",
  currency: "RON",
  createdAt: "2026-07-01",
  notes: "",
};

describe("intakeV6QuoteDisplay", () => {
  it("detects intake v6 quotes by intake code or quote code", () => {
    expect(isIntakeV6Quote(baseQuote)).toBe(true);
    expect(
      isIntakeV6Quote({
        ...baseQuote,
        intakeId: "",
        id: "Q-V6-IV6-00000000-0000-4000-8000-000000000001",
      }),
    ).toBe(true);
    expect(isIntakeV6Quote({ ...baseQuote, intakeId: "IV3-abc", id: "Q-123" })).toBe(false);
  });

  it("marks draft zero-total v6 quotes as unpriced", () => {
    expect(isUnpricedIntakeV6Quote(baseQuote)).toBe(true);
    expect(isUnpricedIntakeV6Quote({ ...baseQuote, grandTotal: 100 })).toBe(false);
    expect(isUnpricedIntakeV6Quote({ ...baseQuote, status: "priced" })).toBe(false);
  });

  it("formats unpriced totals with operator-facing label", () => {
    expect(formatV6QuoteTotalLabel(baseQuote, "0,00 RON")).toBe("Nepretuit (draft V6)");
    expect(formatV6QuoteTotalLabel({ ...baseQuote, grandTotal: 100 }, "100,00 RON")).toBe(
      "100,00 RON",
    );
  });
});
