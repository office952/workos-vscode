import { describe, expect, it } from "vitest";
import {
  decideLogicalListFetchAfterPricedQuoteSettle,
  shouldApplyLogicalListResponse,
} from "./intakeV6LogicalListD2Schedule";

describe("decideLogicalListFetchAfterPricedQuoteSettle", () => {
  it("fetches on initial pricedQuote settle", () => {
    const decision = decideLogicalListFetchAfterPricedQuoteSettle({
      analysisReady: true,
      settle: { pricedQuoteGen: 0, breakdownGen: 0 },
      currentPricedQuoteGen: 0,
      currentBreakdownGen: 0,
      lastFetchedBreakdownGen: null,
    });
    expect(decision.shouldFetch).toBe(true);
    expect(decision.reason).toBe("initial_or_breakdown");
  });

  it("does not require a prior settle — null settle stays not_ready until PQ finally", () => {
    const decision = decideLogicalListFetchAfterPricedQuoteSettle({
      analysisReady: true,
      settle: null,
      currentPricedQuoteGen: 0,
      currentBreakdownGen: 0,
      lastFetchedBreakdownGen: null,
    });
    expect(decision.shouldFetch).toBe(false);
    expect(decision.reason).toBe("not_ready");
  });

  it("new/empty workspace initial gen 0/0 is not classified as markup_only_skip", () => {
    const decision = decideLogicalListFetchAfterPricedQuoteSettle({
      analysisReady: true,
      settle: { pricedQuoteGen: 0, breakdownGen: 0 },
      currentPricedQuoteGen: 0,
      currentBreakdownGen: 0,
      lastFetchedBreakdownGen: null,
    });
    expect(decision.reason).not.toBe("markup_only_skip");
    expect(decision.shouldFetch).toBe(true);
  });

  it("fetches when breakdown advanced after finish save wave", () => {
    const decision = decideLogicalListFetchAfterPricedQuoteSettle({
      analysisReady: true,
      settle: { pricedQuoteGen: 2, breakdownGen: 2 },
      currentPricedQuoteGen: 2,
      currentBreakdownGen: 2,
      lastFetchedBreakdownGen: 1,
    });
    expect(decision.shouldFetch).toBe(true);
  });

  it("skips markup-only pricedQuote settle when breakdown unchanged", () => {
    const decision = decideLogicalListFetchAfterPricedQuoteSettle({
      analysisReady: true,
      settle: { pricedQuoteGen: 5, breakdownGen: 2 },
      currentPricedQuoteGen: 5,
      currentBreakdownGen: 2,
      lastFetchedBreakdownGen: 2,
    });
    expect(decision.shouldFetch).toBe(false);
    expect(decision.reason).toBe("markup_only_skip");
  });

  it("does not fetch when settle is for a superseded pricedQuote gen", () => {
    const decision = decideLogicalListFetchAfterPricedQuoteSettle({
      analysisReady: true,
      settle: { pricedQuoteGen: 1, breakdownGen: 1 },
      currentPricedQuoteGen: 2,
      currentBreakdownGen: 2,
      lastFetchedBreakdownGen: 0,
    });
    expect(decision.shouldFetch).toBe(false);
    expect(decision.reason).toBe("pq_not_current");
  });
});

describe("shouldApplyLogicalListResponse", () => {
  it("applies only matching token and breakdown generation", () => {
    expect(
      shouldApplyLogicalListResponse({
        responseFetchToken: 3,
        latestFetchToken: 3,
        responseBreakdownGen: 2,
        currentBreakdownGen: 2,
      }),
    ).toBe(true);
  });

  it("discards stale token after newer edit", () => {
    expect(
      shouldApplyLogicalListResponse({
        responseFetchToken: 3,
        latestFetchToken: 4,
        responseBreakdownGen: 2,
        currentBreakdownGen: 3,
      }),
    ).toBe(false);
  });

  it("discards when breakdown moved ahead", () => {
    expect(
      shouldApplyLogicalListResponse({
        responseFetchToken: 4,
        latestFetchToken: 4,
        responseBreakdownGen: 2,
        currentBreakdownGen: 3,
      }),
    ).toBe(false);
  });
});
