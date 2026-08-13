# STEP2_SIBLING_REQUEST_TIMELINE_BEFORE

Baseline: `979d22d2`  
QA clone: `09cea6e2-41d3-44a3-a862-add13b01af84`  
Trigger: discrete return depth `80 → 100`  
Raw: `network/step2_fanout_before.json`

## Summary

| Metric | Value |
|---|---:|
| PUT_COUNT | 1 |
| GET_COUNT | 7 |
| PRICED_QUOTE_COUNT | 1 |
| LOGICAL_LIST_COUNT | 1 |
| MATERIAL_BREAKDOWN_COUNT | 1 |
| PRODUCTION_TASK_GET_COUNT | **0** |
| SAVE_ACK_MS | 82 |
| PQ_DURATION_MS | 1069 |
| LL_DURATION_MS | 1107 |
| PQ_START_MS == LL_START_MS | **1729** (concurrent) |

## Timeline (ms from click origin)

| REQUEST | START_MS | END_MS | DURATION_MS | STATUS | OVERLAP |
|---|---:|---:|---:|---:|---|
| PUT …/finish-setup | 1637 | 1720 | 82 | 200 | — |
| GET …/pricing-input-preview | 1729 | 1820 | 91 | 200 | overlaps_priced_quote |
| GET …/ai-informational-assist-candidate | 1729 | 1827 | 97 | 200 | overlaps_priced_quote |
| GET …/product-system-binding | 1728 | 1930 | 202 | 200 | overlaps_priced_quote |
| GET …/material-breakdown | 1729 | 1971 | 243 | 200 | overlaps_priced_quote |
| GET …/quote-handoff-preview | 1730 | 2076 | 347 | 200 | overlaps_priced_quote |
| GET …/priced-quote-dry-run | 1729 | 2798 | **1069** | 200 | self |
| GET …/logical-list-read-model | 1729 | 2836 | **1107** | 200 | overlaps_priced_quote |

## Initiator

All via `window.fetch` from Intake V6 ReviewStep refresh effects after save ack.

## Critical observation

Logical-list and pricedQuote start in the **same millisecond** after save. LL nests another full dry-run → SQLite/CPP contention on the offer-critical path.
