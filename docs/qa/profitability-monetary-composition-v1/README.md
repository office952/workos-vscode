# QA — Profitability Monetary Composition V1

**Verdict:** PARTIAL_BLOCKED (`currency_mismatch_no_fx` for EUR/RON Letters)  
**QA_MUTATIONS:** 0

## Commands

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_profitability_monetary_composition_v1.py `
  tests/test_f6_multi_type_actual_cost_pilot.py `
  tests/test_material_actuals_closed_job_v1.py `
  tests/test_profitability_actual_read_model.py `
  --ignore=tests/manual
```

**Result:** green (composition + N/A + currency fail-closed + regressions).

## UI

Route: `/execution/:orderId` (admin/manager) — Costs + Final result panels.  
Labels: Contribuție cunoscută V1; utilaj/alte = N/A pentru V1.
