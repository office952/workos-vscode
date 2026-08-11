# FINAL_REPORT — RETURN-CANT Commercial Depth / Finish Matrix Integrity V1

## VERDICT: PASS

## Baseline
`2d495b60` parity OK.

## Root defects repaired
1. `return_depth_mm` dropped in dry-run enrich / not forced onto quote_input.
2. CPP collapsed mixed group cant depths to job-level.

## Not changed (by authority)
- Stock finish depth sell = intentional zero surcharge; forming flat 5 EUR/ml.
- Oracal labor remains F7F 3 EUR/m² (not rewritten to registry 1 EUR/ml).
- RAL EUR minimum remains unpublished (F7H).
- No new Pricing Registry values.

## Plain answers

| Question | Answer |
|---|---|
| Does 30/60/80/100 reach CPP faithfully? | **YES** |
| Does Oracal material change with depth? | **YES** |
| Does Oracal labor stay constant per ml? | **NO** (F7F = 3 EUR/m² on wrap area; scales with depth) |
| Does RAL material use 2/2.5/3/4 EUR/ml? | **YES** |
| Does RAL labor use 1 EUR/ml? | **YES** |
| Does stock depth have intended commercial delta? | **INTENTIONAL_ZERO_DELTA** (finish); forming flat |
| Are mixed depths preserved per group? | **YES** |
| Does live offer change correctly? | **YES** (CPP/dry-run path) |
| Did GET-diet regress? | **NO** |

```
PRICING_RULE_CHANGES = 0 (consumption/wiring only)
PRICING_REGISTRY_VALUE_CHANGES = 0
PRODUCT_TRUTH_SCHEMA_CHANGES = 0
DB_SCHEMA_CHANGES = 0
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```
