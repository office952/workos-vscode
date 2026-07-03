import { describe, expect, it } from "vitest";
import type { Quote } from "@/lib/mockData";
import { getQuoteIntakeCommercialGuard } from "./quoteIntakeCommercialGuard";

const baseQuote: Quote = {
  id: "Q-1",
  client: "Test",
  contactPerson: "Ops",
  status: "draft",
  version: 1,
  intakeId: "IV3-ws-1",
  lineItems: [],
  subtotal: 0,
  discountPct: 0,
  totalBeforeVat: 0,
  vat: 21,
  grandTotal: 0,
  marginPct: 0,
  validUntil: "2026-12-31",
  notes: JSON.stringify({
    intake_v3_linkage_v1: {
      source_module: "intake_v3",
      requires_pricing_review: true,
    },
  }),
};

describe("quoteIntakeCommercialGuard", () => {
  it("requires pricing review for IV3 draft without completion", () => {
    const guard = getQuoteIntakeCommercialGuard(baseQuote);
    expect(guard.isGuardedQuote).toBe(true);
    expect(guard.requiresPricingReview).toBe(true);
    expect(guard.pricingReviewCompleted).toBe(false);
  });

  it("clears requires pricing review after completion in notes", () => {
    const quote: Quote = {
      ...baseQuote,
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed" },
        },
      }),
    };
    const guard = getQuoteIntakeCommercialGuard(quote);
    expect(guard.requiresPricingReview).toBe(false);
    expect(guard.pricingReviewCompleted).toBe(true);
    expect(guard.pricedDraft).toBe(true);
  });

  it("does not affect normal quotes", () => {
    const guard = getQuoteIntakeCommercialGuard({
      ...baseQuote,
      intakeId: "WI-123",
      notes: "{}",
    });
    expect(guard.isGuardedQuote).toBe(false);
    expect(guard.blockedMessage).toBeNull();
    expect(guard.acceptBlocked).toBe(false);
    expect(guard.convertBlocked).toBe(false);
  });

  it("blocks accept and convert for priced IV3 draft", () => {
    const quote: Quote = {
      ...baseQuote,
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed" },
        },
      }),
    };
    const guard = getQuoteIntakeCommercialGuard(quote);
    expect(guard.pricingReviewCompleted).toBe(true);
    expect(guard.guardedAcceptReady).toBe(true);
    expect(guard.guardedAcceptCompleted).toBe(false);
    expect(guard.acceptBlocked).toBe(true);
    expect(guard.convertBlocked).toBe(true);
  });

  it("marks IV3 accepted quote with convert guarded ready", () => {
    const quote: Quote = {
      ...baseQuote,
      status: "accepted",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed" },
          accept_decision: { status: "approved" },
        },
      }),
    };
    const guard = getQuoteIntakeCommercialGuard(quote);
    expect(guard.guardedAcceptCompleted).toBe(true);
    expect(guard.guardedAcceptReady).toBe(false);
    expect(guard.guardedConvertReady).toBe(true);
    expect(guard.orderCreated).toBe(false);
    expect(guard.convertBlocked).toBe(true);
  });

  it("marks IV3 converted quote with order created", () => {
    const quote: Quote = {
      ...baseQuote,
      status: "accepted",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed" },
          accept_decision: { status: "approved" },
          convert_decision: {
            status: "approved",
            order_created: true,
            order_id: 7001,
          },
        },
      }),
    };
    const guard = getQuoteIntakeCommercialGuard(quote);
    expect(guard.orderCreated).toBe(true);
    expect(guard.guardedConvertReady).toBe(false);
    expect(guard.blockedMessage).toMatch(/Production readiness audit/i);
  });
});