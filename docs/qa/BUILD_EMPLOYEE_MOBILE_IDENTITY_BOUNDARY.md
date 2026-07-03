# BUILD — Employee Mobile Identity Boundary

## Status

**Implementation: NOT EXECUTED** — audit + architecture decision only.

No backend runtime changes. No DB migration. No live wiring.

## Purpose

Define user → employee identity boundary and self-only access rules before connecting Employee Mobile Portal to real HR/ops data.

## Prerequisite HEAD

`dff0700` — `feat(employee): add mobile portal shell blueprint`

---

## TASK 0 — Precheck

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` ✅ |
| HEAD | `dff0700` ✅ |
| Working tree | clean ✅ |
| `Co-authored-by` | absent ✅ |

---

## TASK 1 — Auth audit summary

| Finding | Detail |
|---------|--------|
| User model | `users` — id (OIDC sub), email, name, role |
| Auth | OIDC + JWT cookie; `get_current_user` ✅ |
| Dev bypass | Synthetic admin user in dev |
| RBAC | `admin/manager/sales/operator/viewer` — no `employee_mobile` |
| User → Employee on users | **Missing** (`users.employee_id` absent) |
| Gap | Auth proves login, not employee identity |

---

## TASK 2 — Employee model audit summary

| Finding | Detail |
|---------|--------|
| Table | `employees` with operational + CostEngine fields |
| **Link exists** | **`employees.user_id` → `users.id`** (nullable, optional) |
| Unique email/phone on employee | **No** dedicated columns |
| Active status | `status` field ✅ |
| Confusion risk | User vs Employee vs operator role |

---

## TASK 3 — Sensitive endpoints summary

| Area | Self-only today? | Blocker |
|------|------------------|---------|
| Employees CRUD | No | Cost fields + roster |
| Attendance | No | Client `employee_id` param |
| Balances | No | All-employee summary |
| Payments | No | Situation returns all + salary |
| Tasks | Partial | Not auth-bound to user |
| Installations | No | No dedicated API |
| Requests | N/A | Not built |

**Verdict:** wiring current endpoints to mobile = **data leak**. New `/employee-mobile/*` namespace required.

---

## TASK 4–7 — Identity decision

**Document created:** `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md`

### Core rule

Client `employee_id` is **never** access authority. Backend resolves employee from authenticated user.

### Schema recommendation

**Option D (MVP):** use existing **`employees.user_id`**.

- No migration required for column existence
- Later: unique index + backfill (separate build)
- **Reject** email/phone runtime matching (Option C)
- Optional future mirror: `users.employee_id` (Option A) — not MVP blocker

### API boundary

- Employee-self: `/api/v1/employee-mobile/*` — no client employee_id
- Manager/admin: existing routes with explicit permissions

### Role model

Add `employee_mobile` (and later `team_lead_mobile`) before live HR wiring.

---

## TASK 8 — TypeScript constants

**Skipped** — documentation sufficient; no runtime wiring needed.

---

## TASK 9 — Files changed

| File | Change |
|------|--------|
| `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md` | **New** |
| `docs/qa/BUILD_EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md` | **New** |

---

## TASK 10 — Tests

**N/A** — docs only.

---

## TASK 11 — Runtime smoke

**N/A** — no runtime changes. Existing `/employee-app` shell unchanged at `dff0700`.

---

## Boundaries confirmed

- no DB migration
- no backend runtime changes
- no live attendance/payment/task wiring
- no payroll fiscal
- no CostEngine exposure path
- no quote/pricing/margins
- no sensitive data exposure

---

## Risks

1. `employees.user_id` nullable — most rows unlinked today
2. Dev auth bypass returns admin — unsafe for mobile HR testing
3. Existing HR APIs allow cross-employee reads for any authenticated ERP user
4. Operator tablet picks employee_id in UI without user binding

## Open questions

See architecture doc §12 (shared tablets, inactive employees, team lead roster, operator vs employee_mobile roles).

## Recommended next build

**Employee Request Foundation — self-only request model**

1. `resolve_employee_for_user` service + tests
2. `employee_mobile` role + permissions
3. `employee_requests` model/router
4. Optional unique index migration (owner-approved)

## Recommended commit message

```text
docs(employee): define mobile identity boundary
```

## READY / NOT READY

**READY** for manual `commit-tree` (2 doc files only).

---

## Owner decision hint

Proceed with **docs commit** now. Do **not** start backend migration until owner confirms:

- one user ↔ one employee policy
- link backfill approach via `employees.user_id`
