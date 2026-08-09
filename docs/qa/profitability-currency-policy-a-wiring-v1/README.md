# QA — Profitability Currency Policy A Wiring

**Verdict:** PASS  
**QA_MUTATIONS:** 0

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_profitability_monetary_composition_v1.py `
  tests/test_profitability_currency_policy_a_wiring.py `
  tests/test_order_snapshot_v2_convert.py::test_order_snapshot_v2_json_policy_fields `
  tests/test_f6_multi_type_actual_cost_pilot.py `
  tests/test_profitability_actual_read_model.py `
  --ignore=tests/manual
```

**Result:** green (Policy A stamp + composition + historical stability).
