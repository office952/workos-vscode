# D2_INITIAL_BOOTSTRAP_TRACE

## Initial mount (gen 0/0, new/empty or configured)

| Question | Answer |
|----------|--------|
| Does pricedQuote initial GET start? | **YES** (when `analysisReady`) |
| Does its finally publish a settle signal? | **YES** (when not cancelled) |
| Can settle be skipped because no refresh generation changed? | **NO** — gen 0 settle is published |
| Can LL wait forever for a signal that never occurs? | **YES previously** if PQ always cancelled by `updated_at` identity thrash; **mitigated** by dropping `updated_at` from identity + reset-before-PQ |
| Can LL/PQ state prevent ReviewStep render? | **NO** — blank was unrelated render throw |
| Can markup_only_skip classify initial load as skip? | **NO** (`lastFetchedBreakdownGen === null` → `initial_or_breakdown`) |

## Scheduler after fix

1. Identity reset effect (refs + clear settle) — **before** PQ.
2. PQ effect clears settle at start, fetches, publishes settle in `finally` (incl. gen 0/0).
3. LL effect uses `decideLogicalListFetchAfterPricedQuoteSettle`.

D2 is not the blank-screen root cause; bootstrap coherence still repaired.
