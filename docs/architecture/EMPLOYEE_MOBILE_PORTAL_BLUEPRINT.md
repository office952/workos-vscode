# Employee Mobile Portal — Architecture Blueprint

## 1. Purpose

Define a **mobile-first, employee-scoped mini-application** inside WorkOS for shop-floor and field staff. Each authenticated employee sees only their own operational context: tasks, installations, attendance, internal requests, balances, and confirmed internal payments — without ERP admin surfaces, commercial pricing, or fiscal payroll.

This document is the product + technical boundary for phased delivery. It does **not** authorize backend schema changes or production data wiring without a follow-up build.

## 2. Non-goals

- Fiscal payroll, tax declarations, official accounting documents
- Native Android/iOS apps (PWA / responsive web only for MVP)
- Salaries or balances of **other** employees
- Quote pricing, margins, profit, CostEngine configuration
- Client commercial data, intake internals, inventory admin
- Full HR legal dossier management
- Replacing admin pages (`/employees`, `/attendance`, `/employee-payments`) for managers
- Mock fallback in real employee flows once live auth exists

## 3. User roles

| Role | Scope |
|------|--------|
| `employee_mobile` | Own tasks, attendance read, own requests, own balances/payments read-only, field notes |
| `team_lead_mobile` | Own data + team queue visibility (read-only first), approve simple field updates later |
| `manager` | Existing WorkOS manager RBAC; approves employee requests via admin/manager UI |
| `admin` | Full ERP; not a target user of employee portal |

**Current gap:** JWT roles are `admin | manager | sales | operator | viewer` (+ legacy `user`). There is **no** `employee_mobile` role and **no** `users.employee_id` link in `models/auth.py`.

## 4. Mobile app areas

| Area | Employee value |
|------|----------------|
| **Today** | Schedule snapshot, punch status, tasks due, installations today, alerts |
| **My Tasks** | Assigned operator/execution tasks; status updates (later build) |
| **Installations / Montaj** | Site, crew, checklist, materials, field status, photos (later) |
| **Attendance** | Own pontaj view; leave / day-off / time-off / correction **requests** |
| **Requests** | Generic employee request inbox + submit |
| **Balances** | Own internal ledger read-only; advance **request** |
| **Payments** | Own confirmed internal payments read-only (not fiscal) |
| **Notes** | Manager notes, task observations, announcements (read-first) |

## 5. Data access rules

1. **Self-scope only:** every query filtered by `authenticated_user.employee_id`.
2. **Fail-closed:** missing link user → employee ⇒ no HR/payment data (shell only).
3. **Read before write:** Phase 1–5 read-only; mutations only via approved request workflow or explicit task-action permissions.
4. **No aggregate HR exports** from mobile routes.
5. **Attribution:** created requests/events store `employee_id` + `created_by_user_id`.

## 6. Security boundaries

| Surface | Current state | Employee portal rule |
|---------|---------------|----------------------|
| `/api/v1/entities/employees` | Lists all employees; exposes `cost_lunar_firma`, CostEngine fields | **Block** for mobile; need `/me` subset without cost fields |
| `/api/v1/employee-attendance/*` | Any authenticated user; optional `employee_id` filter | **Must enforce** self-scope on mobile |
| `/api/v1/employee-balances/*` | Any authenticated user; all employees | **Must enforce** self-scope |
| `/api/v1/employee-payments/situation` | Returns **all** employees + salary hints | **Never** expose raw situation to mobile |
| `/api/v1/operator/tasks` | All tasks | Need `/mine?employee_id=` with server-side filter |
| `/api/v1/execution/*` | Order-level; manager/operator roles | Field/install views need order task subset only |

**Risk if we wire current endpoints without scoping:** any logged-in operator/admin token can read every employee's attendance, balances, and payment situation.

## 7. Module map

### Existing WorkOS foundations (reuse)

| Layer | Asset | Notes |
|-------|-------|-------|
| Frontend HR admin | `/employees`, `/employees-records`, `/attendance`, `/employee-payments`, `/employee-advances` | Manager-facing; live APIs |
| Frontend ops | `/operator`, `/tablet/*`, `/shop-floor`, `/execution/*` | Task + montaj partial |
| Hooks/API | `useEmployeeAttendance`, `useEmployeeBalances`, `useOperatorData`, `useTabletStationData` | Live; not employee-scoped |
| Backend | `employee_attendance`, `employee_balances`, `employee_payments`, `operator_tasks`, `execution`, `employees` | Live; auth = `get_current_user` only |
| Design system | `SourceBadge`, `StatusBadge` | Reuse for portal chrome |
| Auth | OIDC + app JWT cookie; RBAC in `dependencies/permissions.py` | No employee link |

### New portal modules (to build)

| Module | Route | Depends on |
|--------|-------|------------|
| Portal shell | `/employee-app` | None (Phase 1) |
| Today | `/employee-app/today` | employee_id + tasks + attendance summary |
| Tasks | `/employee-app/tasks` | operator tasks mine |
| Installations | `/employee-app/installations` | execution reality / montaj model |
| Attendance | `/employee-app/attendance` | attendance events self |
| Requests | `/employee-app/requests` | `employee_requests` table (new) |
| Balances | `/employee-app/balances` | balance summary self |
| Payments | `/employee-app/payments` | payment history self |
| Notes | `/employee-app/notes` | announcements + task notes |

## 8. MVP phases

### Phase 1 — Shell mobile read-only ✅ (this build scope)

- Route `/employee-app` + section placeholders
- `MOBILE SHELL` badge; static/mock identity for dev preview only
- No backend mutation; no real employee PII

### Phase 2 — Employee Request Foundation

- DB model `employee_requests` (type, status, payload JSON, employee_id, approver)
- Backend CRUD + manager approval endpoints
- Mobile: submit leave/day_off/time_off/advance/correction requests
- Attendance integration **only after approval** (no direct event create from mobile)

### Phase 3 — My Attendance (read-only)

- `GET /api/v1/employee-mobile/me/attendance` (scoped)
- Mobile calendar + month summary for self only

### Phase 4 — My Tasks / Installations

- `GET .../me/tasks` wrapping operator task query filtered by employee assignment
- Read-only installation cards from execution/reality
- Task status mutations gated by `operator.task_action` + employee match

### Phase 5 — Balances / Payments read-only

- Scoped summaries without colleague data or CostEngine rates
- Payment history: confirmed records only; strip suggested deductions from employee view if sensitive

### Phase 6 — Field Reality

- Photo upload (storage permissions), geo optional, completion notes
- Links to `execution.reality` with employee attribution

**Build first:** **Phase 1** (shell) — zero security debt.  
**Build second:** **Phase 2** (requests) — unlocks attendance corrections and leave flow safely.

## 9. API requirements (future)

| Endpoint | Method | Scope | Phase |
|----------|--------|-------|-------|
| `/api/v1/employee-mobile/me` | GET | Profile stub (name, role, workcenter) | 2 |
| `/api/v1/employee-mobile/me/attendance/summary` | GET | Self month summary | 3 |
| `/api/v1/employee-mobile/me/attendance/events` | GET | Self events range | 3 |
| `/api/v1/employee-mobile/me/requests` | GET/POST | Self requests | 2 |
| `/api/v1/employee-mobile/me/tasks` | GET | Self assigned tasks | 4 |
| `/api/v1/employee-mobile/me/balances` | GET | Self ledger summary | 5 |
| `/api/v1/employee-mobile/me/payments` | GET | Self payment history | 5 |
| `/api/v1/manager/employee-requests` | GET/PATCH | Manager approval queue | 2 |

All mobile routes require `employee_mobile` or mapped role + verified `employee_id`.

## 10. UI route proposal

```
/employee-app                    → home / section index
/employee-app/today
/employee-app/tasks
/employee-app/installations
/employee-app/attendance
/employee-app/requests
/employee-app/balances
/employee-app/payments
/employee-app/notes
```

Layout: mobile-first column, bottom nav (later), no ERP sidebar in dedicated layout (future refactor).

## 11. Sensitive data rules

**Never show on employee mobile:**

- `cost_lunar_firma`, `cost_ora_calculat`, `valid_for_cost_engine`
- Colleague salaries, balances, attendance
- Quote totals, markup, client commercial terms
- Inventory costs, workcenter rates
- Full payment situation grid (manager view)

**Allowed (self, read-only, later phases):**

- Name, workcenter, shift, task assignments
- Own attendance exceptions (approved/confirmed)
- Own balance totals and transaction types (not colleague rows)
- Own paid internal payment amounts (labelled non-fiscal)

## 12. Open questions

1. **User ↔ Employee link:** add `users.employee_id` FK or separate mapping table?
2. **Login model:** same OIDC users for everyone, or PIN/QR for shared shop tablets?
3. **Team lead scope:** which tasks/installations visible for crew vs self only?
4. **Installation entity:** reuse execution order + reality, or new `field_jobs` aggregate?
5. **Request approval SLA:** manager-only vs team_lead for time-off?
6. **PWA:** installable manifest + offline shell — when?
7. **Language:** RO-only for MVP?

---

## Appendix — Reuse vs risky pages (audit summary)

| Page | Live/Demo | Mobile reuse |
|------|-----------|--------------|
| `Employees.tsx` | Live + CostEngine fields | **Do not reuse** — admin |
| `Attendance.tsx` | Live all-employee | Patterns only; not component reuse |
| `EmployeePayments.tsx` | Live all-employee | Patterns only |
| `EmployeeAdvances.tsx` | Live all-employee | Patterns only |
| `OperatorView.tsx` | Live/mock tasks | Task card patterns |
| `TabletMode.tsx` | Live station queue | Montaj/task UX reference |
| `Personal.tsx` | Demo/mock HR roster | **Do not reuse** for auth employee identity |
