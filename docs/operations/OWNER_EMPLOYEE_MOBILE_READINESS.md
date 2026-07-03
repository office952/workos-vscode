# Owner Employee Mobile Readiness — Operations Guide

Complete step-by-step preparation for real Employee Mobile testing on phone.

## Prerequisites

- `DATABASE_URL`, `APP_ENV`, `JWT_SECRET_KEY` set (see `AGENTS.md`).
- Owner user exists in `users` (first OIDC login or dev auth).
- Placeholder env values below — **do not commit real emails**.

### Database URL (required)

Owner readiness scripts and Alembic read **`DATABASE_URL`** via `core.config.resolve_database_url()`:

1. Loads `backend/.env` (if present), then repo-root `.env` — without overriding shell vars.
2. Raises a clear error if `DATABASE_URL` is still missing (not `Settings has no attribute database_url`).

**Recommended local setup:**

```powershell
# Option A — copy example env (gitignored)
Copy-Item C:\Users\offic\workos\backend\.env.example C:\Users\offic\workos\backend\.env
# Edit backend/.env if needed; default uses sqlite+aiosqlite:///./dev.db relative to backend cwd

# Option B — export in shell (same pattern as npm run dev:backend)
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
```

If `DATABASE_URL` is missing, scripts exit with a message listing these options before connecting.

---

## Step 1 — Apply migrations

Dev local using `create_all` may skip Alembic; staged/production DBs need s51.

Run from `backend/` with `DATABASE_URL` set or `backend/.env` present:

```powershell
cd C:\Users\offic\workos\backend

# If not using backend/.env:
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'

.\.venv\Scripts\python.exe -m alembic upgrade head
```

Alternative (same requirement — DATABASE_URL must be set or in backend/.env):

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Do **not** rely on `alembic.ini` `sqlalchemy.url` (empty placeholder). Alembic loads `.env` the same way as owner scripts.

Required revision includes `s51_employee_manager_employee_id` (`employees.manager_employee_id`).

---

## Optional local/dev user seed

When the local DB has an empty `users` table (no OIDC login yet), seed a dev owner user **before** owner bootstrap.

This is **local/dev readiness only** — it does not replace OIDC/login, does not create Employee rows, and does not touch payroll.

```powershell
cd C:\Users\offic\workos\backend

$env:DATABASE_URL="sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db"

$env:WORKOS_DEV_OWNER_EMAIL="office@p-media.ro"
$env:WORKOS_DEV_OWNER_NAME="Axinte Remus"
$env:WORKOS_DEV_OWNER_ROLE="admin"
$env:WORKOS_DEV_OWNER_USER_ID="dev-owner-office-p-media-ro"
$env:WORKOS_DEV_OWNER_DRY_RUN="1"

.\.venv\Scripts\python.exe scripts\seed_dev_owner_user.py
```

Real run (persists User row only):

```powershell
$env:WORKOS_DEV_OWNER_DRY_RUN="0"
.\.venv\Scripts\python.exe scripts\seed_dev_owner_user.py
```

Then run owner bootstrap dry-run:

```powershell
$env:WORKOS_OWNER_EMAIL="office@p-media.ro"
$env:WORKOS_OWNER_EMPLOYEE_NAME="Axinte Remus"
$env:WORKOS_OWNER_BOOTSTRAP_DRY_RUN="1"
.\.venv\Scripts\python.exe scripts\bootstrap_owner_employee.py
```

Owner bootstrap remains a separate step — it links User → Employee and still does not create payroll or attendance.

---

## Test as specific dev user (Employee Mobile)

Dev auth bypass normally returns synthetic Dev Admin. To test as another **existing** user in local DB, set before starting backend:

```powershell
cd C:\Users\offic\workos\backend
$env:DATABASE_URL="sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db"
$env:APP_ENV="development"
$env:ENVIRONMENT="development"
$env:JWT_SECRET_KEY="local-dev-secret-not-for-production"
```

**Dev Admin (explicit):**

```powershell
$env:WORKOS_DEV_AUTH_USER_ID="dev-admin-user-00000000"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Normal employee (`employee_mobile`, requires user + employee link in DB):**

```powershell
$env:WORKOS_DEV_AUTH_USER_ID="dev-employee-test-001"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Owner seed user:**

```powershell
$env:WORKOS_DEV_AUTH_USER_ID="dev-owner-office-p-media-ro"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Notes:

- User must already exist in `users` (seed scripts do not run automatically).
- Employee Mobile **self** requires `employees.user_id` linked and `status=active`.
- **Restart backend** after changing `WORKOS_DEV_AUTH_USER_ID`.
- **Not available in production/staging** — env var is ignored when dev auth bypass is disabled.
- Does not create users or employees.

Unset env var to restore default synthetic Dev Admin:

```powershell
Remove-Item Env:WORKOS_DEV_AUTH_USER_ID -ErrorAction SilentlyContinue
```

---

## Step 2 — Bootstrap owner employee (dry-run)

Scripts load `backend/.env` automatically. Set owner vars in shell:

```powershell
$env:WORKOS_OWNER_EMAIL='<owner-email>'
$env:WORKOS_OWNER_EMPLOYEE_NAME='Axinte Remus'
$env:WORKOS_OWNER_EMPLOYEE_DEPARTMENT='Management'
$env:WORKOS_OWNER_EMPLOYEE_TITLE='Owner'
$env:WORKOS_OWNER_BOOTSTRAP_DRY_RUN='1'

cd C:\Users\offic\workos\backend
.\.venv\Scripts\python.exe scripts\bootstrap_owner_employee.py
```

If `DATABASE_URL` is missing, the script exits before DB init with setup instructions (not an AttributeError).

---

## Step 3 — Bootstrap owner employee (real)

```powershell
$env:WORKOS_OWNER_BOOTSTRAP_DRY_RUN='0'
.\.venv\Scripts\python.exe scripts\bootstrap_owner_employee.py
```

Expected: `action` = `created`, `linked_existing_employee`, `already_linked`, or `updated`.

---

## Step 4 — Assign direct reports (dry-run)

Prefer employee IDs or user emails — not department.

```powershell
$env:WORKOS_DIRECT_REPORT_USER_EMAILS='<employee1-email>,<employee2-email>'
# or: $env:WORKOS_DIRECT_REPORT_EMPLOYEE_IDS='12,15'
$env:WORKOS_DIRECT_REPORTS_DRY_RUN='1'
.\.venv\Scripts\python.exe scripts\assign_owner_direct_reports.py
```

If owner not linked: error `manager_employee_link_missing` — run Step 3 first.

To overwrite existing manager on a report:

```powershell
$env:WORKOS_DIRECT_REPORTS_FORCE_REASSIGN='1'
```

---

## Step 5 — Assign direct reports (real)

```powershell
$env:WORKOS_DIRECT_REPORTS_DRY_RUN='0'
.\.venv\Scripts\python.exe scripts\assign_owner_direct_reports.py
```

---

## Step 6 — Readiness check

```powershell
$env:WORKOS_OWNER_EMPLOYEE_NAME='Axinte Remus'
.\.venv\Scripts\python.exe scripts\check_employee_mobile_readiness.py
```

| status | Meaning |
|--------|---------|
| `PASS` | Ready for phone test |
| `WARN` | Linked owner OK but missing direct reports or non-root manager — review `team.warnings` |
| `FAIL` | Blocking issue in `issues` |

Exit code: 0 for PASS/WARN, 1 for FAIL.

---

## Step 7 — Phone test checklist

- [ ] Login with owner user
- [ ] Open `/employee-app` — Home, bottom nav, no desktop sidebar
- [ ] Cererile mele (`/employee-app/requests`)
- [ ] Pontajul meu (`/employee-app/attendance`) — read-only
- [ ] Review (`/employee-app/review`) — direct report requests only (manager role)
- [ ] Echipa mea (`/employee-app/team`) — direct reports only
- [ ] Desktop `/attendance/effects` — admin/operator only if applicable

---

## Env vars reference

| Variable | Purpose |
|----------|---------|
| `WORKOS_OWNER_EMAIL` | Owner user lookup |
| `WORKOS_OWNER_USER_ID` | Alternative user lookup |
| `WORKOS_OWNER_EMPLOYEE_ID` | Manager employee id for assignment |
| `WORKOS_OWNER_EMPLOYEE_NAME` | Required for bootstrap/readiness |
| `WORKOS_DIRECT_REPORT_EMPLOYEE_IDS` | Comma-separated employee ids |
| `WORKOS_DIRECT_REPORT_USER_EMAILS` | Comma-separated user emails |
| `WORKOS_DIRECT_REPORT_NAMES` | Unique name match only |
| `WORKOS_DIRECT_REPORTS_DRY_RUN` | `1` = no writes |
| `WORKOS_DIRECT_REPORTS_FORCE_REASSIGN` | `1` = overwrite existing manager |

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `DATABASE_URL environment variable is required` | Copy `backend/.env.example` → `backend/.env` or export `DATABASE_URL` |
| `Could not parse SQLAlchemy URL` (Alembic) | Same — empty/missing `DATABASE_URL`; set env or create `backend/.env` |
| `Settings object has no attribute database_url` | Fixed in owner-readiness DB config build — upgrade and use `backend/.env` or export `DATABASE_URL` |
| `owner_user_not_found` | Login once to create user row |
| `manager_employee_link_missing` | Run bootstrap owner script |
| `inactive_employee` | Set employee `status=active` |
| `manager_employee_id_column_missing` | Run Alembic through s51 |
| `no_direct_reports_assigned` | Run assign script Step 5 |
| Empty team/review | Verify `manager_employee_id` on reports |
| `missing_manager_role_for_review` | JWT role must be `admin` or `manager` |
| JWT role differs from `users.role` | Re-login; roles come from OIDC/JWT not bootstrap |
| Phone session/CORS issues | Same origin HTTPS; clear PWA cache |
| Old bundle on phone | Hard refresh or reinstall PWA |

---

## Important

| Statement | True |
|-----------|------|
| Employee record activates payroll | **No** |
| Bootstrap creates attendance/requests | **No** |
| Assignment uses department | **No** |
| Scripts modify auth/JWT roles | **No** |
