# BUILD — Personal Employee Payments Live Data Wiring

## Branch + HEAD (before this build)

| Item | Value |
|------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| Base HEAD | `c7dbdf7` — `feat(personal): add employee internal pay base` |
| Prerequisite | `s49_employee_monthly_internal_pay_amount` on `employees` |

## Scope

Wire `/employee-payments` from demo/local state to **live backend data** while preserving the accepted **master-detail UI** (Tranșa 15 / Tranșa 30 tabs, left employee list, right detail + payment form).

The page is **informational / operational** only:

1. Read monthly payment situation (tranșe 15/30).
2. Record actual paid amounts.
3. Show paid / remaining / status.

**Out of scope:** fiscal payroll, taxes, SmartBill, CostEngine, compensation profiles, salary configuration on Payments, pontaj edits, balance/debt edits, auto-close debts, auto-create payments on load.

**Contract references:**

- `docs/architecture/PERSONAL_EMPLOYEE_PAYMENTS_SCREEN_CONTRACT.md`
- `docs/architecture/PERSONAL_EMPLOYEE_PAYMENTS_LIVE_DATA_CONTRACT.md`
- `docs/qa/BUILD_PERSONAL_EMPLOYEE_INTERNAL_PAY_BASE_FOUNDATION.md`

## Files modified / created

### Backend

| File | Change |
|------|--------|
| `backend/models/employee_payment_record.py` | New model `employee_payment_records` |
| `backend/models/__init__.py` | Import new model |
| `backend/alembic/versions/s50_employee_payment_records.py` | Migration s50 |
| `backend/services/employee_payment_situation_service.py` | Read-only situation calculation |
| `backend/services/employee_payment_record_service.py` | Create + cancel payment records |
| `backend/routers/employee_payments.py` | API router (`/api/v1/employee-payments`) |
| `backend/tests/test_employee_payments_live.py` | Live wiring pytest |

Router auto-registered via `include_routers_from_package` in `main.py`.

### Frontend

| File | Change |
|------|--------|
| `frontend/src/api/employeePayments.ts` | API client + DTO types |
| `frontend/src/lib/employeePaymentLiveMapper.ts` | API → existing UI type mapping |
| `frontend/src/lib/employeePaymentSituationDemo.ts` | Optional `history` on slot type (demo/tests) |
| `frontend/src/pages/EmployeePayments.tsx` | Live fetch + POST + refetch; badge **LIVE DB** |
| `frontend/src/pages/EmployeePayments.test.tsx` | Mock live API (not demo builder) |

### QA

| File | Change |
|------|--------|
| `docs/qa/BUILD_PERSONAL_EMPLOYEE_PAYMENTS_LIVE_DATA_WIRING.md` | This document |

**Not part of commit:** local `dev.db`, `dev.db.bak-*`, archived broken DB under `workos-local-backups`.

## Migration s50

| Property | Value |
|----------|--------|
| Revision | `s50_employee_payment_records` |
| Down revision | `s49_employee_monthly_internal_pay_amount` |
| Table | `employee_payment_records` |

Columns: `id`, `employee_id`, `year`, `month`, `slot` (`15` \| `30`), `amount_paid`, `payment_date`, `status`, `notes`, `cancelled_at`, `cancelled_reason`, `source`, `created_at`, `updated_at`.

Index: `ix_employee_payment_records_employee_period` on `(employee_id, year, month, slot)`.

Does **not** modify `employees`, attendance, or balance tables.

**Apply on fresh or migrated DB:**

```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Local dev.db — Option B (fresh rebuild)

Prior local `dev.db` was **inconsistent** (phantom alembic revision, legacy `employee_payment_records` prototype schema blocking s50). Owner approved **Option B**: fresh DB aligned with repo migrations.

1. Verified backup copy of broken DB.
2. Moved active `backend/dev.db` out of path.
3. `alembic upgrade head` on empty DB → head `s50_employee_payment_records`.
4. Reseeded employees + dev pay-base values for smoke.

**Archive path (do not commit):**

`C:\Users\offic\workos-local-backups\2026-06-11-employee-payments-live-wiring\`

- `dev.db.broken-pre-fresh-rebuild.sqlite`
- `dev.db.active-path-removed.sqlite`

## Backend endpoints

Prefix: `/api/v1/employee-payments` (auth: dev bypass or JWT).

### GET `/situation?year=YYYY&month=MM`

Read-only. Returns monthly summary + per-employee slots `15` and `30`. Does **not** create payment records or mutate employees / pontaj / balances.

### POST `/`

Creates one payment record. Body:

```json
{
  "employee_id": 7,
  "year": 2026,
  "month": 6,
  "slot": "15",
  "amount_paid": 500,
  "payment_date": "2026-06-11",
  "notes": "optional"
}
```

Does not modify employee profile, pontaj, or balances.

### POST `/{record_id}/cancel` (optional)

Sets `status` cancelled + `cancelled_at` / `cancelled_reason`. Cancelled records excluded from active `paid_amount`. Implemented; runtime smoke focused on create + situation refetch.

## Owner decision — salary source realignment (post-audit)

After live wiring at `a4d909f`, audit found employees with profile salary in `cost_lunar_firma` / API `salary_amount` showed **0 RON** in Plăți because calculation used `monthly_internal_pay_amount` (mostly NULL).

**Owner decision (Option A):** Profile salary = `employees.cost_lunar_firma` / `salary_amount` **always** for Employee Payments tranșe base.

- `monthly_internal_pay_amount` is **not** the active payment base after this fix.
- Avoids duplicate salary entry; matches „Salariu HR” in operational registry.
- CostEngine logic unchanged; same DB column is shared operationally.
- Examples: Chirilă 7000 → 3500/3500; Andrei 8000 → 4000/4000; Vali 5000 → 2500/2500.

Attendance / overtime / loans / debts remain **adjustment layers** (deferred amounts = 0 in this build).

## Calculation rules

| Rule | Behavior |
|------|----------|
| Pay base (`salary_monthly`) | `employees.cost_lunar_firma` (= API `salary_amount`) |
| `base_source` | `employee_profile_salary` |
| Slot 15 expected | `salary_monthly / 2` (before adjustments) |
| Slot 30 expected | `salary_monthly / 2` (before adjustments) |
| Slot 15 period | `YYYY-MM-01` … `YYYY-MM-15` |
| Slot 30 period | `YYYY-MM-16` … last day of month |
| `monthly_internal_pay_amount` | **Not** used for payment base |
| Missing salary | `cost_lunar_firma` null or ≤ 0 → `missing_pay_base`; warning `missing_profile_salary`; expected 0 |
| POST guard | Payment rejected if profile salary missing or ≤ 0 |
| Paid | Sum of non-cancelled records (`confirmed` / `draft`) for employee/year/month/slot |
| Remaining | `max(expected - paid, 0)` |
| Status | `unpaid` (paid=0, expected>0), `partial` (paid>0, remaining>0), `paid` (remaining=0, expected>0), `missing_base` (no base) |
| Pontaj | Read-only label from attendance summary; `attendance_adjustment` = 0 (deferred) |
| Balances | Read-only label + informational `suggested_deduction`; not applied to expected; `no_auto_close` |

## Frontend wiring

| Item | Detail |
|------|--------|
| Badge | **LIVE DB** (replaces DEMO when data from API) |
| Client | `frontend/src/api/employeePayments.ts` — `getSituation`, `createPayment`, `cancelPayment` |
| Mapper | `employeePaymentLiveMapper.ts` → existing master-detail types |
| Page | `EmployeePayments.tsx` — load situation on month change; POST on save + refetch; loading/error/empty states |
| Layout | Master-detail preserved: tabs 15/30, left list, right detail + form |
| Missing base | Warning „Lipsește suma lunară în profilul angajatului.” + CTA „Deschide profil angajat” — **no** salary edit on Payments |
| Removed from runtime | `recordedPayments` local state, `usePersonalDemoModule` as primary source |

## Runtime smoke (fresh dev.db, 2026-06-11)

**Stack:** backend `127.0.0.1:8000`, frontend `127.0.0.1:3000`.

**Seed:** `seed_operational_workforce_registry()` — profile salary in `cost_lunar_firma` for all employees.

| Employee | `cost_lunar_firma` / `salary_amount` | Slot 15 / 30 expected |
|----------|--------------------------------------|------------------------|
| Chirila Cristian | 7000 | 3500 / 3500 |
| Andrei Goghi | 8000 | 4000 / 4000 |
| Vali Colantator | 5000 | 2500 / 2500 |
| No profile salary | null / 0 | missing warning; 0 |

| Check | Result |
|-------|--------|
| `GET /openapi.json` | 200 |
| `GET /situation?year=2026&month=6` | 200, employees + slots 15/30 |
| Chirila 7000 | 3500 / 3500 per slot |
| Andrei 8000 | 4000 / 4000 per slot |
| Vali 5000 | 2500 / 2500 per slot |
| Recorded payments subtracted from slot | PASS |
| Missing salary warning only when `cost_lunar_firma` absent | PASS |
| POST payment persists + refresh | PASS |
| `employee_payment_records` count after smoke | 2 |
| `employee_attendance_events` | 0 (no mutation) |
| `employee_balance_transactions` | 0 (no mutation) |
| LIVE DB badge on `/employee-payments` | Visible |

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_payments_live.py tests/test_employee_internal_pay_base.py -q
```

**Result:** 10 passed.

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeePayments.test.tsx src/pages/Employees.internalPayBase.test.tsx
```

**Result:** 10 passed (8 EmployeePayments + 2 Employees internal pay base).

## Boundaries confirmed

- No CostEngine integration
- No SmartBill
- No fiscal payroll / tax / gross/net fiscal fields
- Profile salary = `cost_lunar_firma` / `salary_amount` for Plăți (CostEngine logic not changed)
- `monthly_internal_pay_amount` not used as payment base
- No salary / profile configuration on Plăți angajați
- No attendance mutation from Payments
- No balance / debt mutation from Payments
- No automatic debt close or compensation transactions

## Limitations / next candidates

| Item | Notes |
|------|--------|
| Attendance adjustment | Label only; adjustment amount 0 until rules defined |
| Overtime in breakdown | 0 + deferred warnings when no confirmed rate |
| `suggested_deduction` | Informational; not subtracted from expected |
| Cancel payment UI | API exists; operator cancel flow not in this build |
| `operationalEmployeeRecords.sumaLunaraInterna` | Still demo mapping from `cost_lunar_firma` — separate cleanup |
| Production deploy | Run `alembic upgrade head` on target DB; do not copy local `dev.db` |
| E2E Playwright | Not added; Vitest + manual smoke used |

## Commands + results summary

| Gate | Status |
|------|--------|
| Alembic s50 on fresh DB | PASS |
| Backend targeted pytest | PASS (10) |
| Frontend targeted vitest | PASS (10) |
| Runtime smoke `/employee-payments` | PASS |
| `validate:frontend` (full repo) | Not run — not this build gate |

## Next steps

Manual **commit-tree** on branch `local/integration-pr4-plus-svg-path` with backend + frontend + this QA doc. Exclude local DB backups from commit.
