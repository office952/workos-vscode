# WorkOS — Profitability Currency Policy A Wiring

**Date:** 2026-08-09  
**Starting HEAD:** `8821638c`  
**Owner decisions:**  
`PROFITABILITY_CURRENCY_POLICY = A`  
`AUTHORIZE_WORKOS_V1_PROFITABILITY_CURRENCY_POLICY_A_WIRING`

## Verdict

```text
WORKOS_V1_PROFITABILITY_CURRENCY_POLICY_A_WIRING = PASS
PROFITABILITY_CURRENCY_POLICY = A
PROFITABILITY_REPORTING_CURRENCY = EUR
FX_RATE_AUTHORITY = company_commercial_settings.eur_to_ron_rate SNAPSHOTTED at Order convert
FX_FREEZE_POINT = order_convert
FX_STORAGE = OrderSnapshotV2.profitability_fx_v1
HISTORICAL_FX_STABILITY = PROVEN (stamp immutable; live Settings ignored at P&L)
ORDER_SNAPSHOT_MUTATIONS = 0 (commercial totals unchanged; additive stamp only)
LABOR_COST_MUTATIONS = 0
MATERIAL_COST_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0 (additive JSON / Pydantic field)
QA_MUTATIONS = 0
MACHINE / OTHER = N_A_FOR_V1 preserved
PROFITABILITY_MONETARY_COMPOSITION_V1 = DONE_FOR_V1
NEXT_TASK = NOT_AUTHORIZED
NEXT_RECOMMENDED_BUILD = WORKOS_V1_BOUNDED_UI_HONESTY_CLOSURES
  (or WORKOS_V1_PRODUCTION_READINESS_SMOKE_PACK — roadmap order)
```

## Behavior

- Convert stamps `profitability_fx_v1` from Settings once.
- Profitability RM: same-currency path unchanged; EUR revenue + RON costs → divide aggregated RON known cost by stamp → compose in EUR.
- Missing stamp on EUR/RON job → fail-closed `profitability_fx_stamp_missing` (no invent FX).
- UI: contribution EUR + optional normalized cost + FX note.

## Tests

`test_profitability_monetary_composition_v1` · `test_profitability_currency_policy_a_wiring` · convert policy fields · regressions — green.
