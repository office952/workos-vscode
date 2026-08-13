# D2_REVISION_AND_STALE_RESPONSE_TRACE

## Revision identity (reused, not invented)

| Signal | Source |
|---|---|
| `previewRefresh.pricedQuote` | Existing refetch counter |
| `previewRefresh.breakdown` | Existing refetch counter |
| `pricedQuoteSettleSignal` | Published in PQ `finally` with gens captured at request start |
| `logicalListFetchTokenRef` | Monotonic in-flight token for stale discard |
| `lastFetchedBreakdownGenRef` | Last successfully applied LL breakdown gen |

`localRevisionRef` remains save-coalescing authority; D2 pairs LL to **preview refresh generations** after PQ settle.

## Sequence

```text
PQ revision N completes (settle signal)
→ decide LL for breakdown gen N (skip if markup-only)
→ fetch token T
If breakdown becomes N+1 before apply:
→ shouldApplyLogicalListResponse = false → discard
```

## Tests

`frontend/src/lib/intakeV6/intakeV6LogicalListD2Schedule.test.ts` covers:

- initial fetch
- breakdown-advanced fetch
- markup-only skip
- superseded PQ gen skip
- stale token / breakdown discard
