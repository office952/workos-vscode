# STEP2_SIBLING_REQUEST_TIMELINE_AFTER

Strategy: **D2**  
QA clone: `09cea6e2-41d3-44a3-a862-add13b01af84`

## Depth change (80↔100)

| Metric | Value |
|---|---:|
| SAVE_START | 110 |
| SAVE_ACK | 54 |
| PQ_START | 170 |
| PQ_END | 412 |
| OFFER_CURRENT_AT | 467 |
| LL_START | 415 |
| LL_END | 589 |
| CLICK_TO_CURRENT_MS | **412** |
| gap LL−PQ | **3 ms** |
| D2_OK (`PQ_END <= LL_START`) | **YES** |
| PRODUCTION_TASK_GET_COUNT | **0** |

## Face change (→ oracal_651)

| Metric | Value |
|---|---:|
| CLICK_TO_CURRENT_MS | **373** |
| PQ_MS | 219 |
| LL_MS | 168 |
| gap LL−PQ | **4 ms** |
| D2_OK | **YES** |

## Required relationship

```text
PQ_START < PQ_END <= OFFER_CURRENT ≈ LL_START
```

Satisfied. Logical-list no longer overlaps the pricedQuote offer-critical window.
