# Regression evidence

```text
HEAD = 5daa3b86
APP_ENV = test
ENVIRONMENT = test
```

## Commands

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_controlled_employee_assignment.py `
  tests/test_finalization_wave6_assignment_command_hardening.py `
  tests/test_finalization_wave11_phase_b_reassignment.py `
  tests/test_finalization_wave11_phase_b_guard_closure.py `
  tests/test_execution_task_assignment.py `
  tests/test_finalization_wave5_assignment_readiness_audit.py `
  tests/test_employee_eligibility_read_model.py `
  tests/test_finalization_wave10_assignment_transition_schema.py `
  --ignore=tests/manual
```

## Result

```text
77 passed
```

MachineRun V1 not re-opened; assignment suites only. QA `backend/dev.db` plan 23 unchanged after suite (see `qa-baseline-after.json`).
