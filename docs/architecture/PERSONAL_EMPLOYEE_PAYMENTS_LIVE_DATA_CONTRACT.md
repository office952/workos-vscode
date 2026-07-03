# Personal — Employee Payments Live Data Contract

**Date:** 2026-06-11  
**Type:** Audit + API contract — **no implementation in this build**  
**Git baseline:** `b35bcd3`  
**UI baseline:** `89c4023` master-detail DEMO (`employeePaymentSituationDemo.ts`)  
**Screen contract:** `docs/architecture/PERSONAL_EMPLOYEE_PAYMENTS_SCREEN_CONTRACT.md`

---

## 1. Purpose

Wire `/employee-payments` to **real read sources** (profile, pontaj, balances) and **write-only payment recordings**, without changing page responsibility.

This document records what exists today, what is missing, proposed APIs, calculation/mutation rules, and the next implementation build scope.

---

## 2. Audit — real sources today

### A. Employee / profil angajat

| Item | Finding |
|------|---------|
| **Table** | `employees` (`backend/models/employees.py`) |
| **API** | `GET/PATCH /api/v1/entities/employees` (`backend/routers/employees.py`) |
| **Frontend edit** | `/employees` — `frontend/src/pages/Employees.tsx` |
| **Live list hook** | `useOperationalEmployees` → `employeesApi.list` |

**Monetary / hours fields on `employees`:**

| Field | Role today | Valid for Payments base? |
|-------|------------|---------------------------|
| `cost_lunar_firma` | Profile salary in operator workflow; CostEngine labour input; shown as **Cost lunar firmă** on `/employees` and **Salariu HR** via `salary_amount` in operational registry | **YES** — **active payment base** after owner decision (2026-06-11) |
| `salary_amount` (API alias) | Same as `cost_lunar_firma` in `_serialize` | **YES** — same as profile salary |
| `monthly_internal_pay_amount` | Optional separate field on `/employees` (s49) | **NO** — not used for Plăți calculation after realignment |
| `ore_lucru_luna` | Nominal hours/month | Read-only context for future proration |
| `ore_productive_luna` | Productive hours/month | CostEngine only |
| `salary_currency`, `salary_period` | Metadata | Display only |

**Owner decision (post-audit, implemented in live wiring):**

- Employee Payments **salary source** = profile salary = `cost_lunar_firma` / `salary_amount`.
- Tranșa 15 = `salary_monthly / 2`; Tranșa 30 = `salary_monthly / 2`; then adjustments (attendance, overtime, advances/debts) and subtract recorded payments.
- Examples: Chirilă 7000 → 3500/3500; Andrei 8000 → 4000/4000.
- Avoids duplicate salary entry; `monthly_internal_pay_amount` is not the active Plăți base.
- CostEngine aggregation logic is **not** changed in this build (same DB column shared operationally).

**Historical note:** Initial live wiring (`a4d909f`) incorrectly used `monthly_internal_pay_amount` only; audit fixed via salary source realignment.

**Compensation profiles:** not in repo (rejected WIP rolled back).

### B. Pontaj (attendance)

| Item | Finding |
|------|---------|
| **Table** | `employee_attendance_events` (`s47`) |
| **Model** | `backend/models/employee_attendance_event.py` |
| **Service** | `backend/services/employee_attendance_service.py` |
| **API base** | `/api/v1/employee-attendance` |
| **Frontend** | `frontend/src/api/employeeAttendance.ts`, `useEmployeeAttendance`, `/attendance` |

**Endpoints (live):**

| Method | Path | Role |
|--------|------|------|
| GET | `/summary?year=&month=` | Month rollup per active employee |
| GET | `/events?start_date=&end_date=&employee_id=` | Exception events in range |
| POST/PATCH/DELETE | `/events`, `/events/{id}` | **Mutations — forbidden on Payments page** |

**Event types:** `absent`, `leave`, `sick`, `partial`, `overtime`, `correction`  
**Event statuses:** `planned`, `approved`, `confirmed`, `cancelled`  
**Summary applies:** `planned`, `approved`, `confirmed` (not `cancelled`)

**Default-present model:** Mon–Fri 8h; exceptions only. No per-day present rows.

**Summary fields per employee:** `standard_work_days`, `standard_hours`, `present_days`, `absent_days`, `leave_days`, `sick_days`, `partial_days`, `overtime_hours`, `total_hours`, status counts (`planned_event_count`, etc.).

**Payments page today:** uses **demo** `getMonthlyAttendance()` from `employeeRecordsData.ts` (synthetic calendar) — **not** live API.

**Tranșa periods (1–15 vs 16–end):**

- **Not implemented** in backend summary — full calendar month only.
- Live situation service must clip events to:
  - slot `15`: `[month-01 … month-15]` working days
  - slot `30`: `[month-16 … month-last]` working days

**Completeness / validation labels (proposed for UI):**

| Label | Rule |
|-------|------|
| OK | No unconfirmed gaps; `present_days` aligns with standard minus documented exceptions |
| Incomplet | `planned_event_count > 0` OR material attendance gaps |
| Nevalidat | `approved_event_count > 0` with zero `confirmed` on material events (policy TBD) |

### C. Avansuri / Datorii (balances)

| Item | Finding |
|------|---------|
| **Table** | `employee_balance_transactions` (`s48`) |
| **Model** | `backend/models/employee_balance_transaction.py` |
| **Service** | `backend/services/employee_balance_service.py` |
| **API base** | `/api/v1/employee-balances` |
| **Frontend** | `frontend/src/api/employeeBalances.ts`, `/employee-advances` |

**Endpoints (live):**

| Method | Path | Role |
|--------|------|------|
| GET | `/summary` | Per-employee rollup + totals |
| GET | `/transactions?employee_id=&status=&…` | Ledger lines |
| POST/PATCH | `/transactions`, cancel route | **Mutations — forbidden on Payments page** |

**Transaction types:** `advance`, `loan`, `retention`, `repayment`, `compensation`, `adjustment`  
**Statuses:** `active`, `settled`, `cancelled`

**Active balance calculation:**

- `cancelled` → excluded from summary.
- `settled` → **still counted** in `active_balance` (MVP per `BUILD_PERSONAL_ADVANCES_DEBTS_FOUNDATION.md`).
- Signed: advance/loan/retention/adjustment **+**; repayment/compensation **−**.

**Summary endpoint:** `GET /api/v1/employee-balances/summary` — **exists**; includes all active employees with zero when empty.

**Payments page today:** `usePersonalDemoModule` → `buildDemoAdvancesForEmployees` — **not** live balances API.

**Suggested retention for payment calc (read-only):**

- Use `active_balance` for display label.
- For slot deduction suggestion: sum **active** `retention` lines in period + configurable loan installment policy (not auto-closing loans on payment save).

### D. Plăți existente (payment recordings)

| Item | Finding |
|------|---------|
| **Backend table/model** | **Does not exist** in repo at `b35bcd3` |
| **Rejected WIP** | `employee_payment_records` was in rolled-back patch (local archive only) |
| **Frontend today** | `RecordedPaymentEntry` + React `recordedPayments` state in `EmployeePayments.tsx` |
| **Demo helper** | `createRecordedPayment` in `employeePaymentSituationDemo.ts` |

**Minimum table for next build** (`employee_internal_payment_records` suggested name):

| Column | Type | Notes |
|--------|------|-------|
| `id` | int PK | |
| `employee_id` | int FK | → `employees.id` |
| `year` | int | calendar year |
| `month` | int | 1–12 |
| `slot` | string | `15` \| `30` |
| `amount_paid` | float | > 0 |
| `payment_date` | date | |
| `status` | string | `draft` \| `confirmed` \| `cancelled` |
| `notes` | text | optional |
| `source` | string | default `manual` |
| `created_at`, `updated_at` | timestamp | |

**Excluded:** `gross_internal_amount`, fiscal net, taxes, SmartBill, payment_method enums tied to accounting.

**Cancelled handling:** cancelled rows appear in history; excluded from `paid_amount` sums (mirror demo).

**Migration:** `s49_*` — **not in this build**; next implementation build only.

---

## 3. Proposed read API

### `GET /api/v1/employee-payments/situation`

**Query:** `year` (int), `month` (int 1–12)

**Auth:** same as other Personal operational routes (`get_current_user`).

**Response shape** (supports existing master-detail UI without layout change):

```json
{
  "year": 2026,
  "month": 6,
  "currency": "RON",
  "summary": {
    "calculated": 54004,
    "paid": 0,
    "remaining": 54004,
    "partial_or_unpaid_slots": 16
  },
  "employees": [
    {
      "employee_id": 1,
      "employee_name": "Andrei Goghi",
      "attendance_label": "OK — 21/22 zile",
      "advances_debts_label": "Sold activ 300 RON (1 poz.)",
      "monthly_expected_amount": 8070,
      "monthly_paid_amount": 500,
      "monthly_remaining_amount": 7570,
      "missing_pay_base": false,
      "warnings": [],
      "slots": {
        "15": { "...slot..." },
        "30": { "...slot..." }
      }
    }
  ]
}
```

**Per slot object:**

```json
{
  "slot": "15",
  "label": "Tranșa 15",
  "expected_amount": 4035,
  "paid_amount": 500,
  "remaining_amount": 3535,
  "status": "partial",
  "breakdown": {
    "base_amount": 2000,
    "attendance_adjustment": 0,
    "overtime_amount": 135,
    "advances_debts_deduction": 300,
    "existing_payments": 500
  },
  "history": [
    {
      "id": 42,
      "amount_paid": 500,
      "payment_date": "2026-06-11",
      "status": "confirmed",
      "notes": null,
      "created_at": "2026-06-11T18:00:00Z"
    }
  ]
}
```

**Status enum (API):** `unpaid` | `partial` | `paid` (map to UI Neplătit / Parțial / Plătit).

**Warnings examples:** `missing_pay_base`, `attendance_incomplete`, `attendance_unconfirmed`, `planned_events_pending`.

**Implementation note:** single aggregated endpoint preferred over 4 client calls — server composes employees + attendance + balances + payment records.

---

## 4. Proposed write API

### `POST /api/v1/employee-payments`

**Body:**

```json
{
  "employee_id": 1,
  "year": 2026,
  "month": 6,
  "slot": "15",
  "amount_paid": 500,
  "payment_date": "2026-06-11",
  "notes": "optional"
}
```

**Rules:**

| Rule | Enforcement |
|------|-------------|
| Partial payment allowed | `amount_paid <= remaining_amount` (or policy warning only) |
| No salary mutation | No writes to `employees` pay fields |
| No pontaj mutation | No calls to attendance event APIs |
| No debt auto-close | No balance transaction creation on save |
| No compensation profiles | N/A — not in repo |
| No fiscal payroll | No tax/gross/net fields |
| Default status | `confirmed` (or `draft` if operator workflow added later) |

**Response:** created record + optional embedded slot summary.

**Follow-up:** UI refetches `GET /situation` (or PATCH response includes updated slot).

### `POST /api/v1/employee-payments/{id}/cancel` (optional same build)

- Sets `status = cancelled`
- Does not delete row; does not adjust balances

---

## 5. Calculation rules (proposed — server-side)

Mirror demo logic in `generatePaymentRunForEmployees` / `employeePaymentSituationDemo.ts` but with live inputs:

1. **Pay base:** `monthly_internal_pay_amount` from employee profile (**new field — see gap below**).
2. **Slot gross share:** `base_slot = monthly_internal_pay_amount * 0.5` per tranșă.
3. **Attendance adjustment:** prorate by **slot period** working days using attendance service logic on clipped date range.
4. **Overtime:** overtime hours in period × hourly rate × multiplier (1.5 in demo).
5. **Advances/debts deduction (suggested, not settled):** read-only suggestion from active balance / retention lines — **display only** unless owner defines auto-retention policy later.
6. **Expected slot** = `max(0, base_slot - attendance_adj + overtime - suggested_retention)` (exact formula locked in implementation build + tests).
7. **Paid** = sum non-cancelled `amount_paid` for employee/year/month/slot.
8. **Remaining** = `max(0, expected - paid)`.
9. **Monthly aggregates** = slot15 + slot30 for summary cards.

**Demo gaps to fix in live calc:**

- Attendance currently full-month for both slots — must split 1–15 / 16–end.
- Demo `bonusuri` index heuristic — drop or replace with explicit policy.
- Demo uses fake advances — replace with balance ledger rules.

---

## 6. Mutation rules (write boundary)

**Payments page may write:**

- `employee_internal_payment_records` (create; optional cancel).

**Payments page may NOT write:**

- `employees` (including `cost_lunar_firma`)
- `employee_attendance_events`
- `employee_balance_transactions`
- CostEngine config, quotes, inventory, any fiscal export

---

## 7. Explicit out-of-scope boundary

| Forbidden | Notes |
|-----------|-------|
| CostEngine | No labour cost aggregates as pay base |
| SmartBill | No invoice/fiscal export |
| Fiscal payroll | No gross/net legal salary, taxes, contributions |
| Salary configuration on Payments | Edit on `/employees` only |
| Attendance mutation | `/attendance` only |
| Debt auto-close | Payment save does not create `repayment` transactions |
| Compensation profiles | Rolled back; not in tree |
| `cost_lunar_firma` as payment base | Company cost ≠ internal pay tranșă |
| schedule-preview API | Rejected WIP |

---

## 8. What exists vs missing

| Capability | Status |
|------------|--------|
| Live employee list + profile API | **Exists** |
| Dedicated internal pay base field | **Missing** — blocker for correct live calc |
| Live attendance month summary | **Exists** — needs period split for slots |
| Live balance summary | **Exists** |
| Payment recordings persistence | **Missing** |
| Situation aggregation endpoint | **Missing** |
| Frontend wiring off demo module | **Missing** (`usePersonalDemoModule` + `employeePaymentSituationDemo`) |

---

## 9. Next build scope (implementation)

**Build name suggestion:** `BUILD_PERSONAL_EMPLOYEE_PAYMENTS_LIVE_WIRING`

1. **Profile field decision** — add `monthly_internal_pay_amount` (or owner-approved mapping policy) + Employees UI field separate from `cost_lunar_firma`.
2. **Migration `s49`** — `employee_internal_payment_records` table only (no compensation profiles).
3. **Service** — `employee_payment_situation_service.py` composing employees + attendance + balances + records.
4. **Router** — `GET /situation`, `POST /` (+ optional cancel).
5. **Tests** — pytest for calc, partial pay, cancel exclusion, boundary (no side effects on balances/attendance).
6. **Frontend** — replace demo builder with API hook; keep master-detail UI; refetch after save.

**Not in that build:** global UI polish, fiscal payroll, CostEngine changes, loan auto-settlement.

---

## 10. Related documents

| Document | Role |
|----------|------|
| `PERSONAL_EMPLOYEE_PAYMENTS_SCREEN_CONTRACT.md` | UI responsibility |
| `BUILD_PERSONAL_EMPLOYEE_PAYMENTS_FIGMA_UI_IMPLEMENTATION.md` | Committed UI behavior |
| `BUILD_PERSONAL_ATTENDANCE_EVENTS_FOUNDATION.md` | Pontaj API |
| `BUILD_PERSONAL_ADVANCES_DEBTS_FOUNDATION.md` | Balances API |
| `WORKOS_UI_POLISH_STRATEGY.md` | Page-scoped frontend wiring only |

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| No internal pay base field | Implement profile field **before** or **with** live calc; do not silently use `cost_lunar_firma` |
| Full-month attendance on both slots | Period-split service + tests |
| `settled` balances still in `active_balance` | Document in UI label; optional filter `status=active` for deduction suggestion |
| Double data fetching on frontend | Single situation endpoint |
| Reintroducing rejected WIP | Archive patches local-only; charter references screen contract |

---

## 12. Recommendation

**Sequence:**

1. **First:** profile pay base field + Employees UI (`monthly_internal_pay_amount`) — small schema + router field exposure.
2. **Then:** payment records migration + situation service + POST + frontend wire.

Skipping step 1 forces a policy violation (`cost_lunar_firma`) or continued demo fallbacks.

**Do not** implement full backend in audit build — this document only.
