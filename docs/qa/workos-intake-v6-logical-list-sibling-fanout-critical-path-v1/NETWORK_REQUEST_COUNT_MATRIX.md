# NETWORK_REQUEST_COUNT_MATRIX

| Scenario | PUT | PQ | LL | MB | PRODUCTION/TASK |
|---|---:|---:|---:|---:|---:|
| Depth change (after D2) | 1 | 1 | 1 | 1 | 0 |
| Face → 651 (after D2) | 1 | 1 | 1 | 1 | 0 |
| Markup-only (unit decision) | 1* | 1* | **0** | 0 | 0 |

\* Markup path covered by `decideLogicalListFetchAfterPricedQuoteSettle` unit test (`markup_only_skip`). Live CDP commercial debounce was not reliably triggered; scheduling logic is unit-proven.

Expected: `PUT≈1`, `PQ=1`, `LL<=1` when LL-relevant, `PRODUCTION_TASK=0`.
