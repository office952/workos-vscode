# BUILD: Dev Owner User Seed for Mobile Readiness

## Purpose

Enable local Owner Employee Mobile readiness when `dev.db` has zero `users` rows and owner bootstrap returns `owner_user_not_found`.

## Context

Operational run on:

```text
DATABASE_URL=sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db
```

Results before this build:

- Alembic PASS through `s51_employee_manager_employee_id`
- `users` table empty
- Owner bootstrap dry-run: `owner_user_not_found`
- Readiness checker: `FAIL` with same issue

## Root cause

Owner bootstrap correctly requires an existing User row. Local dev DB had no OIDC login yet.

## Decision

Add a separate dev/local script to seed the owner User row. Do **not** auto-create users from owner bootstrap.

## Script

`backend/scripts/seed_dev_owner_user.py`

Service: `backend/services/dev_owner_user_seed_service.py`

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `WORKOS_DEV_OWNER_EMAIL` | `office@p-media.ro` | Dev owner email |
| `WORKOS_DEV_OWNER_NAME` | `Axinte Remus` | Display name |
| `WORKOS_DEV_OWNER_ROLE` | `admin` | RBAC role (must be in `VALID_ROLES`) |
| `WORKOS_DEV_OWNER_USER_ID` | `dev-owner-office-p-media-ro` | Dev user primary key |
| `WORKOS_DEV_OWNER_DRY_RUN` | `1` | `1` = no writes |

Uses `resolve_database_url()` for DB config (same as owner scripts).

## Dry-run behavior

- Action: `dry_run_would_create`
- No User row persisted
- Exit code 0 on success

## Idempotency

- Second real run with same email/id → `already_exists`
- Email exists with different id → `conflict`
- User id exists with different email → `conflict`

## Tests

`backend/tests/test_seed_dev_owner_user.py` — dry-run, create, idempotency, conflicts, role validation, no employee/attendance/request/payment side effects.

## Boundary confirmations

- No auth/OIDC/JWT rewrite
- No owner bootstrap logic change
- User seed does not create Employee
- No attendance, requests, or payroll rows
- No direct reports assignment
- No schema/migration change

## Commands

```powershell
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db"
$env:WORKOS_DEV_OWNER_DRY_RUN="1"
.\.venv\Scripts\python.exe scripts\seed_dev_owner_user.py
```
