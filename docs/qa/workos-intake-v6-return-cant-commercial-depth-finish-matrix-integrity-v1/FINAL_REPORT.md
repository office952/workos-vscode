# FINAL_REPORT — RETURN-CANT Commercial Depth / Finish Matrix Integrity V1

## VERDICT: PASS

## Baseline chain

| Commit | Role |
|---|---|
| `2d495b60` | remote tip (pushed) |
| `fa3437a8` | depth fidelity / RAL / mixed groups (local) |
| *(this commit)* | Oracal labor authority closure (local, on top of `fa3437a8`) |

## Root defects repaired

1. `return_depth_mm` dropped in dry-run enrich / not forced onto quote_input.  
2. CPP collapsed mixed group cant depths to job-level.  
3. **Oracal cant labor incorrectly consumed F7F 3 EUR/m² wrap-area application** instead of dedicated `RETURN_CANT_VINYL_APPLICATION_LABOR` @ 1 EUR/ml perimeter.

## Not changed (by authority)

- Stock finish depth sell = intentional zero surcharge; forming flat 5 EUR/ml.  
- Face vinyl application remains F7F **3 EUR/m²** (`finisaje_aplicare_autocolant_fata`).  
- Oracal **material** rates unchanged (area-based).  
- RAL values unchanged; EUR minimum remains unpublished (F7H).  
- No new Pricing Registry **values** (existing 1 EUR/ml key wired).  
- No GET-diet / face-token / VAT / FX / commercial-input / confirm-gate changes.

## Plain answers

| Question | Answer |
|---|---|
| What is F7F? | Owner commercial-law package (2026-08-03); includes face vinyl application **3 EUR/m²** among other rates |
| Is F7F generic or RETURN-CANT specific? | **Generic / face-scoped** for the 3 EUR/m² application rate |
| Canonical RETURN-CANT Oracal labor authority? | **`RETURN_CANT_VINYL_APPLICATION_LABOR` @ 1 EUR/ml** |
| Does RETURN-CANT Oracal labor use 1 EUR/ml? | **YES** |
| Does Oracal material remain area-based? | **YES** |
| Does depth affect only Oracal material, not per-ml labor? | **YES** |
| Does 30/60/80/100 preserve correct commercial totals? | **YES** |
| Did RAL regress? | **NO** |
| Did GET-diet regress? | **NO** |
| Are mixed depths preserved per group? | **YES** |

```
PRICING_RULE_WIRING_CHANGES = 1 (cant Oracal labor → registry ml; face F7F untouched)
PRICING_REGISTRY_VALUE_CHANGES = 0
PRODUCT_TRUTH_SCHEMA_CHANGES = 0
DB_SCHEMA_CHANGES = 0
PUSH = NO
NEXT_TASK = NOT_AUTHORIZED
```
