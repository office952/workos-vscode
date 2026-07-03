# Employee Request Attendance Effects — Apply Step Decision

## 1. Status

| Item | Value |
|------|--------|
| **Status** | Decision / Guard |
| **Runtime impact** | none (this document only) |
| **DB impact** | none |
| **Frontend impact** | none |
| **Payroll impact** | none |

This build **does not apply anything** to pontaj. It defines guards and contracts for the **next** implementation build that will write to `employee_attendance_events`.

**Related docs:**

- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md` — integration principles + foundation
- `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_FOUNDATION.md` — foundation implementation (`ae23b2b`)

---

## 2. Context

Current chain (committed):

1. Employee requests: create/list/cancel (self); approve/reject (manager/admin) — **status-only**.
2. `attendance_request_effects` (foundation `ae23b2b`): idempotent **generation** of `pending` / `conflict` / `cancelled` rows — **no write** to `employee_attendance_events`.
3. Internal pontaj: default-present schedule + exception events in `employee_attendance_events` (CRUD via `/api/v1/employee-attendance/events`).

The **apply step** is the first operation that may **create** attendance events from an effect. Because it mutates pontaj truth, it requires a separate decision and service boundary **before** any runtime code.

---

## 3. Principles

1. **Attendance Effects report/prepare before mutate** — generate/conflict-check first; apply is a distinct, explicit mutation.
2. **Approval ≠ attendance mutation** — `approve_employee_request` must never call apply.
3. **Apply is separate, explicit, audited** — manual operator action in MVP; not silent background side effect.
4. **Attendance ≠ payroll** — internal hours/events only; no salary/tax/ledger.
5. **Payroll / payment / CostEngine out of scope** for apply pipeline.
6. **Client does not dictate `employee_id`** — apply uses server-resolved employee from effect/request linkage.
7. **No duplicate apply** for the same `employee_request_id` / effect id.
8. **Conflict stops apply** — never ignored, never auto-repaired in MVP.
9. **Cancelled request/effect is not applicable** — apply refused.
10. **Applied effect is not silently deleted or overwritten** — reversal is a deferred build.

---

## 4. Actors and permissions

| Actor | Generate effect (today) | Apply effect (future MVP) |
|-------|-------------------------|---------------------------|
| Self employee | No (via review path only) | **No** |
| Manager reviewer | No (not wired to approve) | **No** in MVP |
| Admin / operator attendance | Yes (explicit service call / future job) | **Yes** — recommended MVP |
| System scheduled job | Deferred | **No** in MVP |
| Payroll / payment role | No | **No** |

**Firm recommendation:** apply is **manual admin/operator only** in MVP — not on approve, not manager self-service. Reason: pontaj mutation needs mature conflict rules and human oversight.

Authorization (future): reuse `get_current_user`; require `admin` (or dedicated `attendance_operator` role if introduced later — **deferred**).

---

## 5. Lifecycle — `attendance_request_effects`

Uses **existing** model statuses (`backend/models/attendance_request_effect.py`):

| Status | Meaning | Apply eligibility |
|--------|---------|-------------------|
| `pending` | Generated; no attendance write yet; no blocking conflict (or re-validated clean) | **Eligible** if all §6 conditions pass |
| `conflict` | Blocked — overlap, missing payload, deferred type | **Not eligible** until manually resolved (deferred) |
| `applied` | Attendance event(s) created; `applied_at` / `applied_by_user_id` set | **Not eligible** (idempotent no-op or 409) |
| `cancelled` | Request/effect no longer valid for apply | **Forbidden** |

**Not in model today:** `superseded` — **deferred**; do not add without migration build.

**Transitions (future apply build):**

```text
pending  --apply(success)-->  applied
pending  --apply(conflict)-->  conflict  (or remain pending + conflict metadata — prefer status conflict)
conflict --manual resolve-->   pending   (deferred admin workflow)
pending|conflict --cancel-->   cancelled
applied  --reversal-->         (deferred separate build; NOT delete/overwrite)
```

---

## 6. When `pending` becomes `applied`

Apply **must refuse** unless **all** conditions hold:

| # | Condition |
|---|-----------|
| 1 | Source `employee_requests.status == approved` |
| 2 | Effect row exists; unique on `employee_request_id` |
| 3 | Effect `status == pending` (not `applied`, `cancelled`, `conflict`) |
| 4 | Re-run `detect_attendance_effect_conflict` → no active conflict |
| 5 | Request was not self-approved (reviewer ≠ subject employee link) |
| 6 | `employee_id` on effect matches approved request employee (server-side) |
| 7 | Payload complete for type (see mapping §6.1) |
| 8 | No overlapping non-cancelled `employee_attendance_events` in range |
| 9 | Apply creates **exactly** the intended attendance event(s) — no extras |
| 10 | Audit fields populated: `applied_by_user_id`, `applied_at`, attendance event `source` |

### 6.1 Type mapping (apply-time, future)

| Effect type | Request type | Attendance event (proposed) | MVP apply |
|-------------|--------------|----------------------------|-----------|
| `leave_range` | `leave` | `event_type=leave`, range `date_start`–`date_end`, `event_status=confirmed` or `approved` | **Yes** if pending + no conflict |
| `day_off` | `day_off` | Map to `leave` (paid) **or** `absent` (unpaid) — **open policy** | **Yes** only after policy locked; until then treat as conflict/deferred |
| `partial_time_off` | `time_off` | `event_type=partial`, single day, `hours_override` | **Deferred** — request has no `hours` |
| `attendance_correction` | `attendance_correction` | `event_type=correction`, single day, notes + override/delta | **Deferred** — no structured old/new on request |

Attendance write must use existing `create_attendance_event` validation (conflicts → 409 at service layer).

**Proposed future linkage (schema change deferred):** `applied_attendance_event_id` on effect row **or** attendance event `source=employee_request:{effect_id}`. Not in foundation model — document only for implementation build.

---

## 7. Conflict handling

| Rule | Behavior |
|------|----------|
| Conflict before apply | Apply **refused** (HTTP 409) |
| Existing events | **Never deleted** or overwritten |
| Operator visibility | `conflict_reason` + list of overlapping event types/ids in error detail |
| Effect status on refused apply | Remain `pending` or set `conflict` — **recommend** set/update `conflict` + reason |
| Auto-repair | **Forbidden** in MVP |
| Resolution | Manual/deferred (admin adjusts attendance or cancels effect) |

**Examples:**

- `leave` effect over existing `sick` on same working day → conflict.
- `day_off` over existing `leave` range → conflict.
- `time_off` effect (deferred type) → conflict at generation; apply blocked.
- `attendance_correction` without payload → conflict at generation; apply blocked.
- Request cancelled after effect generated → effect `cancelled`; apply forbidden.
- Effect already `applied` → apply returns 409 / idempotent success with same event id.

Reuse overlap logic from `attendance_request_effect_service._load_overlapping_attendance_events` and `employee_attendance_service._validate_conflicts`.

---

## 8. Idempotency and duplicate prevention

| Layer | Rule |
|-------|------|
| Generate | Unique `employee_request_id` — retry returns same row (implemented) |
| Apply | If `status == applied` and attendance event exists → return existing linkage; **do not** create second event |
| Apply retry | Safe no-op when already applied with same audit |
| Attendance events | At most one applied event set per effect in MVP (single range or single day) |

**Future field (proposal, not in this build):** `applied_attendance_event_id` Integer FK nullable on `attendance_request_effects`.

---

## 9. Cancelled request / effect

| Scenario | Apply |
|----------|-------|
| Request `rejected` | Never generated / never apply |
| Request `submitted` / not approved | Generate raises; apply N/A |
| Effect `cancelled` | Apply **403/409** forbidden |
| Request approved then cancelled (self) | Effect should be `cancelled` (existing `cancel_attendance_effect_for_request`); apply forbidden |
| Effect already `applied` then request cancelled | **No silent delete**; reversal deferred |

Foundation: `cancel_attendance_effect_for_request` refuses when `status == applied`.

---

## 10. Audit model

### Existing (foundation)

| Field | Location |
|-------|----------|
| `generated_by_user_id`, `generated_at` | `attendance_request_effects` |
| `applied_by_user_id`, `applied_at` | Reserved on effect (null until apply) |
| `reviewed_by_user_id`, `reviewed_at` | `employee_requests` |
| `conflict_reason`, `notes` | effect row |
| `source` | effect default `employee_request`; attendance `manual` today |

### Required on future apply

| Audit item | Storage |
|------------|---------|
| Who applied | `applied_by_user_id` |
| When applied | `applied_at` |
| Request id | `employee_request_id` |
| Effect id | `id` |
| Employee id | `employee_id` (server-side) |
| Attendance event id(s) created | proposed FK or `source` tag |
| Previous effect status | log / notes on apply |
| Apply refusal reason | HTTP 409 detail + optional `conflict_reason` update |
| Action source | e.g. `attendance_effect_apply` in attendance `source` |

**Not audited here:** payroll, payment, CostEngine, sensitive salary fields.

**Gap to verify before implementation:** centralized audit logger — if none, persist on effect + attendance `notes` minimum.

---

## 11. Proposed endpoints (future — not implemented)

Base prefix aligns with existing router: `/api/v1/employee-attendance`.

| Method | Path | Role | Purpose |
|--------|------|------|---------|
| GET | `/effects` | admin | List effects (filter: status, employee_id, date) |
| GET | `/effects/{effect_id}` | admin | Detail + conflict info |
| POST | `/effects/{effect_id}/apply` | admin | Apply pending effect → create attendance event(s) |
| POST | `/effects/{effect_id}/cancel` | admin | Cancel non-applied effect |

Optional (deferred): `POST /effects/generate` for explicit generation from approved request id.

### POST `/effects/{effect_id}/apply`

**Does:**

- Re-validate §6 conditions
- Create attendance event via `create_attendance_event`
- Set effect `applied`, `applied_at`, `applied_by_user_id`

**Does NOT:**

- Modify payments, payroll, balances
- Delete/overwrite existing attendance
- Auto-run on approve
- Accept `employee_id` from client body

**Responses:**

| Code | When |
|------|------|
| 200/201 | Applied; returns effect + attendance event summary |
| 403 | Non-admin; self-apply forbidden |
| 404 | Effect not found |
| 409 | Conflict, already applied, cancelled, request not approved |
| 422 | Invalid state / incomplete payload |

**Idempotency:** second apply → 200 with same result or 409 if inconsistent.

### POST `/effects/{effect_id}/cancel`

Same as service `cancel_attendance_effect_for_request`; admin only; 409 if already applied.

---

## 12. Mandatory tests (future implementation build)

1. Apply `leave` pending → creates one `leave` attendance event; effect `applied`.
2. Apply `day_off` pending → creates event per locked policy.
3. Pending effect + request not approved → apply 409.
4. Rejected request → no apply path.
5. Cancelled effect → apply 409/403.
6. Cancelled request → effect cancelled; apply forbidden.
7. Overlapping attendance → apply 409; existing event unchanged.
8. Apply idempotent — retry does not duplicate event.
9. Self employee cannot apply (403).
10. Manager cannot apply own linked request (403) — if manager role ever granted apply.
11. Admin can apply.
12. Apply sets `applied_by_user_id`, `applied_at`; attendance `source` documents request/effect.
13. Applied effect cannot be overwritten by second apply.
14. No `EmployeePaymentRecord` / payroll side effects.
15. `time_off` effect → apply blocked (409/deferred).
16. `attendance_correction` effect → apply blocked until structured payload.

Regression: foundation generate tests + review no-side-effect tests + attendance event tests remain green.

---

## 13. Deferred items

- Automatic apply on approval
- Scheduled apply worker
- Payroll / payment / balance integration
- Reversal / unapply after applied
- `time_off` apply until request has structured hours
- `attendance_correction` apply until old/new payload on request
- Advanced conflict resolution UI
- Migration: `applied_attendance_event_id` (or equivalent)
- Frontend admin review/apply panel
- Manager role apply
- `superseded` status
- `day_off` → `leave` vs `absent` policy lock

---

## 14. PASS / FAIL criteria (for this decision build)

**PASS:**

- This document exists
- QA doc exists
- No runtime / frontend / DB / migration changes
- No writes to `employee_attendance_events`
- No payroll/payment/CostEngine integration
- Working tree contains only expected docs

**FAIL:**

- Any apply service/endpoint/model change
- Auto-apply on approve proposed without explicit guard
- Conflict ignored or auto-repaired in spec
- Staging/commit without explicit user request

---

## Appendix — Current code inventory (read-only audit)

| Area | Finding |
|------|---------|
| Effect model | Statuses: pending/applied/conflict/cancelled; audit fields present |
| Generate service | No attendance write; overlap detection implemented |
| Cancel service | Blocks cancel when applied |
| Attendance service | `create_attendance_event` with conflict validation |
| Review approve | Status-only; tests prove no attendance create |
| Request model | No hours / correction structured fields |

**Next implementation build name:** `Employee Request Attendance Effects Apply Step`
