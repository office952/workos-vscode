# BUILD: Dev Auth Impersonation for Employee Mobile

## Purpose

Enable local Employee Mobile testing as specific DB users (admin, owner seed, employee_mobile) without OIDC/JWT manual setup.

## Problem

Dev auth bypass always returned `dev-admin-user-00000000`. Seeded users like `dev-employee-test-001` could not be exercised in browser/API live.

## Decision

Development-only `WORKOS_DEV_AUTH_USER_ID` env var → read user from `users` table when dev bypass is active.

See `docs/architecture/DEV_AUTH_IMPERSONATION_DECISION.md`.

## Security guard

- `resolve_dev_auth_impersonation_user_id()` returns `None` unless `dev_auth_allowed()` (local/development/test).
- Staging/production: no dev bypass token without credentials; env var ignored.

## Env vars

| Variable | Purpose |
|----------|---------|
| `WORKOS_DEV_AUTH_USER_ID` | User primary key to impersonate in dev bypass |
| (unset) | Fallback synthetic Dev Admin |

## Files changed

- `backend/core/config.py`
- `backend/dependencies/auth.py`
- `backend/tests/test_auth_dev_impersonation.py`
- `docs/architecture/DEV_AUTH_IMPERSONATION_DECISION.md`
- `docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md`

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_auth_dev_impersonation.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_manager_team_workspace.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_request_review.py -v
```

## Manual smoke

```powershell
$env:DATABASE_URL="sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db"
$env:WORKOS_DEV_AUTH_USER_ID="dev-employee-test-001"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/requests
```

## Confirmations

- Dev-only
- No production impersonation
- No user creation by impersonation
- No employee creation by impersonation
- No auth/OIDC rewrite
- No permission model relaxation
- No business logic changes in employee mobile/review/attendance
