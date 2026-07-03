# BUILD: Reproducible Employee Mobile Production Fixture — Sandu + Tasks + Work File

## 1. Purpose

Provide a **manual, dev-only, idempotent** way to recreate the local Employee Mobile production scenario:

- dev user `dev-sandu-employee-001` (`employee_mobile`);
- link to existing employee **Putaru Sandu**;
- six execution tasks assigned on the E2E commercial order;
- one intake production SVG work-file for mobile document handoff smoke.

**Base commit:** `da0f2c1` — `feat(employee): hand off production documents to mobile tasks`

## 2. Why this fixture exists

The Sandu mobile scenario (6 tasks + SVG on order `1`) was previously created **manually** in `backend/dev.db` and `backend/storage/intake_work_files/`. That state was not reproducible after DB reset or on another machine.

This build adds an explicit script — **not** startup seed, **not** migration.

## 3. What the script creates/updates

| Item | Action |
|------|--------|
| User `dev-sandu-employee-001` | Create or ensure email/name/role |
| Employee **Putaru Sandu** | Set `user_id` link only (does not create employee) |
| Order `1` / `WI-E2E-COMMERCIAL-001` | Assign T-004, T-006, T-007, T-008, T-009, T-010 to Sandu |
| Intake work-file | Ensure `sandu-sketch-001` metadata + minimal SVG on disk |

## 4. What it does NOT modify

- **Axinte** / owner users
- **Calin / T-001** assignment (protected)
- Quote PDF / commercial archive
- Order snapshot cost/pricing JSON
- `execution_reality` (no reset of started/blocked/done)
- Employee Mobile UI
- CostEngine / pricing / global seeds

## 5. How to run

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'

cd backend
.\.venv\Scripts\python.exe scripts/dev_seed_employee_mobile_sandu_fixture.py
.\.venv\Scripts\python.exe scripts/dev_seed_employee_mobile_sandu_fixture.py --apply
```

- **Default:** dry-run — prints planned actions, no writes.
- **`--apply`:** writes to dev DB + storage.
- **Guards:** refuses staging/production; requires local sqlite `DATABASE_URL` unless `WORKOS_DEV_SANDU_FIXTURE_FORCE=1` (discouraged).

## 6. Idempotency

Second `--apply` run should report:

- `user_exists` / `employee_user_id_ok`
- `skip` for tasks already assigned to Sandu
- `work_file_exists_on_disk` / `work_file_metadata_unchanged`

No duplicate users, attachments, or redundant assignments.

## 7. Smoke (after `--apply`)

```powershell
$env:WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/tasks
```

Expected:

- Putaru Sandu / `employee_mobile`
- 6 tasks with document `Schiță litere volumetrice.svg`
- T-001 absent
- Download: `GET /api/v1/employee-mobile/orders/1/work-files/sandu-sketch-001/download` → 200, `image/svg+xml`

Browser: `http://127.0.0.1:3000/employee-app/tasks` — task detail shows **Deschide**.

## 8. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_dev_employee_mobile_sandu_fixture.py tests/test_employee_mobile_tasks.py -q
```

Helper tests cover attachment merge idempotency and assignment planning.

## 9. Risks

| Risk | Mitigation |
|------|------------|
| Accidental run on non-dev DB | APP_ENV guard + sqlite URL check |
| Multiple employees named Sandu | Script stops with error |
| Sandu missing from workforce seed | Script stops — run operational workforce seed first |
| Task already started/blocked | Warning only; assignment skipped for that task |
| Reassign away from another employee | Only on listed Sandu task IDs; T-001 protected |

## 10. When to remove or rebuild

- After `dev.db` delete/reset: run E2E commercial fixture seed if needed, then this script with `--apply`.
- To drop the SVG only: remove file under `storage/intake_work_files/WI-E2E-COMMERCIAL-001/` and attachment row from intake spec (or re-run script — idempotent recreate).
- **Do not commit** `dev.db` or generated storage files.

## Files

- `backend/scripts/dev_seed_employee_mobile_sandu_fixture.py`
- `backend/services/dev_employee_mobile_sandu_fixture_service.py`
- `backend/tests/test_dev_employee_mobile_sandu_fixture.py`

## Boundary

Dev/test reproducibility only. No production behavior change.
