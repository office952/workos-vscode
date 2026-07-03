# BUILD: Owner Readiness DB Config Fix

## Purpose

Fix operational CLI failures when running owner readiness scripts and Alembic without `DATABASE_URL` in the shell.

## Observed errors

```text
sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from given URL string
```

```text
Failed to lazy initialize database: 'Settings' object has no attribute 'database_url'
AttributeError: 'Settings' object has no attribute 'database_url'
```

## Root cause

1. `Settings` has no explicit `database_url` field; dynamic `__getattr__` raises `AttributeError` when `DATABASE_URL` is absent.
2. `database.py` used `settings.database_url` in a truthiness check, triggering that AttributeError instead of a clear missing-env message.
3. `alembic/env.py` fell back to empty `sqlalchemy.url` from `alembic.ini` when `DATABASE_URL` was unset.
4. Owner CLI scripts did not load `backend/.env`; pytest passed because `conftest.py` sets `DATABASE_URL`.

## Fix applied

- Added `load_backend_env()` and `resolve_database_url()` in `core/config.py`.
- `DatabaseManager.init_db()` uses `resolve_database_url()` instead of `settings.database_url`.
- `alembic/env.py` uses the same resolver and async URL normalization.
- Owner scripts validate DB config in `main()` before `ensure_initialized()`.

## Commands (local)

### Alembic

```powershell
cd C:\Users\offic\workos\backend
# DATABASE_URL from backend/.env or shell:
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### Bootstrap dry-run

```powershell
cd C:\Users\offic\workos\backend
$env:WORKOS_OWNER_EMAIL='<owner-email>'
$env:WORKOS_OWNER_EMPLOYEE_NAME='Axinte Remus'
$env:WORKOS_OWNER_EMPLOYEE_DEPARTMENT='Management'
$env:WORKOS_OWNER_EMPLOYEE_TITLE='Owner'
$env:WORKOS_OWNER_BOOTSTRAP_DRY_RUN='1'
.\.venv\Scripts\python.exe scripts\bootstrap_owner_employee.py
```

## Required env vars

| Variable | Required for |
|----------|----------------|
| `DATABASE_URL` | All owner scripts, Alembic, backend DB init |
| `WORKOS_OWNER_EMAIL` or `WORKOS_OWNER_USER_ID` | Bootstrap / readiness / assign |
| `WORKOS_OWNER_EMPLOYEE_NAME` | Bootstrap / readiness |
| `WORKOS_OWNER_BOOTSTRAP_DRY_RUN` | Bootstrap dry-run (`1`) vs real (`0`) |
| `WORKOS_DIRECT_REPORT_*` | Assign direct reports script |

Optional dev vars: `APP_ENV`, `ENVIRONMENT`, `JWT_SECRET_KEY` (backend server; not required for bootstrap DB connection alone).

## If DATABASE_URL is missing

1. Copy `backend/.env.example` to `backend/.env`, or
2. Export `DATABASE_URL` in PowerShell before running scripts, or
3. Use `npm run dev:backend` pattern from repo root (helper injects URL).

Scripts print a multi-line `ValueError` message — not an AttributeError.

## Boundary

- No auth, permission model, attendance CRUD, payroll, CostEngine, Quote/Pricing/ProductSystem changes.
- No schema/migration changes.
- No business logic changes in owner bootstrap or direct-reports services.

## Files changed

- `backend/core/config.py`
- `backend/core/database.py`
- `backend/alembic/env.py`
- `backend/scripts/bootstrap_owner_employee.py`
- `backend/scripts/assign_owner_direct_reports.py`
- `backend/scripts/check_employee_mobile_readiness.py`
- `backend/tests/test_owner_employee_bootstrap.py`
- `backend/tests/test_employee_direct_reports_assignment.py`
- `docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md`

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_owner_employee_bootstrap.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_direct_reports_assignment.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_manager_team_workspace.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_request_review.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py -v
```

## Result

PASS — owner scripts and Alembic align with real DB config resolution path.
