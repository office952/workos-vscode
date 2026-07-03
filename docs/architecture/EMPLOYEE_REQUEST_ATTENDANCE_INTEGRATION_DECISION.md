# Employee Request → Attendance Integration Decision

## 1. Purpose

Define how **approved employee requests** that may affect internal pontaj should interact with the existing **event-based attendance** model — without implementing runtime integration in this document.

This decision applies after the Employee Mobile / Requests chain (`3e3377a` and prior): self-only requests, manager review, status-only approve/reject, UI hardening.

**Scope of this doc:** architecture and policy only. **No code, DB, or migrations in this build.**

---

## 2. Current state

### Employee requests (`employee_requests`)

| Aspect | State |
|--------|--------|
| Table | `employee_requests` |
| Types | `leave`, `day_off`, `time_off`, `advance`, `attendance_correction`, `equipment`, `issue_report`, `other` |
| Review | Manager/admin approve/reject **submitted** only |
| Approve side effects | **None** — status + review metadata only |
| Self-approval | Blocked (`403 self_review_forbidden`) |
| Date fields | `start_date`, `end_date` (required for date-bound types) |
| Hours / correction payload | **Not modeled** on request (no `hours`, no `old_value`/`new_value`) |

Contract enforced by tests: `test_approve_does_not_create_attendance_event`, `test_approve_does_not_create_payment_record`.

### Internal attendance (`employee_attendance_events`)

| Aspect | State |
|--------|--------|
| Model | **Default present** Mon–Fri, 8h/day; exceptions via events |
| Table | `employee_attendance_events` (migration `s47_employee_attendance_events`) |
| Event types | `absent`, `leave`, `sick`, `partial`, `overtime`, `correction` |
| Event statuses | `planned`, `approved`, `confirmed`, `cancelled` (default create: `confirmed`) |
| Range vs single-day | Range: `absent`, `leave`, `sick`. Single-day: `partial`, `overtime`, `correction` |
| Partial hours | `hours_override` on `partial`; `hours_delta` on `overtime` / `correction` |
| Check-in / check-out | **Not implemented** — no punch-clock model |
| Source field | `source` (default `manual`) — no `employee_request_id` today |
| Conflicts | Service-level validation; HTTP 409 on overlap |
| API | `/api/v1/employee-attendance/events` (CRUD), `/summary` (month rollup) |
| Payroll fiscal | **Out of scope** — internal hours summary only |

Reference: `docs/qa/BUILD_PERSONAL_ATTENDANCE_EVENTS_FOUNDATION.md`, `backend/services/employee_attendance_service.py`.

### Gap: request types vs attendance event types

| Request type | Attendance event type (direct) |
|--------------|--------------------------------|
| `leave` | `leave` (range) |
| `day_off` | **No 1:1 type** — must map (see §4) |
| `time_off` | **`partial`** (needs hours — **not on request today**) |
| `attendance_correction` | `correction` (needs notes + override/delta — **partially on request**) |

---

## 3. Non-goals

- No automatic attendance mutation on approve/reject in current production path.
- No payment ledger, advance/debt, or balance changes from request approval.
- No payroll fiscal, tax, or salary calculation.
- No CostEngine / Quote / Pricing / Margins integration.
- No team-lead scoped review or notifications in this decision.
- No deletion or overwrite of existing attendance events without explicit apply step.
- No implementation in this document (no tables, workers, or UI).

---

## 4. Request type classification

| Request type | Can affect attendance? | Needs date range? | Needs partial day / hours? | Auto-create attendance event at approve? | Risks | Decision |
|--------------|------------------------|-------------------|----------------------------|------------------------------------------|-------|----------|
| **leave** | yes | yes | no | **no** — use `attendance_request_effects` pending | Overlap with leave/sick/absent; multi-day weekends | Map to effect → `leave` range; apply with conflict check |
| **day_off** | yes | yes (often 1 day) | no | **no** | No `day_off` event type; paid vs unpaid ambiguity | MVP: effect → `leave` (paid day off) **or** `absent` (unpaid) — **open question §18**; default **pending manual review** until policy set |
| **time_off** | yes | yes (typically 1 day) | **yes** (hours) | **deferred** | Request has no `hours` field; `partial` requires `hours_override` | **DEFERRED** until request schema adds hours or duration; do not auto-apply in MVP |
| **attendance_correction** | yes | yes (single day) | optional delta | **no** | Request lacks structured old/new; correction requires notes + override/delta | Effect **pending**; apply step validates and creates `correction` event; **never** direct overwrite at approve |
| **advance** | no | no | no | no | Payment confusion | **Forbidden** — no attendance effect |
| **equipment** | no | no | no | no | — | **Forbidden** — no attendance effect |
| **issue_report** | no | no | no | no | — | **Forbidden** — no attendance effect |
| **other** | no (default) | varies | no | no | Scope creep | **Forbidden** by default; manual attendance entry if ops decides |

### Mapping notes (attendance-capable types)

- **`leave`** → proposed `effect_type`: `leave_range` → attendance `event_type=leave`, `event_status=planned` or `approved` until applied as `confirmed`.
- **`day_off`** → proposed `effect_type`: `day_off` → target attendance type TBD (`leave` vs `absent`); status **pending** until policy confirmed.
- **`time_off`** → proposed `effect_type`: `partial_hours` → attendance `event_type=partial` — **blocked** until hours on request.
- **`attendance_correction`** → proposed `effect_type`: `correction` → attendance `event_type=correction`, single-day, requires apply-time validation.

---

## 5. Attendance integration principles

1. **Separation of concerns:** Request approval records **HR/workflow intent**; attendance records **operational pontaj truth**.
2. **Dedicated effect layer:** Approved requests do **not** write `employee_attendance_events` directly in the approve handler.
3. **Idempotency:** One approved request → at most one active effect chain; re-processing must not duplicate.
4. **No silent overwrite:** Existing events on affected dates → **conflict** or explicit adjustment, never blind replace.
5. **Auditability:** Every applied effect links to `employee_request_id`, reviewer, and apply actor.
6. **Fail-closed on ambiguity:** Missing hours, missing correction details, or policy gaps → **pending** or **conflict**, not guess.
7. **Payroll boundary:** Attendance integration adjusts **internal event summary only** — not fiscal payroll.

---

## 6. Approved request lifecycle

```text
1. Employee creates request (submitted)
2. Manager/admin approves → request.status = approved (ONLY)
3. Effect worker/service creates attendance_request_effect (status = pending)
4. Conflict check against employee_attendance_events (+ other pending effects)
5. If clean → apply creates/updates attendance event(s); effect = applied
6. If conflict → effect = conflict; operator review required
7. If request cancelled after approval → effect → cancelled or manual review (see matrix)
```

Reject/cancel before approval: **no effect**.

---

## 7. Side-effect rules

| Action | Allowed side effect |
|--------|---------------------|
| Approve request | Update `employee_requests` status/review fields only |
| Reject request | Status only |
| Cancel (self) | Status only |
| Future: generate effect | Insert/update `attendance_request_effects` only |
| Future: apply effect | Insert `employee_attendance_events` (or cancel/adjust per rules) |
| Forbidden at approve | Payment records, balance transactions, payroll runs, CostEngine |

---

## 8. Auditability rules

Any attendance effect or applied event must retain:

| Field | Source |
|-------|--------|
| `employee_request_id` | FK / effect row |
| `approved_by` | `reviewed_by_user_id` on request |
| `approved_at` | `reviewed_at` on request |
| `generated_by` | user/service that created effect |
| `generated_at` | timestamp |
| `applied_by` | user/service that applied effect |
| `applied_at` | timestamp |
| `old_value` / `new_value` | For corrections: snapshot in effect notes/JSON (request lacks fields today) |

Attendance events should set `source = employee_request` (or `request_effect:{id}`) when applied from this flow.

---

## 9. Conflict rules

- Two full-day types (`absent`, `leave`, `sick`) on same working day → **conflict** (already enforced in attendance service).
- `partial` on day with full-day leave/sick/absent → **conflict**.
- Approved request range overlapping existing **confirmed** leave → **conflict** or **pending manual review** (MVP: **conflict**).
- Duplicate pending effect for same `employee_request_id` → **forbidden** (idempotency).
- Employee inactive → **forbidden** for new effects.
- **Never** auto-delete existing attendance rows.

---

## 10. Idempotency rules

- Unique constraint (recommended): `(employee_request_id)` on `attendance_request_effects` where status not in (`cancelled`).
- Re-running effect generator for same approved request → no second pending row.
- Re-approve (409 today) → no effect path.
- Apply endpoint must be safe to retry when effect already `applied` (return existing link).

---

## 11. Manual override rules

- Operators may apply, reject, or cancel a **pending** effect via admin UI/API (future build).
- **Conflict** effects require human resolution: adjust dates, merge with existing event, or cancel effect.
- Manual attendance CRUD (`/employee-attendance/events`) remains valid; effects must detect drift if event edited outside flow.

---

## 12. Manager/admin responsibilities

- Approve/reject only others' requests (self blocked).
- Approval does **not** imply pontaj is updated — operators must understand **pending effect** queue (future UI).
- Manager's own leave/time-off requires **another** reviewer → effect generated only after that approval.

---

## 13. Data model requirements (future — not in this build)

### Recommended: `attendance_request_effects`

| Column | Notes |
|--------|--------|
| `id` | PK |
| `employee_request_id` | FK, unique active per request |
| `employee_id` | denormalized for queries |
| `request_type` | copy from request |
| `effect_type` | e.g. `leave_range`, `day_off`, `partial_hours`, `correction` |
| `status` | `pending`, `applied`, `conflict`, `cancelled` |
| `date_start`, `date_end` | from request |
| `hours` | nullable; for future `time_off` |
| `payload_json` | correction old/new, mapping choices |
| `generated_by_user_id`, `generated_at` | |
| `applied_by_user_id`, `applied_at` | nullable |
| `attendance_event_id` | nullable FK after apply |
| `source` | `employee_request` |
| `notes` | audit / conflict reason |

**Do not create this table in the decision-only build.**

Optional extension to `employee_attendance_events`: `employee_request_id` nullable FK for reverse lookup (alternative to effect table only — effect table preferred for pending/conflict states).

---

## 14. API requirements (future)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/employee-requests/effects/generate` | Internal/worker: create pending from approved request |
| `GET /api/v1/employee-requests/effects` | List pending/conflict for ops |
| `POST /api/v1/employee-requests/effects/{id}/apply` | Apply after conflict check |
| `POST /api/v1/employee-requests/effects/{id}/cancel` | Cancel pending/conflict |

Approve/reject endpoints **unchanged** — no attendance calls inside.

---

## 15. Test requirements (future)

See §17 and QA doc `BUILD_EMPLOYEE_REQUEST_ATTENDANCE_DECISION.md` test plan.

---

## 16. Recommended MVP

**Option: `attendance_request_effects` (recommended)**

| Step | Behavior |
|------|----------|
| 1 | Employee submits request |
| 2 | Manager approves → **status only** (unchanged) |
| 3 | Async or explicit job creates **one** `pending` effect for attendance-capable types |
| 4 | Apply service checks conflicts against `employee_attendance_events` |
| 5 | If no conflict → create attendance event(s), mark effect `applied` |
| 6 | If conflict → `conflict`, no attendance write |
| 7 | `advance` / `equipment` / `issue_report` / `other` → **no effect row** |

**In MVP scope:**

- `leave` → auto-apply path when no conflict (optional: still default **pending** for first release — see deferred).
- `day_off`, `time_off`, `attendance_correction` → **pending manual review** or **conflict** until schema/policy complete.

**First release conservative default:** all effects start as **`pending`**; auto-apply only for `leave` without overlap in a later sub-build.

---

## 17. Deferred decisions

| Item | Reason |
|------|--------|
| `time_off` auto-apply | No hours on `employee_requests` |
| `day_off` → `leave` vs `absent` | HR policy not codified |
| Auto-apply vs always pending | Ops preference |
| Async worker vs sync on approve | Infra choice |
| Link effect to multiple events (multi-day split) | Implementation detail |
| Employee self visibility of effect status | UI build |
| Notifications on conflict | Explicit non-goal for now |

---

## 18. Open questions

1. **`day_off`:** paid leave (`leave`) or unpaid (`absent`)?
2. **`time_off`:** add `hours` / `duration_minutes` to request model?
3. **`attendance_correction`:** add structured `correction_before` / `correction_after` fields?
4. Should first MVP auto-apply **`leave`** only, or all types manual?
5. Who may **apply** effects — admin only, or manager with scope?
6. Cancel approved request: auto-cancel pending effect, or require manual cleanup?

---

## 19. Next build proposal

**`Employee Request Attendance Effects Foundation`**

- Migration for `attendance_request_effects` (or equivalent)
- Effect generator service (no change to approve handler behavior initially — separate trigger)
- Apply + conflict services reusing `employee_attendance_service._validate_conflicts`
- Backend tests from test plan
- No payroll, no payment, no CostEngine

---

## Appendix A — Conflict matrix

Legend: **AUTO** = auto apply if no other blockers | **PENDING** = pending manual review | **CONFLICT** = conflict state | **FORBIDDEN** = no effect | **DEFERRED** = not in MVP

| Scenario | leave | day_off | time_off | attendance_correction |
|----------|-------|---------|----------|------------------------|
| No attendance record for date | AUTO* | PENDING | DEFERRED | PENDING |
| Existing check-in/check-out | N/A (no punch model) | N/A | N/A | N/A |
| Existing confirmed leave/sick/absent on date | CONFLICT | CONFLICT | CONFLICT | CONFLICT |
| Overlapping pending request effect | CONFLICT | CONFLICT | CONFLICT | CONFLICT |
| Employee inactive | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| Request cancelled after approval | effect → cancelled / manual review | same | same | same |
| Request rejected | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| Partial day request | N/A (full-day range) | N/A | DEFERRED | N/A |
| Multi-day request | AUTO* (range) | PENDING (range) | DEFERRED | FORBIDDEN (single-day only) |

\*AUTO only after dedicated apply step and MVP policy enables it; until then treat as **PENDING**.

---

## Appendix B — Required decisions (explicit)

| ID | Decision |
|----|----------|
| A | Not all requests touch pontaj — `advance`, `equipment`, `issue_report`, `other` default **no** |
| B | `leave`, `day_off`, `time_off`, `attendance_correction` **may** affect pontaj |
| C | Approved request **must not** modify pontaj without dedicated layer; MVP uses **`attendance_request_effects`**, idempotent |
| D | **No auto-delete** of existing pontaj; overlap → conflict or explicit adjustment |
| E | Idempotency via `employee_request_id` on effect table |
| F | Full audit trail on effects and applied events |
| G | `attendance_correction` requires apply step + validation — not direct approve side effect |
| H | `time_off` partial hours **deferred** until request model supports hours |
| I | Manager self-requests: no self-approve → no self-generated effect |
| J | Attendance integration ≠ payroll fiscal |

---

## Appendix C — Future test plan (mandatory)

1. Approved `leave` creates **one** pending attendance effect.
2. Re-approving same request does not duplicate effect (409 on request; no second effect).
3. Approved multi-day `leave` effect carries correct `date_start`/`date_end`.
4. Existing `leave`/`sick`/`absent` on date → **conflict**, not overwrite.
5. `attendance_correction` effect requires structured payload at apply time.
6. Rejected request creates **no** effect.
7. Cancel after approval marks effect **cancelled** or flags manual review.
8. Manager cannot approve own request → cannot generate own effect via self-approval path.
9. `advance` approval creates **no** attendance effect.
10. No payment/payroll side effects in effect/apply pipeline.

---

## 20. Implemented foundation (BUILD — Attendance Effects Foundation)

**Status:** model + service + tests implemented. **No auto-apply** to `employee_attendance_events` yet.

### Model: `attendance_request_effects`

| Field | Purpose |
|-------|---------|
| `employee_request_id` | Unique (idempotency) |
| `employee_id`, `request_type`, `effect_type`, `status` | Effect identity |
| `date_start`, `date_end`, `hours` | Planned range (hours deferred) |
| `generated_by_user_id`, `generated_at` | Audit |
| `applied_at`, `applied_by_user_id` | Reserved for apply step |
| `conflict_reason`, `notes` | Conflict / cancel audit |
| `source` | Default `employee_request` |

Statuses: `pending`, `applied`, `conflict`, `cancelled`.

### Service: `attendance_request_effect_service.py`

| Function | Behavior |
|----------|----------|
| `generate_attendance_effect_for_request` | Approved + capable types only; idempotent; **no** attendance write |
| `get_attendance_effect_for_request` | Lookup by request id |
| `detect_attendance_effect_conflict` | Re-evaluate conflict reason |
| `cancel_attendance_effect_for_request` | Cancel non-applied effects |

**Generation rules (current):**

- `leave` / `day_off` → `pending` unless attendance overlap → `conflict`
- `time_off` → always `conflict` (`time_off_requires_structured_hours`)
- `attendance_correction` → always `conflict` (`attendance_correction_requires_structured_payload`)
- `advance` / `equipment` / `issue_report` / `other` → skip (`None`)

**Conflict detection:** overlapping non-cancelled `employee_attendance_events` for same employee/date range.

**DB:** table created via `Base.metadata.create_all` in dev/test (no new migration in foundation build).

**Deferred:** apply step, API endpoints, frontend, structured time_off/correction fields on requests.

**Apply step decision (docs only):** see `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md` — guards for manual admin apply, conflict refusal, idempotency, no auto-apply on approve.

