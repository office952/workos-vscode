# WorkOS Actual-Cost Coverage V1 (F5)

**Stamp:** `PASS WITH WARNINGS`
**Branch:** `feat/actual-cost-coverage-v1`
**Base:** `c5e54eb3`

## Verdict language (binding)

```text
Representative closed-job profitability proof PASS (multi-job coverage fixtures)
Platform Profitability Complete = NOT READY
```

## What landed

1. Shared closed-job mutation guard (`closed_job_mutation_guard.py`) on:
   - `MaterialActualsService.record_issue|return|scrap`
   - `InventoryDeductionService.deduct_materials`
   - `InventoryStockAdjustmentService.reverse_movement` (when `order_id` present)
2. Cost-category applicability contract on profitability read model:
   - labor/material required
   - machine conditional (`not_applicable` | `applicable_optional` + unavailable)
   - other_direct `not_applicable` until classified facts exist
3. Expanded tests beyond single fixture `880041` → jobs `880051` / `880052`
4. No WC-rate / commercial / planned-duration machine inventing
5. No commercial snapshot mutation

## Warnings

- Machine actual capture + dated machine policy persistence not implemented (intentionally unavailable).
- Other-direct classified ledger not implemented (explicitly not_applicable).
- Legacy `reversal` path still lacks F4 valuation/`reverses_movement_id` — not treated as material actual.

## Tests

```text
tests/test_actual_cost_coverage_v1.py
tests/test_material_actuals_closed_job_v1.py
tests/test_profitability_actual_read_model.py
→ green with -W error::RuntimeWarning
```
