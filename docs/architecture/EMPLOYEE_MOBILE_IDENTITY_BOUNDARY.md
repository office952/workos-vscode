# Employee Mobile Identity Boundary

## 1. Purpose

Define how WorkOS binds an **authenticated user** to an **operational employee record** so the Employee Mobile Portal can enforce **self-only** data access — before any live wiring to attendance, balances, payments, or tasks.

This document is **decision + architecture**. The **Employee Request Foundation** build (see §14) implements resolver, role gate, and self-only request endpoints; frontend shell remains MOCK except Cereri placeholder status.

Related: [`EMPLOYEE_MOBILE_PORTAL_BLUEPRINT.md`](./EMPLOYEE_MOBILE_PORTAL_BLUEPRINT.md)

---

## 2. Current auth findings

| Question | Finding |
|----------|---------|
| User model exists? | **Yes** — `backend/models/auth.py` → `users` table |
| User schema | `id` (OIDC sub, PK), `email`, `name`, `role`, `last_login` |
| Auth mechanism | OIDC login → app JWT in HttpOnly `app_token` cookie (+ optional Bearer) |
| `get_current_user` | **Yes** — `dependencies/auth.py` decodes JWT → `UserResponse` |
| Dev bypass | **Yes** — synthetic `dev-admin-user` with `role=admin` when `dev_auth_allowed()` |
| RBAC roles (effective) | `admin`, `manager`, `sales`, `operator`, `viewer` via `dependencies/permissions.py` |
| JWT `role` claim | Stored on user; legacy `user` maps to `admin` (dev) or `viewer` (prod) |
| `employee_mobile` role | **Implemented** in `VALID_ROLES`; self routes use `require_employee_mobile_self` |
| Permissions matrix | Quote/order/execution/inventory/employee CRUD — **no** `employee_mobile.*` keys |
| User ↔ Employee on `users` | **No** `employee_id` column on `users` |
| CSRF | Cookie auth requires CSRF header on mutating requests |

**Gap:** authentication proves **who logged in**, not **which employee** they are. Dev bypass returns admin — unsafe for mobile HR testing without explicit employee persona.

**Owner/admin note:** Users with `admin` or `manager` JWT roles may also require a linked `employees` row (`employees.user_id`) for Employee Mobile self flows. Owner employee records are **operational identity**, not payroll records. See `OWNER_EMPLOYEE_IDENTITY_BOOTSTRAP_DECISION.md`.

---

## 3. Current employee model findings

Table: `employees` (`backend/models/employees.py`)

| Field | Notes |
|-------|--------|
| `id` | Integer PK — canonical operational employee id |
| `name`, `role`, `department`, `status` | Operational HR fields |
| `employee_type` | productive / indirect / administrative / management |
| **`user_id`** | **Optional** `String(255)` — comment: link to `users.id` (OIDC sub) |
| `cost_lunar_firma` | **CostEngine sensitive** — must never appear on mobile |
| `monthly_internal_pay_amount` | Internal pay base — mobile may show derived payment summaries only in later phase |
| `ore_*`, skills, machines | Cost/ops metadata |
| Email / phone on employee | **Not present** as dedicated unique columns |
| `employee_id` on `users` | **Not present** |

**API exposure:** `/api/v1/entities/employees` CRUD includes `user_id` in payload; lists all employees with cost fields to any authenticated user with route access.

**Confusion risk:** three concepts overlap:

- **User** — login identity (OIDC)
- **Employee** — operational registry + CostEngine labour source
- **Operator** — RBAC role for task actions (not a separate table)

Tablet/operator flows pick `employee_id` in UI without binding to logged-in user.

---

## 4. Core identity rule

> **Employee Mobile Portal MUST NOT treat client-supplied `employee_id` as an access authority.**

Including: query params, JSON body fields, URL path segments, or localStorage selections on production mobile routes.

**Correct pattern:**

```text
authenticated_user.id  →  resolve employee row  →  enforce self-only filters server-side
```

**Resolver (implemented — `services/employee_mobile_identity.py`):**

```python
async def resolve_employee_for_user(db, current_user: UserResponse) -> ResolvedEmployee:
    # employees.user_id == current_user.id; 0 → 403, 2+ → 409, inactive → 403
```

If resolution fails → **403/409**, not empty mock data and not fallback to employee #1.

---

## 5. Role model

| Role | Mobile portal intent |
|------|----------------------|
| `employee_mobile` | **New** — self-only read + create requests |
| `team_lead_mobile` | **New** — self + explicit team roster (future) |
| `operator` | Existing — shop/tablet task actions; **not** a substitute for employee_mobile |
| `manager` | Approvals via manager/admin routes, not employee-self namespace |
| `admin` | Full ERP; never routed through `/employee-mobile/*` for bulk HR |

**MVP decision:** introduce `employee_mobile` in JWT + permission matrix before any live HR wiring. Until then, portal stays MOCK SHELL.

**Team lead:** requires explicit `team_id` / reporting structure — **deferred**; do not infer from department string alone.

---

## 6. Self-only access rules

1. Every `GET /employee-mobile/*` handler calls `resolve_employee_for_user` once.
2. SQL filters use resolved `employee.id` only — never client `employee_id`.
3. `POST /employee-mobile/requests` sets `employee_id` from resolver; body may include request type/payload only.
4. Mutations to attendance ledger, balance transactions, payment records remain **manager/admin** paths until request approval workflow exists.
5. Task status updates use existing `operator.task_action` permissions **plus** employee match guard (assigned employee_id == resolved id).
6. Fail-closed: inactive employee (`status != active`) → read-only or 403 for mutations.

---

## 7. Forbidden access (employee mobile)

Never expose via employee-self routes:

| Category | Examples |
|----------|----------|
| Colleague HR | Other employees' attendance, balances, payments |
| CostEngine | `cost_lunar_firma`, `cost_ora_calculat`, `valid_for_cost_engine` |
| Commercial | Quote totals, margins, client pricing |
| Fiscal payroll | Tax, contributions, official payslips |
| Admin aggregates | `/employee-payments/situation` full grid |
| Workforce-wide summaries | Month attendance summary for all employees |

---

## 8. API boundary rules

### Employee-self namespace (future)

Prefix: `/api/v1/employee-mobile/`

- **No** `employee_id` query param for self access
- **No** reuse of admin list endpoints
- Response DTOs are **redacted projections** (no cost engine fields)

### Manager / admin namespace (existing + future)

- `/api/v1/entities/employees`, `/employee-attendance/*`, `/employee-balances/*`, `/employee-payments/*`
- Explicit `{employee_id}` allowed **only** with `manager`/`admin` permission checks
- Never called from `/employee-app` mobile shell in employee role

### Anti-patterns (current codebase — do not wire to mobile)

| Endpoint | Problem |
|----------|---------|
| `GET /employee-attendance/events?employee_id=` | Client chooses employee |
| `GET /employee-balances/transactions?employee_id=` | Client chooses employee |
| `GET /employee-payments/situation` | Returns all employees + salary fields |
| `GET /entities/employees` | Full roster + CostEngine |
| `GET /operator/tasks` | All tasks; `mine` still query-param driven |

---

## 9. Data exposure matrix

Legend: **RS** = READ SELF · **RT** = READ TEAM · **RA** = READ ALL · **CSR** = CREATE SELF REQUEST · **UOF** = UPDATE OWN FIELD STATUS · **F** = FORBIDDEN

| Area | Employee self | Team lead | Manager | Admin | Public |
|------|---------------|-----------|---------|-------|--------|
| **Profile** | RS (name, dept, role, status) | RT basic roster | RA | RA | F |
| **Today** | RS aggregated dashboard | RT team summary | RA ops view | RA | F |
| **My Tasks** | RS assigned | RT team queue | RA | RA | F |
| **Installations** | RS assigned jobs | RT crew jobs | RA | RA | F |
| **Attendance** | RS own calendar; CSR correction/leave | RT team calendar read | RA edit events | RA | F |
| **Requests** | RS own; CSR create | RT team inbox (future) | RA approve | RA | F |
| **Balances** | RS own summary + own ledger rows | F (unless policy) | RA | RA | F |
| **Payments** | RS own confirmed payments/slots | F | RA situation grid | RA | F |
| **Notes** | RS notes to self | RT team notes | RA | RA | F |

**Attendance rule:** employee self may **not** POST direct `attendance/events` for approved periods — only **requests** until manager approval (Phase 2).

**Payments rule:** employee self sees **confirmed** internal payments only; no suggested deduction engine internals, no colleague rows.

**Tasks rule:** UOF (start/complete) only when task assignment matches resolved employee_id and role permits.

---

## 10. Proposed schema options

### Option A — `users.employee_id` FK

Add nullable `employee_id` on `users`.

| Pros | Cons |
|------|------|
| Fast lookup from auth | Duplicate link if `employees.user_id` also set |
| Clear direction from session | Migration + backfill |

### Option B — `user_employee_links` table

| Pros | Cons |
|------|------|
| Multi-firm / multi-hat future | More joins |
| Audit history of link changes | Heavier MVP |

### Option C — Email/phone matching

| Pros | Cons |
|------|------|
| No migration for demo | **Unacceptable** as runtime access boundary |
| | Collision risk; not fail-closed |

### Option D — **Use existing `employees.user_id` (recommended MVP)**

**Link already exists on employee row:** `employees.user_id → users.id`.

| Pros | Cons |
|------|------|
| **No migration required** for column existence | Lookup is reverse (query employees by user_id) |
| Single source of truth on operational record | Must enforce unique index on `employees.user_id` (one employee per user) |
| Admin sets link via existing employee CRUD | Nullable today — many employees unlinked |

**Verdict:** **Option D for MVP resolver** + optional **Option A mirror** later for performance only.

**Do not use Option C at runtime.** Admin UI may suggest link candidates by email match as **helper only**, never auto-grant access.

**Migration needed later (separate build):**

- Unique partial index on `employees.user_id WHERE user_id IS NOT NULL`
- Backfill script for production employees (admin operation)
- **Not in this build**

---

## 11. Recommended MVP decision

1. **Identity link:** resolve employee via `employees.user_id = current_user.id`.
2. **New role:** add `employee_mobile` to JWT + `PERMISSION_MATRIX` before live data.
3. **New router namespace:** `/api/v1/employee-mobile/*` with resolver middleware — never attach existing HR list endpoints to mobile shell.
4. **Portal gating:** `/employee-app` shows MOCK SHELL until resolver returns employee **and** role is `employee_mobile` (or dev impersonation flag for local QA only).
5. **Dev safety:** dev bypass must not silently load real HR; require explicit `DEV_EMPLOYEE_USER_ID` env for mobile QA if needed.

---

## 12. Open questions

1. One user → one employee enforced globally, or exceptions for admin impersonation?
2. How to link shop-floor shared tablet users (PIN vs individual login)?
3. When employee leaves (`status=inactive`), revoke link automatically?
4. Team lead roster source — HR hierarchy table vs workcenter assignment?
5. Should `operator` role automatically imply `employee_mobile`, or separate assignment?
6. Redacted payment DTO — which fields from `monthly_internal_pay_amount` / slots are employee-safe?

---

## 13. Implemented foundation (Employee Request Foundation build)

| Component | Location | Notes |
|-----------|----------|-------|
| Resolver | `backend/services/employee_mobile_identity.py` | `employees.user_id`; fail-closed |
| Role gate | `backend/dependencies/employee_mobile.py` | `EMPLOYEE_SELF_ACCESS_ROLES`: mobile + manager + admin with link |
| Model | `backend/models/employee_request.py` | `employee_requests` via `create_all` |
| Service | `backend/services/employee_request_service.py` | No attendance/payment side effects |
| Router | `backend/routers/employee_mobile_requests.py` | `/api/v1/employee-mobile/requests` |
| Tests | `backend/tests/test_employee_mobile_requests.py` | Cross-employee + role security |

**Self-only endpoints (live):**

```text
GET    /api/v1/employee-mobile/requests
POST   /api/v1/employee-mobile/requests
GET    /api/v1/employee-mobile/requests/{request_id}
PATCH  /api/v1/employee-mobile/requests/{request_id}/cancel
```

**Deferred (partially addressed in Manager Review build):**

- ~~Manager approval / reject routes~~ → live at `/api/v1/employee-requests/review` (status only)
- Attendance event creation on approve
- Payment/advance ledger on approve
- Unique DB index on `employees.user_id`

QA log: [`../qa/BUILD_EMPLOYEE_REQUEST_FOUNDATION.md`](../qa/BUILD_EMPLOYEE_REQUEST_FOUNDATION.md)

---

## 14. Dual context — self app vs manager review (Manager Review build)

**Owner rule:** Managers use the **self app** for own requests when linked via `employees.user_id`. They use **review routes** only for others' requests. They must **not** approve their own request.

| Context | Prefix | Roles | Identity |
|---------|--------|-------|----------|
| Employee self app | `/api/v1/employee-mobile/` | `employee_mobile`, `manager`, `admin` | `resolve_employee_for_user` |
| Manager review | `/api/v1/employee-requests/review` | `admin`, `manager` | No client `employee_id`; self-approval blocked |

**Review endpoints (status-only, no side effects):**

```text
GET   /api/v1/employee-requests/review
GET   /api/v1/employee-requests/review/{request_id}
PATCH /api/v1/employee-requests/review/{request_id}/approve
PATCH /api/v1/employee-requests/review/{request_id}/reject
```

- Approve/reject only when `status=submitted`
- Sets `reviewed_at`, `reviewed_by_user_id`, `review_note` server-side
- No attendance events, no payment/advance ledger, no payroll exposure

QA log: [`../qa/BUILD_EMPLOYEE_REQUEST_MANAGER_REVIEW.md`](../qa/BUILD_EMPLOYEE_REQUEST_MANAGER_REVIEW.md)

---

## 15. Next build plan

**Build:** `Employee Request Manager Review UI` or `Attendance hook after approval` (separate gated builds)

Sequence:

1. Manager review UI wired to `/api/v1/employee-requests/review`
2. Optional notifications on approve/reject
3. **Still no** attendance/payment ledger until dedicated approval-integration build

---

## Appendix A — Sensitive endpoint classification

### Employees

```text
Area: Employees
Existing endpoints: GET/POST/PUT/DELETE /api/v1/entities/employees
Data sensitivity: HIGH (cost_lunar_firma, full roster)
Self-only possible now: NO — list endpoint
Needs user->employee_id: YES (resolver)
Needs role permission: employee CRUD = admin/manager only
Allowed for employee mobile: NONE (use /employee-mobile/me projection)
Forbidden for employee mobile: ALL current CRUD/list
Notes: employees.user_id writable today via admin API — use for linking
```

### Attendance

```text
Area: Attendance
Existing endpoints: GET summary (all), GET/POST/PUT/DELETE events
Data sensitivity: HIGH (workforce-wide)
Self-only possible now: NO — optional employee_id is client-controlled
Needs user->employee_id: YES
Needs role permission: manager/admin for direct edits
Allowed for employee mobile: future read-self + request-only create
Forbidden for employee mobile: summary all-hands, POST events with arbitrary employee_id
```

### Advances / Balances

```text
Area: Balances
Existing endpoints: GET summary (all), GET/POST transactions
Data sensitivity: HIGH (ledger, amounts)
Self-only possible now: NO
Needs user->employee_id: YES
Allowed for employee mobile: future read-self summary + own transactions
Forbidden: workforce summary, POST transactions from mobile self
```

### Payments

```text
Area: Payments
Existing endpoints: GET situation (all employees + salary), POST records
Data sensitivity: CRITICAL
Self-only possible now: NO
Allowed for employee mobile: future read-self confirmed history only
Forbidden: situation grid, salary_monthly fields of others
```

### Tasks / Execution

```text
Area: Tasks
Existing endpoints: GET /operator/tasks, POST task-action, execution plan/reality
Data sensitivity: MEDIUM (operational, may embed client/product names)
Self-only possible now: PARTIAL — assignment exists but not auth-bound
Allowed for employee mobile: read assigned; update with guard
Forbidden: all tasks, order commercial internals, costing
```

### Installations / Montaj

```text
Area: Installations
Existing endpoints: execution reality, tablet station queues (partial)
Data sensitivity: MEDIUM
Self-only possible now: NO dedicated install API
Allowed: read assigned field job projection
Forbidden: profit/cost, unrelated orders
```

### Requests / Leave

```text
Area: Requests
Existing endpoints: NONE dedicated
Data sensitivity: LOW-MEDIUM
Self-only possible now: N/A — build new
Allowed: CREATE SELF REQUEST, READ SELF
Forbidden: approve without manager role
```

---

## Appendix B — Future employee-mobile API (document only)

```text
GET  /api/v1/employee-mobile/me
GET  /api/v1/employee-mobile/today
GET  /api/v1/employee-mobile/tasks
GET  /api/v1/employee-mobile/installations
GET  /api/v1/employee-mobile/attendance
GET  /api/v1/employee-mobile/requests
POST /api/v1/employee-mobile/requests
GET  /api/v1/employee-mobile/balances
GET  /api/v1/employee-mobile/payments
GET  /api/v1/employee-mobile/notes
```

Manager/admin lookups (separate):

```text
GET /api/v1/manager/employees/{employee_id}/...
GET /api/v1/admin/employees/{employee_id}/...
```
