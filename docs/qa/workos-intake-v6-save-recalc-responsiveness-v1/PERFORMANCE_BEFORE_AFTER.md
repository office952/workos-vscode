# PERFORMANCE_BEFORE_AFTER

## BEFORE (code authority)

| Metric | Discrete selector |
|---|---|
| SELECT_TO_SAVE_START | **≥700 ms** floor (short) or **≥1400 ms** if long latch |
| Operator feedback | Coarse pending banner only; no pricedQuote loading flag |

## AFTER (QA clone runtime)

Workspace clone: `09cea6e2-…` (`IV6-7EF4715C`) · `OWNER_DEV_DB_MUTATIONS = 0`

| Case | SELECT_TO_SAVE_START_MS | SAVE_ACK_MS | PRICED_QUOTE_MS | TOTAL_CLICK_TO_CURRENT_PRICE_MS |
|---|---:|---:|---:|---:|
| Face → 651 | **125** | 249 | 1535 | 1923 |
| Face → 641 | **125** | 74 | 1877 | 2089 |

## Interpretation

- Discrete save start meets **&lt;200 ms** target (100 ms policy + small React overhead).
- End-to-end live price refresh is **~1.9–2.1 s** on this local runtime — dominated by **priced-quote-dry-run (~1.5–1.9 s)**, not the removed 700 ms debounce.
- Warning threshold (&gt;1.5 s total) is reported honestly; material improvement is the removed selector floor + immediate lifecycle feedback.

Source: `network/discrete_selector_timings.json`