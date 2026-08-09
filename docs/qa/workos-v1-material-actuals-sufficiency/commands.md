# Commands

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_v1_material_actuals_sufficiency.py `
  tests/test_material_actuals_closed_job_v1.py `
  tests/test_actual_cost_coverage_v1.py `
  tests/test_profitability_actual_read_model.py `
  tests/test_inventory_reversal_adjustment_contract.py `
  --ignore=tests/manual
```

**Results:** sufficiency `9 passed`; closed-job + coverage + RM + reversal regressions green (`13` + `12` in batched runs).
