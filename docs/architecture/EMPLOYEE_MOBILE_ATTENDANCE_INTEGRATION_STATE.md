# Employee Mobile & Attendance — Integration State

## Status

| Item | Value |
|------|--------|
| **Status** | Current State / Integration Index |
| **Runtime impact** | none (index document) |
| **DB impact** | none |
| **Payroll impact** | none |

Last hardened audit: `BUILD_EMPLOYEE_MOBILE_ATTENDANCE_INTEGRATION_HARDENING_AUDIT.md`

## Operational generation closure

| Rule | Value |
|------|--------|
| Generate trigger | Explicit admin/operator HTTP — **not** on approve |
| Generate guard | `require_attendance_operator` |
| Payload | `employee_request_id` only — no client `employee_id` |
| Idempotent | Second POST returns `already_exists: true` (HTTP 200) |
| Conflict at generate | Effect row may be `conflict` (e.g. overlap, deferred types) — no attendance write |
| Deferred types | `time_off`, `attendance_correction` → conflict effect; apply still deferred |
| Skipped types | `advance`, `equipment`, etc. → HTTP 422 |
| Apply | Separate POST `/effects/{id}/apply` — unchanged |
| Attendance event | Created **only** on apply |

### Endpoints (generation)

| Method | Path | Role |
|--------|------|------|
| GET | `/api/v1/employee-attendance/effects/generation-candidates` | admin/operator |
| POST | `/api/v1/employee-attendance/effects/generate` | admin/operator |

## Current capabilities

| Capability | State | Notes |
|------------|-------|-------|
| Employee Mobile dashboard | Live | `/employee-app` — cards, summaries, bottom nav |
| Self requests | Live | Create/list/cancel; no client `employee_id` |
| Manager review | Live | Separate router; status-only approve/reject |
| Self attendance | Live | Read-only GET; server-resolved identity |
| PWA foundation | Live | `manifest.webmanifest` → `start_url: /employee-app` |
| Effects console | Live | `/attendance/effects` — candidates, generate, list, apply |
| Attendance access control | Live | CRUD + effects admin/operator only |
| Effects apply | Live | Manual POST apply; idempotent |
| Effect generation HTTP | Live | POST generate + GET candidates |
| Manager team workspace | Live | `/employee-app/team` — direct-report scoped read-only |

## Manager team read workspace

| Rule | Value |
|------|--------|
| Scope | Active employees where `manager_employee_id` = manager's linked employee id |
| Admin scope | All employees |
| Endpoints | `GET /employee-mobile/manager/team-attendance`, `GET .../team-requests` |
| Guard | `require_manager_team_reader` (admin/manager) |
| Write | **None** — read-only; CRUD/effects unchanged |
| Review | `/employee-requests/review` — manager scoped to direct reports; admin all |
| Schema | `employees.manager_employee_id` (Alembic s51) |

## Owner / tester mobile readiness

| Rule | Value |
|------|--------|
| Real mobile testing | Requires `users` row + linked active `employees.user_id` for tester account |
| Bootstrap | `backend/scripts/bootstrap_owner_employee.py` (env-driven, idempotent) |
| Readiness | `backend/scripts/check_employee_mobile_readiness.py` |
| Owner employee | Operational identity (`employee_type=management`); **not** payroll |
| Direct reports | Manual `manager_employee_id` assignment — see `docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md` |

## Routes

### Frontend

| Route | Purpose |
|-------|---------|
| `/employee-app` | Employee dashboard |
| `/employee-app/requests` | Self requests |
| `/employee-app/attendance` | Self attendance read-only |
| `/employee-app/review` | Manager/admin review inbox |
| `/employee-app/team` | Manager team workspace (read-only) |
| `/attendance/effects` | Admin/operator effects console |

### Backend (key prefixes)

| Prefix | Purpose |
|--------|---------|
| `GET/POST/PATCH /api/v1/employee-mobile/requests` | Self requests |
| `GET /api/v1/employee-mobile/attendance` | Self attendance read-only |
| `GET /api/v1/employee-mobile/manager/team-attendance` | Manager team attendance read-only |
| `GET /api/v1/employee-mobile/manager/team-requests` | Manager team requests overview |
| `GET/PATCH /api/v1/employee-requests/review` | Manager review |
| `GET/POST /api/v1/employee-attendance/effects` | Effects list/detail/apply/generate/candidates |
| `GET/POST/PATCH/DELETE /api/v1/employee-attendance/events` | Attendance CRUD (operator) |

## Permission model

| Actor | Employee app | Self requests | Self attendance | Team read | Review | Attendance CRUD | Effects generate/candidates | Effects apply |
|-------|--------------|---------------|-----------------|-----------|--------|---------------|----------------------------|---------------|
| `employee_mobile` | Yes (if linked) | Yes | Yes (read) | No | No | No | No | No |
| `manager` | Yes (if linked) | Yes | Yes (read) | Yes (dept) | Yes | No | No | No |
| `admin` | Yes (if linked) | Yes | Yes (read) | Yes (all) | Yes | Yes | Yes | Yes |
| `operator` | No* | No | No | No | No | Yes | Yes | Yes |
| Basic authenticated | No | No | No | No | No | No | No | No |

Guards: `require_employee_self_user`, `require_employee_request_reviewer`, `require_manager_team_reader`, `require_attendance_operator`.

## Flow map

```text
Employee creates request (self, no employee_id)
        ↓
Manager reviews (separate inbox, no self-approve)
        ↓
Approve → status-only (no attendance write, no auto-apply)
        ↓
Admin/operator lists generation candidates
        ↓
Admin/operator POST generate (idempotent effect row)
        ↓
Admin/operator applies pending effect manually
        ↓
Attendance event created on explicit apply only
        ↓
Employee sees own attendance read-only in mobile app
```

## Security invariants

- No client `employee_id` authority on self flows.
- Backend resolves identity via `employees.user_id`.
- Self-review forbidden (all linked employee rows, any status).
- Attendance CRUD admin/operator only.
- Effects apply admin/operator only.
- No auto-apply on approval.
- No payroll/payment integration.

## Deferred

| Item | Reason |
|------|--------|
| Formal manager reporting FK | Requires schema migration |
| Manager-scoped review inbox | Review remains global today |
| Payroll export | Out of scope |
| Reversal/unapply | Out of scope |
| Auto-apply on approve | Explicitly forbidden |
| Push notifications | Out of scope |
| Offline PWA sync | Out of scope |
| Native app | Out of scope |
| Centralized audit logger | Future |
| Multi-firm tenancy hardening | Future |
| `Co-authored-by` cleanup | Separate Employee/Attendance group cleanup |

## Recommended next build

**Formal manager reporting link** — add `manager_employee_id` or org table; align review inbox with team scope; keep read-only until explicit write policy.

## Related docs

- `docs/architecture/EMPLOYEE_MANAGER_TEAM_WORKSPACE_DECISION.md`

- `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md`
- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md`
- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md`
- `docs/architecture/EMPLOYEE_ATTENDANCE_ACCESS_CONTROL_DECISION.md`
- `docs/architecture/EMPLOYEE_IDENTITY_SESSION_AND_PWA_DECISION.md`
- `docs/architecture/EMPLOYEE_MOBILE_EXPERIENCE_DECISION.md`
