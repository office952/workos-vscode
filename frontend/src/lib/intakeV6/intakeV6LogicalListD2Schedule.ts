/**
 * D2 scheduling: logical-list refresh follows pricedQuote settle for the same
 * preview-refresh generation. Does not invent a second revision authority —
 * uses existing previewRefresh.breakdown / pricedQuote counters.
 */

export type IntakeV6LogicalListD2SettleSignal = {
  /** previewRefresh.pricedQuote at the start of the settled PQ request */
  pricedQuoteGen: number;
  /** previewRefresh.breakdown at the start of that same PQ request wave */
  breakdownGen: number;
};

export type IntakeV6LogicalListD2FetchDecision = {
  shouldFetch: boolean;
  /** Breakdown generation the in-flight LL response must match to apply */
  expectedBreakdownGen: number;
  reason:
    | "not_ready"
    | "pq_not_current"
    | "markup_only_skip"
    | "initial_or_breakdown"
    | "already_fetched_breakdown";
};

/**
 * After a pricedQuote request settles, decide whether to launch logical-list.
 *
 * - Wait until the settle signal matches the latest pricedQuote generation.
 * - Fetch on first load or when breakdown generation advanced (finish/material).
 * - Skip when only pricedQuote advanced (commercial_preview markup/discount/manual).
 */
export function decideLogicalListFetchAfterPricedQuoteSettle(args: {
  analysisReady: boolean;
  settle: IntakeV6LogicalListD2SettleSignal | null;
  currentPricedQuoteGen: number;
  currentBreakdownGen: number;
  /** null = never successfully applied an LL for this workspace/analysis identity */
  lastFetchedBreakdownGen: number | null;
}): IntakeV6LogicalListD2FetchDecision {
  const expectedBreakdownGen = args.currentBreakdownGen;
  if (!args.analysisReady || args.settle == null) {
    return { shouldFetch: false, expectedBreakdownGen, reason: "not_ready" };
  }
  if (args.settle.pricedQuoteGen !== args.currentPricedQuoteGen) {
    return { shouldFetch: false, expectedBreakdownGen, reason: "pq_not_current" };
  }
  // Prefer current breakdown (may have advanced if a newer edit landed mid-flight).
  // Settle's breakdownGen is informational for same-wave pairing.
  if (
    args.lastFetchedBreakdownGen !== null &&
    args.lastFetchedBreakdownGen === args.currentBreakdownGen
  ) {
    // pricedQuote-only wave (e.g. markup) — LL MB rows unchanged.
    if (args.settle.breakdownGen === args.currentBreakdownGen) {
      return { shouldFetch: false, expectedBreakdownGen, reason: "markup_only_skip" };
    }
    return { shouldFetch: false, expectedBreakdownGen, reason: "already_fetched_breakdown" };
  }
  return {
    shouldFetch: true,
    expectedBreakdownGen,
    reason: "initial_or_breakdown",
  };
}

/** Discard LL responses that are not the latest in-flight token / breakdown gen. */
export function shouldApplyLogicalListResponse(args: {
  responseFetchToken: number;
  latestFetchToken: number;
  responseBreakdownGen: number;
  currentBreakdownGen: number;
}): boolean {
  return (
    args.responseFetchToken === args.latestFetchToken &&
    args.responseBreakdownGen === args.currentBreakdownGen
  );
}
