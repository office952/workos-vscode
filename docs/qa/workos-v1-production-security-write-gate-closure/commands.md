# Commands

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='test'
$env:ENVIRONMENT='test'
$env:JWT_ALGORITHM='HS256'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_v1_production_security_write_gate.py `
  tests/test_employees_mobile_access_fields.py `
  tests/test_employee_internal_pay_base.py `
  tests/test_employee_payments_live.py `
  tests/test_dashboard_kpi_metrics.py `
  tests/test_operational_data_gaps.py `
  tests/test_pricing_registry.py `
  tests/test_cost_engine_config.py `
  --ignore=tests/manual
```

**Result:** `55 passed`

Security suite alone: `12 passed` (`test_v1_production_security_write_gate.py`).
