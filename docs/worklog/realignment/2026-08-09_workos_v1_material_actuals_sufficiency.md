# WorkOS V1 — Material Actuals Sufficiency

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_WORKOS_V1_MATERIAL_ACTUALS_SUFFICIENCY`  
**Starting HEAD:** `66bb2d88`  
**Verdict:** `PASS`

```text
MATERIAL_ACTUALS_V1 = DONE_FOR_V1
PROFITABILITY_ACTUAL_MATERIAL_COST_READINESS = READY
HISTORICAL_MATERIAL_COST_STABILITY = PROVEN
HISTORICAL_MATERIAL_QUANTITY_STABILITY = PROVEN
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
```

## What was true already

Canonical ISSUE/RETURN/SCRAP writers freeze valuation on `StockMovement`.  
Profitability Actual RM already consumed `material_actual_basis` (frozen).  
Planned BOM / reservation rejected at write.

## Bounded closure in this GO

1. Shared `compute_material_actuals` with line projection + legacy `reversal` exclusion.  
2. Legacy stock reverse copies freeze snapshots + `reverses_movement_id`.  
3. `build_profitability_actual_material_input` (labor-input twin) embedded in Profitability RM.  
4. Controlled scenarios + regressions.

## Next

```text
NEXT_RECOMMENDED_BUILD = PROFITABILITY_MONETARY_COMPOSITION_V1
MACHINE_COST_V1_DECISION_REQUIRED = YES
OTHER_ACTUAL_COST_V1_GAP = other_direct_not_declared (fail-closed N/A pattern exists)
```

Do **not** start an Inventory program. Proceed to monetary composition once Owner resolves machine/other N/A vs required.
