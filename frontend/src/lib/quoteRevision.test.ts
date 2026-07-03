import { describe, expect, it } from "vitest";
import {
  buildLegacyRevisionPriceRequest,
  buildQuoteRevisionRequest,
  extractCanonicalSnapshotFromLineItems,
  extractQuoteRevisionSource,
  extractQuoteRevisionHistory,
  isQuoteRevisionEligible,
  LEGACY_REVISION_BLOCKED_MESSAGE,
  LEGACY_REVISION_RECOVERY_MESSAGE,
  MAX_QUOTE_DISCOUNT_PCT,
  QUOTE_REVISION_RESEND_NOTICE,
  QUOTE_REVISION_SUCCESS_MESSAGE,
  resolveQuoteRevisionSource,
  validateRevisionDiscountPct,
} from "./quoteRevision";
import type { Quote } from "./mockData";

const baseQuote: Quote = {
  id: "Q-REV-001",
  dbId: 99,
  intakeId: "WI-REV-001",
  client: "Client Rev",
  contactPerson: "Contact",
  assignedTo: "Op",
  status: "priced",
  version: 2,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 1000,
  discount: 50,
  discountPct: 5,
  totalBeforeVAT: 950,
  vat: 180.5,
  grandTotal: 1130.5,
  marginPct: 28,
  lineItems: [],
  notes: "",
};

describe("quoteRevision", () => {
  it("allows revision for eligible statuses", () => {
    expect(isQuoteRevisionEligible("draft")).toBe(true);
    expect(isQuoteRevisionEligible("priced")).toBe(true);
    expect(isQuoteRevisionEligible("sent")).toBe(true);
    expect(isQuoteRevisionEligible("viewed")).toBe(true);
    expect(isQuoteRevisionEligible("negotiating")).toBe(true);
  });

  it("blocks revision for terminal or accepted statuses", () => {
    expect(isQuoteRevisionEligible("accepted")).toBe(false);
    expect(isQuoteRevisionEligible("rejected")).toBe(false);
    expect(isQuoteRevisionEligible("expired")).toBe(false);
  });

  it("validates discount bounds", () => {
    expect(validateRevisionDiscountPct(-1)).toMatch(/negativ/i);
    expect(validateRevisionDiscountPct(MAX_QUOTE_DISCOUNT_PCT + 1)).toMatch(/maxim/i);
    expect(validateRevisionDiscountPct(10)).toBeNull();
  });

  it("extracts revision_source from line_items wrapper", () => {
    const raw = JSON.stringify({
      line_items: { status: "priced" },
      revision_source: {
        product_template: { id: 1 },
        user_config: { quantity: 1 },
        pricing: { margin_pct: 25, discount_pct: 5, vat_pct: 19 },
      },
    });
    const source = extractQuoteRevisionSource(raw);
    expect(source?.product_template).toEqual({ id: 1 });
    expect(source?.pricing?.discount_pct).toBe(5);
  });

  it("resolves embedded revision source", () => {
    const raw = JSON.stringify({
      revision_source: {
        product_template: { id: 2 },
        user_config: { quantity: 1 },
      },
    });
    const resolved = resolveQuoteRevisionSource(raw, baseQuote);
    expect(resolved.kind).toBe("embedded");
  });

  it("detects legacy candidate from canonical snapshot with template_id", () => {
    const raw = JSON.stringify({
      line_items: {
        template_id: 7,
        product_definition: { quantity: 1, dimensions: { width_mm: 100, height_mm: 200 } },
        pricing: { margin_pct: 25, discount_pct: 3, vat_pct: 19 },
        cost_result: { total_cost: 80 },
        price: { net: 100, gross: 119 },
      },
    });
    expect(extractCanonicalSnapshotFromLineItems(raw)?.template_id).toBe(7);
    const resolved = resolveQuoteRevisionSource(raw, baseQuote);
    expect(resolved.kind).toBe("legacy_candidate");
  });

  it("blocks legacy flat line_items without snapshot", () => {
    const raw = JSON.stringify([{ description: "Linie", quantity: 1 }]);
    const resolved = resolveQuoteRevisionSource(raw, baseQuote);
    expect(resolved.kind).toBe("blocked");
    if (resolved.kind === "blocked") {
      expect(resolved.message).toBe(LEGACY_REVISION_BLOCKED_MESSAGE);
      expect(resolved.recoveryMessage).toBe(LEGACY_REVISION_RECOVERY_MESSAGE);
    }
  });

  it("accepts IV6 linkage in notes as a legacy repricing candidate", () => {
    const raw = JSON.stringify([{ description: "Linie", quantity: 1 }]);
    const notes = JSON.stringify({
      intake_v6_linkage_v1: {
        source_workspace_id: "41401270-7151-419c-b520-dec258409593",
        quote_input_payload: { width_mm: 5000, height_mm: 600 },
      },
    });
    const resolved = resolveQuoteRevisionSource(raw, baseQuote, notes);
    expect(resolved.kind).toBe("legacy_candidate");
    if (resolved.kind === "legacy_candidate") {
      expect(resolved.pricing?.margin_pct).toBe(baseQuote.marginPct);
      expect(resolved.pricing?.discount_pct).toBe(baseQuote.discountPct);
    }
  });

  it("builds legacy pricing-only revision request", () => {
    const body = buildLegacyRevisionPriceRequest(baseQuote, { margin_pct: 28, vat_pct: 19 }, 12, {
      intakeDbId: 42,
    });
    expect(body.pricing?.discount_pct).toBe(12);
    expect(body.intake_id).toBe(42);
    expect(body.product_template).toBeUndefined();
  });

  it("builds embedded revision request with new discount only", () => {
    const source = {
      product_template: { id: 1, template_code: "TPL" },
      user_config: { quantity: 2 },
      quote_input: { text: "ABC" },
      pricing: { margin_pct: 30, discount_pct: 5, vat_pct: 19 },
    };
    const body = buildQuoteRevisionRequest(baseQuote, source, 12);
    expect(body?.pricing?.discount_pct).toBe(12);
    expect(body?.pricing?.margin_pct).toBe(30);
    expect(body?.client_name).toBe("Client Rev");
  });

  it("success and resend copy are explicit", () => {
    expect(QUOTE_REVISION_SUCCESS_MESSAGE).toMatch(/retrimis/i);
    expect(QUOTE_REVISION_RESEND_NOTICE).toMatch(/retrimis/i);
  });

  it("extracts revision history from line_items wrapper", () => {
    const archivedSnapshot = JSON.stringify({
      line_items: {
        pricing: { discount_pct: 5, margin_pct: 25, vat_pct: 19 },
        price: { net: 950, gross: 1130.5 },
      },
    });
    const raw = JSON.stringify({
      revision_history: [
        {
          version: 1,
          archived_at: "2026-06-02T12:00:00Z",
          line_items: archivedSnapshot,
        },
      ],
    });
    const history = extractQuoteRevisionHistory(raw);
    expect(history).toHaveLength(1);
    expect(history[0].version).toBe(1);
    expect(history[0].discountPct).toBe(5);
    expect(history[0].grandTotal).toBe(1130.5);
  });
});
