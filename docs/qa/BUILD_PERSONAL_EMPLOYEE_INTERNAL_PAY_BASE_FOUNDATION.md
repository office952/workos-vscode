# BUILD — Personal Employee Internal Pay Base Foundation

## Purpose

Add a **real internal monthly pay base** on the operational employee profile so Employee Payments can later calculate tranșe 15/30 from live data — without using `cost_lunar_firma` (company / CostEngine cost).

## Motivation

Live-data audit (`PERSONAL_EMPLOYEE_PAYMENTS_LIVE_DATA_CONTRACT.md`) found no valid pay-base field. Demo code incorrectly fell back to `cost_lunar_firma` or synthetic values.

## New field

| Property | Value |
|----------|--------|
| DB column | `employees.monthly_internal_pay_amount` |
| Type | `Float`, nullable |
| Currency | Uses existing `salary_currency` on employee (default RON) — no new currency system |
| Semantics | Internal monthly amount for tranșe 15/30 in Plăți angajați |

## Difference from `cost_lunar_firma`

| Field | Meaning | Used by |
|-------|---------|---------|
| `cost_lunar_firma` | Total monthly **company cost** (salariu + taxe + beneficii) | CostEngine, `cost_ora_calculat` |
| `monthly_internal_pay_amount` | Internal **pay base** for operator payment tranșe | Future Employee Payments live calc |

API `salary_amount` remains an alias for `cost_lunar_firma` only — **not** mapped to internal pay.

## Where edited

- **Page:** `/employees` (`Employees.tsx`)
- **Label:** Sumă lunară internă pentru plată
- **Helper:** Folosită ulterior pentru calculul tranșelor 15/30 în Plăți angajați. Nu reprezintă costul total al firmei.

## Migration

| File | Revision |
|------|----------|
| `backend/alembic/versions/s49_employee_monthly_internal_pay_amount.py` | `s49_employee_monthly_internal_pay_amount` |
| Down revision | `s48_employee_balance_transactions` |

Adds column only on `employees`. No payment tables.

**Local backup before migrate (manual):**

```powershell
Copy-Item .\backend\dev.db .\backend\dev.db.bak-<stamp>-pre-s49-internal-pay-base
```

## Files changed

| File | Change |
|------|--------|
| `backend/models/employees.py` | Column + comment |
| `backend/alembic/versions/s49_employee_monthly_internal_pay_amount.py` | Migration |
| `backend/services/employees.py` | Validation (>= 0) |
| `backend/routers/employees.py` | Create/update/response |
| `frontend/src/api/costEngine.ts` | DTO + payload types |
| `frontend/src/pages/Employees.tsx` | Form + detail panel |
| `backend/tests/test_employee_internal_pay_base.py` | Service + serialize tests |
| `frontend/src/pages/Employees.internalPayBase.test.tsx` | UI label/helper tests |

## What was NOT implemented

- Employee Payments page changes
- `employee_payment_records` table / API
- schedule-preview, compensation profiles
- CostEngine changes
- Fiscal payroll, taxes, SmartBill
- Pontaj / balances changes
- Wiring `operationalEmployeeRecords.sumaLunaraInterna` to new field (next live wiring build)

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_internal_pay_base.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/Employees.internalPayBase.test.tsx
```

Confirm Employee Payments untouched:

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeePayments.test.tsx
```

## Boundary

Frontend-only Employees + backend employee field. No commit in agent session (owner manual commit-tree).

## Next build

`BUILD_PERSONAL_EMPLOYEE_PAYMENTS_LIVE_WIRING` — situation API, payment records, frontend hook; use `monthly_internal_pay_amount` as calc input.
