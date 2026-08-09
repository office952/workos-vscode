# Regression

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_controlled_session_command_safety.py `
  tests/test_controlled_task_sessions.py `
  tests/test_task_work_sessions.py `
  tests/test_execution_reality_capture.py `
  tests/test_execution_reality_workforce_capture.py `
  tests/test_finalization_wave11_phase_b_reassignment.py `
  tests/test_finalization_wave11_phase_b_guard_closure.py `
  tests/test_finalization_wave6_assignment_command_hardening.py `
  tests/test_controlled_employee_assignment.py `
  --ignore=tests/manual
```

```text
85 passed
```

QA `backend/dev.db` plan 23 unchanged (`qa-baseline-*.json`).
