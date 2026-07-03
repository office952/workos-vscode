# BUILD: Personal Attendance Events Foundation

## Purpose

Replace demo pontaj with **default-present** scheduling: active employees are implicitly present Mon–Fri 8h/day; operators record only **exceptions** as events.

**Abandoned approach:** daily `employee_attendance_entries` (create-present-per-day) was prototyped but **not shipped**. Final build is event-only.

## Default present decision

- **Program standard MVP (hardcoded):** 8h/day, Monday–Friday (`DEFAULT_WORK_HOURS_PER_DAY`, `DEFAULT_WORKING_WEEKDAYS`).
- No per-day manual “present” entries.
- Angajat activ, zi lucrătoare, fără eveniment → 8h implicit în summary.
- Future build: company settings for standard schedule (not in this build).

## Model

Table: `employee_attendance_events` only — **no** `employee_attendance_entries`.

| Column | Notes |
|--------|-------|
| `id` | PK |
| `employee_id` | FK → employees |
| `start_date` | inclusive range start |
| `end_date` | inclusive range end; single-day when `start_date = end_date` |
| `event_type` | absent, leave, sick, partial, overtime, correction |
| `event_status` | planned, approved, confirmed, cancelled (default `confirmed`) |
| `hours_override` | partial / correction |
| `hours_delta` | overtime / correction |
| `notes` | required for correction; recommended for sick |
| `source` | default `manual` |
| `created_at`, `updated_at` | timestamps |

**No unique constraint** on date+type — conflicts validated in service.

### Event types

| Type | Range | Notes |
|------|-------|-------|
| `leave` | yes | working weekdays only in summary |
| `sick` | yes | retro or future; notes recommended |
| `absent` | yes (UI may stay single-day MVP) | distinct from leave/sick |
| `partial` | single-day only | requires `hours_override` |
| `overtime` | single-day only | requires `hours_delta > 0`; weekend allowed |
| `correction` | single-day only | requires notes + override or delta |

### Event statuses

| Status | Summary impact |
|--------|----------------|
| `planned` | affects summary |
| `approved` | affects summary |
| `confirmed` | affects summary (default on create) |
| `cancelled` | **excluded** from summary; row kept for audit |

## Future / planned events

- `leave` / `sick` with `planned` or `approved` on future dates **reduce** summary for the selected month when dates fall in that month.
- UI shows status badge; summary counts `planned_event_count`, `approved_event_count`, `confirmed_event_count`, `cancelled_event_count`.

## Cancel behaviour

- MVP: **Anulează** sets `event_status = cancelled` via PUT (preserves history).
- **Delete** also supported (removes row; restores summary).
- Cancelled events remain in event list with status badge.

## Conflict rules (service validation)

1. No two **full-day** types (`absent`, `leave`, `sick`) on the same working day.
2. No `partial` if full-day absent/leave/sick exists that day.
3. No duplicate `partial` same day.
4. `overtime` allowed with implicit present; allowed on weekends.
5. `correction` with `hours_override` cannot coexist with non-`overtime` events same day.
6. `start_date > end_date` rejected.
7. Conflicts return HTTP 409 from router.

## Weekend behaviour

- **Full-day types** (`absent`, `leave`, `sick`): range must include ≥1 working weekday; weekend days in range are **excluded** from day count.
- **`partial`**: only on working weekdays.
- **`overtime` / `correction`**: any calendar day (including weekend).

## Summary calculation

Per **active** employee for selected month:

1. `standard_work_days` = Mon–Fri in month
2. `standard_hours` = days × 8
3. Start: `present_days = standard_work_days`, `total_hours = standard_hours`
4. Apply each non-cancelled event overlapping month:
   - absent/leave/sick: −8h per working day in overlap
   - partial: −(8 − override) per day
   - overtime: +delta (any day)
   - correction: override/delta rules per day type
5. Status counters per overlapping event (including cancelled for audit counts)

No money, no CostEngine, no fiscal payroll.

## Migration (single final)

| Property | Value |
|----------|-------|
| File | `backend/alembic/versions/s47_employee_attendance_events.py` |
| Revision | `s47_employee_attendance_events` |
| Down revision | `s46_company_commercial_settings` |
| Creates | `employee_attendance_events` (+ indexes) |
| Legacy cleanup | Drops table if old `event_date` schema (no `start_date`/`event_status`) |
| Does **not** create | `employee_attendance_entries` |
| No `s48` revision | confirmed absent from repo |

### Local dev.db

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

If DB was stamped to a deleted revision: `alembic stamp --purge s47_employee_attendance_events` then upgrade.

If `alembic_version` is `s47` but table still has legacy `event_date` column (stamp without migrate): run downgrade then upgrade:

```powershell
.\.venv\Scripts\python.exe -m alembic downgrade s46_company_commercial_settings
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Verified 2026-06-11: columns `start_date`, `end_date`, `event_status` present; `employee_attendance_entries` absent.

## Test harness: `conftest.py` change

Added before app import in `backend/tests/conftest.py`:

```python
os.environ["APP_ENV"] = "test"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-not-for-production"
```

**Why:** `backend/release.json` has `environment: staging`. Without explicit `APP_ENV`, pytest `auth_client` lifespan runs startup safety as staging with no JWT → **BLOCKED** → TestClient startup fails (`test_summary_api_returns_200`).

**Scope:** Applies to all backend tests using shared conftest (session-level, before `main` import).

**Safety:** Does not change application code or production config. `run_startup_safety_checks()` treats `test` as non-strict (informational only). Tests that need other env values use `patch.dict(os.environ, ...)` after conftest load (e.g. `test_auth_environment_hardening.py`).

**Risk:** Low — prevents false BLOCKED from release metadata in local pytest; does not mask staging/production misconfig in deployed builds.

## API

Base: `/api/v1/employee-attendance`

| Method | Path |
|--------|------|
| GET | `/events?start_date&end_date&employee_id?` |
| POST | `/events` |
| PUT | `/events/{id}` |
| DELETE | `/events/{id}` |
| GET | `/summary?year&month` |

## Initial `/summary` 500 and fix

**Symptom:** `GET /api/v1/employee-attendance/summary` returned 500 on stale uvicorn.

**Cause:** Process loaded old daily-entry model while code referenced event model only.

**Fix:** Restart backend (`npm run dev:backend` or `dev:stack`). Ensure `alembic upgrade head` applied for new columns.

## UI (`Attendance.tsx`)

- Badges: `LIVE DB`, `EVIDENȚĂ INTERNĂ`
- Alert: implicit present + exceptions only
- Form: employee, type, status, start/end date, hours override/delta, notes
- Leave/sick/absent: range allowed; hint: *Se aplică doar zilelor lucrătoare din interval.*
- Partial/overtime/correction: single-day enforced in UI
- Event list: interval, type, status, impact, notes; Anulează / Șterge
- Summary KPIs + per-employee table with status counts
- No payroll fiscal UI

## What this does NOT do

- Fiscal payroll / stat de plată
- CostEngine, Quote/VAT, SmartBill, Inventory, Production
- Settings UI for standard schedule
- Full calendar grid / export / approval workflow

## Tests

| Suite | Command | Result (2026-06-11) |
|-------|---------|---------------------|
| Backend attendance | `pytest tests/test_employee_attendance_events.py -q` | **14 passed** |
| Workforce regression | `pytest test_operator_employee_selection + operational_* + execution_reality_workforce_capture -q` | **29 passed** |
| Frontend | `vitest run src/pages/Attendance.test.tsx src/pages/workforceRoutes.test.tsx` | **11 passed** |
| Typecheck | `tsc -b --noEmit` | **exit 0** |

Backend cases: default present, leave range 5d, sick range, cancelled leave, weekend skip, partial, overtime weekend, absent+leave conflict, partial+leave conflict, correction no notes, start>end, delete restore, future leave, API summary 200.

## Smoke (2026-06-11)

### Alembic / SQLite — PASS

- `alembic current` / `heads`: `s47_employee_attendance_events`
- After downgrade s46 + upgrade: `start_date`, `end_date`, `event_status` columns present
- `employee_attendance_entries` absent

### API — PASS

- `GET /employee-attendance/summary?year=2026&month=6` → **200**, 8 active employees, `standard_work_hours_per_day: 8`
- Dev auth bypass (no Bearer required in `development`)
- Create leave planned 2026-06-15→2026-06-19 (employee 12): `leave_days=5`, `total_hours=136`
- Cancel → `leave_days=0`, `total_hours=176`, `cancelled_event_count=1`
- Delete → event removed

### UI (`/attendance`) — PASS

- Page loads; **LIVE DB** badge; no DEMO; no payroll fiscal labels
- 8 live employees; default present messaging when no events
- Form modal: tip, status, start/end date, notes; range hint for leave/sick
- After API-created leave: summary **1368h** total estimate, Andrei Goghi **136h**, event list shows range + **PLANNED** + Anulează
- Smoke events created then cancelled/deleted via API (dev.db clean after smoke)

### Backups (not committed)

- `dev.db.bak-20260611-162414-pre-attendance-events-final-smoke` (+ prior attendance backups)

## Boundaries

- Employee model unchanged.
- `dev.db` / `.bak` not committed.
- `backend/tests/conftest.py`: forces `APP_ENV=test` so `auth_client` survives `release.json` staging metadata.

## Risks

- Standard schedule hardcoded (not per-employee or per-company)
- `partial + overtime` same day allowed (by design)
- Auth = `get_current_user` only
- Alembic upgrade drops/recreates events table if legacy `event_date` schema

## Recommended commit message

`feat(personal): add event-based attendance foundation`
