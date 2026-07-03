import { describe, expect, it } from "vitest";
import {
  getQuoteCommercialActionVisibility,
  getQuoteCommercialGuidance,
  QUOTE_REVISION_MECHANISM_NOTICE,
} from "./quoteCommercialGuidance";
import type { Quote } from "./mockData";

const baseQuote: Quote = {
  id: "Q-TEST-001",
  dbId: 1,
  intakeId: "",
  client: "Test Client",
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

describe("quoteCommercialGuidance", () => {
  it("returns priced guidance with send next step", () => {
    const g = getQuoteCommercialGuidance("priced");
    expect(g.description).toMatch(/calculată/i);
    expect(g.nextAction).toMatch(/trimite/i);
  });

  it("returns sent guidance mentioning re-send after revision", () => {
    const g = getQuoteCommercialGuidance("sent");
    expect(g.description).toMatch(/retrimite/i);
  });

  it("returns rejected guidance without convert implication", () => {
    const g = getQuoteCommercialGuidance("rejected");
    expect(g.description).toMatch(/respinsă/i);
    expect(g.nextAction).toMatch(/terminal/i);
  });

  it("shows send, convert and revision for priced quote", () => {
    const v = getQuoteCommercialActionVisibility(baseQuote);
    expect(v.showAssistedSend).toBe(true);
    expect(v.showConvert).toBe(true);
    expect(v.showRevision).toBe(true);
    expect(v.showAccept).toBe(false);
    expect(v.showExpire).toBe(false);
  });

  it("shows accept/reject/expire and revision for sent quote", () => {
    const v = getQuoteCommercialActionVisibility({
      ...baseQuote,
      status: "sent",
    });
    expect(v.showAccept).toBe(true);
    expect(v.showReject).toBe(true);
    expect(v.showExpire).toBe(true);
    expect(v.showRevision).toBe(true);
    expect(v.showConvert).toBe(false);
  });

  it("hides revision for accepted quote", () => {
    expect(
      getQuoteCommercialActionVisibility({ ...baseQuote, status: "accepted" })
        .showRevision
    ).toBe(false);
  });

  it("shows convert only for accepted (not rejected)", () => {
    expect(
      getQuoteCommercialActionVisibility({ ...baseQuote, status: "accepted" })
        .showConvert
    ).toBe(true);
    expect(
      getQuoteCommercialActionVisibility({ ...baseQuote, status: "rejected" })
        .showConvert
    ).toBe(false);
  });

  it("includes revision mechanism notice constant", () => {
    expect(QUOTE_REVISION_MECHANISM_NOTICE).toMatch(/recalculează/i);
    expect(QUOTE_REVISION_MECHANISM_NOTICE).toMatch(/Totalurile/i);
  });

  it("blocks accept and convert for Intake V3 quotes requiring pricing review", () => {
    const iv3Quote: Quote = {
      ...baseQuote,
      status: "priced",
      intakeId: "IV3-ws-test",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          source_module: "intake_v3",
          requires_pricing_review: true,
        },
      }),
    };
    const v = getQuoteCommercialActionVisibility(iv3Quote);
    expect(v.showAccept).toBe(false);
    expect(v.showConvert).toBe(false);
    expect(v.showAssistedSend).toBe(false);
    expect(v.convertBlockedMessage).toMatch(/pricing review/i);
  });

  it("does not block normal priced quote without IV3 linkage", () => {
    const v = getQuoteCommercialActionVisibility(baseQuote);
    expect(v.showConvert).toBe(true);
    expect(v.convertBlockedMessage).toBeNull();
  });

  it("still blocks accept and convert for Intake V3 after pricing review completed", () => {
    const iv3PricedDraft: Quote = {
      ...baseQuote,
      status: "draft",
      intakeId: "IV3-ws-test",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          source_module: "intake_v3",
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed", method: "manual_review" },
        },
      }),
    };
    const v = getQuoteCommercialActionVisibility(iv3PricedDraft);
    expect(v.showAccept).toBe(false);
    expect(v.showConvert).toBe(false);
    expect(v.showAssistedSend).toBe(false);
    expect(v.convertBlockedMessage).toMatch(/guarded IV3 conversion/i);

    const guidance = getQuoteCommercialGuidance("draft", iv3PricedDraft);
    expect(guidance.description).toMatch(/Pricing review completed/i);
    expect(guidance.nextAction).toMatch(/Intake V3 guarded accept/i);
  });

  it("IV3 accepted guidance points to guarded convert flow", () => {
    const iv3Accepted: Quote = {
      ...baseQuote,
      status: "accepted",
      intakeId: "IV3-ws-test",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed" },
          accept_decision: { status: "approved" },
        },
      }),
    };
    const guidance = getQuoteCommercialGuidance("accepted", iv3Accepted);
    expect(guidance.description).toMatch(/accepted/i);
    expect(guidance.nextAction).toMatch(/guarded convert/i);
  });

  it("IV3 converted guidance points to production readiness audit", () => {
    const iv3Converted: Quote = {
      ...baseQuote,
      status: "accepted",
      intakeId: "IV3-ws-test",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: false,
          priced_draft: true,
          pricing_review: { status: "completed" },
          accept_decision: { status: "approved" },
          convert_decision: { status: "approved", order_created: true, order_id: 7001 },
        },
      }),
    };
    const guidance = getQuoteCommercialGuidance("accepted", iv3Converted);
    expect(guidance.description).toMatch(/Production readiness audit/i);
    expect(guidance.description).toMatch(/material breakdown/i);
    expect(guidance.nextAction).toMatch(/production readiness audit/i);
  });

  it("IV3 unpriced guidance says pricing review required", () => {
    const iv3Quote: Quote = {
      ...baseQuote,
      status: "draft",
      intakeId: "IV3-ws-test",
      notes: JSON.stringify({
        intake_v3_linkage_v1: {
          requires_pricing_review: true,
        },
      }),
    };
    const guidance = getQuoteCommercialGuidance("draft", iv3Quote);
    expect(guidance.description).toMatch(/Pricing review is required/i);
  });

  it("normal quote guidance unchanged without quote context", () => {
    const guidance = getQuoteCommercialGuidance("priced");
    expect(guidance.title).toMatch(/calculată/i);
  });
});
