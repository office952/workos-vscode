# BUILD — Employee Mobile Portal Blueprint + Shell Foundation

## Status

**Phase A–D executed** — audit, blueprint, frontend shell, static HTML mock.  
**No backend / DB / migration changes.**

## Purpose

Define and bootstrap `Employee Mobile Portal` — a mobile-first employee-scoped mini-app — without exposing sensitive HR/commercial data or building fiscal payroll.

## Prerequisite HEAD

`0f2c760` — `docs(design): document source badge next pilot decision`

## Scope

### In scope

- Read-only audits (frontend routes, backend endpoints, auth model)
- Architecture blueprint
- MVP phase plan
- Frontend shell at `/employee-app` (static placeholders, MOCK SHELL)
- Static HTML concept mock for owner review
- Targeted tests for shell

### Out of scope (boundaries)

- Backend routers / services / models
- DB migrations
- CostEngine / quote pricing / margins
- Fiscal payroll
- Real employee data wiring
- New auth system
- Native mobile apps
- Mock fallback in real flows

---

## TASK 1 — Frontend audit findings

### Personal / HR admin pages (live)

| Route | Page | Data |
|-------|------|------|
| `/employees` | `Employees.tsx` | Live — CostEngine fields (`cost_lunar_firma`, `valid_for_cost_engine`) |
| `/employees-records` | `EmployeesRecords.tsx` | HR records |
| `/employees-records/:id` | `EmployeeProfile.tsx` | Profile |
| `/attendance` | `Attendance.tsx` | Live — all employees via `useEmployeeAttendance` |
| `/employee-payments` | `EmployeePayments.tsx` | Live — all employees situation |
| `/employee-advances` | `EmployeeAdvances.tsx` | Live — all employees ledger |

### Field / operator pages

| Route | Page | Reuse potential |
|-------|------|-----------------|
| `/operator` | `OperatorView.tsx` | Task list patterns |
| `/tablet/*` | `TabletMode.tsx` | Station queue, task detail, employee picker |
| `/shop-floor` | `ShopFloor.tsx` | Live machine overview |
| `/execution/*` | Execution dashboards | Order/reality (manager) |

### Hooks / API clients

- `useOperationalEmployees`, `useEmployeeAttendance`, `useEmployeeBalances`
- `useOperatorData`, `useOperatorEmployees`, `useTabletStationData`
- `employeeAttendance.ts`, `employeeBalances.ts`, `employeePayments.ts`, `employeesApi` (CostEngine)

### Demo vs live

- `Personal.tsx` — mock HR roster (redirects to `/employees`)
- Tablet/operator — mock fallback when `isMockEnabled()`
- Employee admin pages — **live**, no mock in production paths

### Mobile employee risk zones

- Any page listing **all** employees with salary/cost fields
- Payment situation grid (colleague amounts)
- Attendance month summary for entire workforce
- CostEngine employee API responses

---

## TASK 2 — Backend audit findings

### Routers present

| Router | Prefix | Employee portal relevance |
|--------|--------|---------------------------|
| `employees.py` | `/api/v1/entities/employees` | Admin CRUD; sensitive cost fields |
| `employee_attendance.py` | `/api/v1/employee-attendance` | Pontaj events + month summary |
| `employee_balances.py` | `/api/v1/employee-balances` | Ledger CRUD + summaries |
| `employee_payments.py` | `/api/v1/employee-payments` | Situation (all employees) + record CRUD |
| `operator_tasks.py` | `/api/v1/operator` | Tasks + task-action |
| `execution.py` | `/api/v1/execution` | Plans, reality, materials |
| `machines.py` | `/api/v1/machines` | Registry read |

### Gaps for Employee Mobile Portal

- No `/api/v1/employee-mobile/*` namespace
- No `employee_requests` model/router
- No `GET .../tasks/mine` scoped by authenticated employee (partial: query param exists but not auth-bound)
- No self-scoped attendance/balance/payment read endpoints
- No installation/field-job aggregate API for employees

### Too sensitive for direct mobile exposure

- `GET /employee-payments/situation` — all employees + salary_monthly
- `GET /employee-attendance/summary` — all employees
- `GET /entities/employees` — CostEngine labour costs
- Full `operator/tasks` without employee filter enforcement

---

## TASK 3 — Auth / role findings

| Question | Answer |
|----------|--------|
| Authentication | OIDC → app JWT in HttpOnly cookie; CSRF double-submit |
| User vs Employee | **Separate** — `users` table has no `employee_id` |
| Roles | `admin`, `manager`, `sales`, `operator`, `viewer` (+ legacy `user`) |
| Operator concept | Yes — permissions for task actions |
| Employee mobile role | **Missing** |
| Link user → employee | **Missing** — must be designed before real data |

**Security risk:** current HR/attendance/balance endpoints only require `get_current_user`; any authenticated ERP user can query other employees if UI allows `employee_id` param.

**Boundary decision:** this build creates blueprint + shell only; no real protected data.

---

## TASK 4–5 — Blueprint + MVP phases

Created: `docs/architecture/EMPLOYEE_MOBILE_PORTAL_BLUEPRINT.md`

**Build first:** Phase 1 — Shell (done in this build).  
**Build second:** Phase 2 — `employee_requests` foundation (requires owner approval — Option C later).

---

## TASK 6 — Frontend shell

Created:

- `frontend/src/pages/EmployeeMobileApp.tsx`
- `frontend/src/pages/EmployeeMobileApp.test.tsx`
- Route: `/employee-app/*` in `App.tsx`

Features:

- Header `WorkOS Employee` + `MOBILE SHELL` badge
- Disclaimer (no real employee data)
- 8 section cards with status pills
- Nested placeholder routes per blueprint
- Dev identity label `MOCK SHELL` only

---

## TASK 7 — HTML mock

Created: `docs/mockups/employee-mobile-portal.html`

- Static concept; tabbed screens (Today, Tasks, Requests, Attendance, Balances/Payments, Field)
- Fictional demo names only
- Header: `Concept mock — not runtime`

---

## TASK 8 — Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeMobileApp.test.tsx
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

| Suite | Result |
|-------|--------|
| `EmployeeMobileApp.test.tsx` | **3 passed** |
| `tsc -b --noEmit` | **FAIL** — 3 pre-existing errors (unrelated files) |

`tsc` errors remain in `QuoteCommercialActionPanel.badges.test.tsx`, `EmployeePayments.tsx`, `Pricing.badges.test.tsx`. **No errors** in `EmployeeMobileApp.tsx`, `EmployeeMobileApp.test.tsx`, or `App.tsx` route change.

---

## TASK 9 — Runtime smoke

Route: `/employee-app` — **PASS**

| Check | Result |
|-------|--------|
| Page loads | ✅ |
| Mobile layout (`max-w-lg`) | ✅ |
| `MOBILE SHELL` badge | ✅ |
| Disclaimer visible | ✅ |
| 8 section cards | ✅ |
| `MOCK SHELL` dev label | ✅ |
| Sensitive data | ✅ none |
| Console errors | ✅ none observed |

---

## Files changed

| File | Change |
|------|--------|
| `docs/architecture/EMPLOYEE_MOBILE_PORTAL_BLUEPRINT.md` | **New** |
| `docs/mockups/employee-mobile-portal.html` | **New** |
| `frontend/src/pages/EmployeeMobileApp.tsx` | **New** |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | **New** |
| `frontend/src/App.tsx` | Route registration only |
| `docs/qa/BUILD_EMPLOYEE_MOBILE_PORTAL_BLUEPRINT.md` | **New** |

---

## Risks

1. Wiring existing HR APIs without `employee_id` scoping → data leak
2. Confusing admin `/attendance` with employee portal
3. CostEngine fields in employee DTOs if reused blindly
4. Shared shop tablets need device/session policy (open question)

## Open questions

See blueprint §12 (user↔employee link, login model, team lead scope, installation entity, PWA).

## Recommended next build

**Phase 2 — Employee Request Foundation** (`employee_requests` model + scoped mobile API + manager approval).  
Do **not** start until owner picks Option B commit + approves auth linking design.

## Owner recommendation

**Option B — balanced:** commit blueprint + HTML mock + `/employee-app` shell (no real data).

## Recommended commit message

```text
feat(employee): add mobile portal shell blueprint
```

(alternate docs-only subset: `docs(employee): add mobile portal blueprint`)

---

## Boundaries confirmed

- no DB / migrations
- no backend changes
- no CostEngine / payroll fiscal / quote pricing
- no sensitive employee data in shell
- no mock fallback in real flows (shell is explicitly labelled MOCK)
