# BUILD: Personal Advances and Debts Foundation

## Purpose

Replace demo `Avansuri / Datorii` with a real internal ledger backed by live employees — advances, loans, retentions, repayments, compensations, and manual adjustments.

**Not fiscal payroll.** Not official accounting.

## Ledger model

Table: `employee_balance_transactions`

| Column | Notes |
|--------|-------|
| `employee_id` | FK → employees |
| `transaction_date` | date |
| `transaction_type` | advance, loan, retention, repayment, compensation, adjustment |
| `amount` | always > 0 |
| `currency` | default `RON` (module-internal) |
| `status` | active, settled, cancelled |
| `notes` | required for `adjustment` |
| `source` | default `manual` |

### Signed balance rules

| Type | Effect on `active_balance` |
|------|---------------------------|
| advance, loan, retention, adjustment | +amount |
| repayment, compensation | −amount |
| cancelled | excluded from summary |

`settled` is visual/historical — still affects ledger sum in MVP (same as `active`).

Summary includes **all active employees** with zero balance when no transactions.

## Migration

| Property | Value |
|----------|-------|
| File | `backend/alembic/versions/s48_employee_balance_transactions.py` |
| Revision | `s48_employee_balance_transactions` |
| Down revision | `s47_employee_attendance_events` |
| Table | `employee_balance_transactions` |

## API

Base: `/api/v1/employee-balances`

| Method | Path |
|--------|------|
| GET | `/summary` |
| GET | `/transactions?employee_id&status&transaction_type&start_date&end_date` |
| POST | `/transactions` |
| PUT | `/transactions/{id}` |
| POST | `/transactions/{id}/cancel` |

## UI (`EmployeeAdvances.tsx`)

- Badges: `LIVE DB`, `MANUAL`
- Alert: internal evidence, operator-confirmed compensation, not official accounting
- Summary KPIs + per-employee balance table
- Transaction list with filters
- Modal `Adaugă tranzacție` (employee, type, date, amount, currency, notes)
- `Anulează` on active transactions

## What this does NOT do

- Fiscal payroll / stat de plată
- Automatic salary deductions
- CostEngine, Quote/VAT, SmartBill, Inventory, Production
- Link to attendance/pontaj (future)

## Tests

| Suite | Command | Result (2026-06-11 re-verify) |
|-------|---------|-------------------------------|
| Backend balances | `pytest tests/test_employee_balances.py -q` | **13 passed** |
| Personal regression | attendance + workforce pytest bundle | **43 passed** |
| Frontend | `vitest EmployeeAdvances.test.tsx workforceRoutes.test.tsx` | **11 passed** |
| Typecheck | `tsc -b --noEmit` | **exit 0** |

## Local migration (dev.db) — PASS

| Step | Result |
|------|--------|
| Backup | `backend/dev.db.bak-20260611-174047-pre-employee-balances-foundation` (**not committed**) |
| First apply | `upgrade head` failed once (table pre-existed via `create_all`); schema verified; `stamp s48` applied |
| `alembic current` / `heads` | **`s48_employee_balance_transactions`** |
| SQLite `employee_balance_transactions` | Present; 11 columns match migration |

## API smoke — PASS (2026-06-11 18:49, live dev.db)

| Step | Result |
|------|--------|
| `GET /summary` (initial) | 200 — **8** active employees, all balances **0** |
| `POST /transactions` employee_id **1** | **404** `employee_id 1 not found` (expected — seed has no id 1) |
| `POST /transactions` advance id **12** | Created id **2**, 500 RON — Andrei Goghi `active_balance` **+500** |
| `GET /summary` (after create) | totals `active_balance` 500 |
| `POST /transactions/2/cancel` | status **`cancelled`** |
| `GET /summary` (after cancel) | totals back to **0** |
| DELETE | **Not exposed** on router |

## UI smoke — PASS (2026-06-11 re-verify)

| Check | Result |
|-------|--------|
| Route `/employee-advances` | Loads |
| `LIVE DB` / `MANUAL` badges | In component (Vitest asserts LIVE DB; no DEMO) |
| `DEMO` badge | Absent |
| Live employees | **8** in summary + employee filter |
| Summary KPIs | **0 RON** after API cancel |
| Form `Adaugă tranzacție` | Modal: angajat, tip, dată, sumă, monedă, observații |
| Create / cancel via UI click | **Not automated** (Cursor policy blocks Salvează); API smoke covers runtime |
| Cancelled rows in list | Visible; no balance impact |
| Fiscal payroll / stat de plată / contabilitate oficială | Not shown |

## dev.db smoke residue

- Transactions id **1** and **2** (Andrei Goghi, advance 500 RON, **cancelled**, notes “Smoke avans intern”) remain in dev.db.
- No DELETE endpoint on router; cancelled rows are acceptable residue.

## Boundaries

- Employee model unchanged
- `dev.db` / `.bak` not committed

## Risks

- `adjustment` increases balance only in MVP (use `compensation` to decrease)
- `settled` still counts in balance sum
- Currency hardcoded default RON for module

## Recommended commit message

`feat(personal): add employee balances foundation`
