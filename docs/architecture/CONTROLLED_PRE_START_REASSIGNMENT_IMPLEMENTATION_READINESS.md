# Controlled Pre-Start Reassignment — Implementation Readiness

**Status:** Wave 9 audit **COMPLETE** — implementation **NOT AUTHORIZED**  
**Date:** 2026-08-04  
**Owner GO:** `FINALIZATION_WAVE_9 = CONTROLLED_PRE_START_REASSIGNMENT_IMPLEMENTATION_READINESS_AUDIT`  
**Decisions:** `CONTROLLED_PRE_START_REASSIGNMENT_DECISIONS.md` (DEC-REASSIGN-01…08)  
**Worklog:** `docs/worklog/realignment/2026-08-04_finalization_wave9_reassignment_implementation_readiness_audit.md`

```text
FINALIZATION_WAVE_9 = PARTIAL_BLOCKED
REASSIGNMENT_IMPLEMENTATION_READINESS = BLOCKED
PERSISTENCE_STRATEGY = SEPARATE_TRANSITION_TABLE_RECOMMENDED
SCHEMA_CHANGE_REQUIRED = YES
BLOCKER = EMBEDDED_MODEL_CANNOT_SAFELY_RETAIN_TRANSITION_HISTORY
OWNER_DECISION_REQUIRED = SCHEMA_CHANGE
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
QA_MUTATIONS = 0
WAVE_10 = NOT_AUTHORIZED
```

Owner decision target after this audit:

```text
SCHEMA_CHANGE_REQUIRED
```

(not `IMPLEMENT_WITHOUT_SCHEMA`)

---

## 1. Current persistence model (factual)

Canonical source: `ExecutionPlan.tasks_json` → `operational_tasks[]`.

Assigned LED task shape (order `880750` / plan `23`):

| Field | Present | Value (safe) |
| ----- | ------- | ------------ |
| `assigned_employee_id` | yes | `7` |
| `assignment_updated_at` | yes | ISO timestamp |
| `assignment_source` | yes | `canonical_controlled_assign_v1` |
| `assignment_actor_user_id` | yes | actor id string |
| previous employee | **no** | — |
| reason_code / note | **no** | — |
| transition_id / correlation_id | **no** | — |
| `assignment_history[]` | **no** | — |
| actor_role | **no** | — |
| eligibility snapshot/reference | **no** (eligibility revalidated at assign time only) | — |

```text
EMBEDDED_HISTORY_CAPABILITY = INSUFFICIENT
```

Answers:

1. **Current state only** — not append-only history.  
2. Retry identity today = same employee already set (`OUTCOME_ALREADY_SAME`); **no** transition id.  
3. Current audit **cannot** represent multiple reassignments.  
4. A reassignment that only overwrites fields **would destroy** prior audit.  
5. `clear_plan_task_assignment` pops `assigned_employee_id` and **loses** prior employee from current state (no history).  
6. No stable transition ordering structure.  
7. No transition ID.  
8. No request/correlation ID in persistence.  
9. Payload limit = whole `tasks_json` blob growth (unbounded if history stuffed into JSON).  
10. History not reportable as a first-class queryable set today.

---

## 2. Multi-transition conceptual simulation (no QA execution)

| # | Transition | Current-state after | History requirement | Idempotent retry | CAS | Conflict |
| - | ---------- | ------------------- | ------------------- | ---------------- | --- | -------- |
| 1 | `null → 7` | emp=7 + assign audit | retain T1 | same emp → no-op (Wave 6) | N/A first assign | different emp → 409 |
| 2 | `7 → X` | emp=X + new audit | retain T1+T2 | needs transition id | expected=7 | expected≠7 |
| 3 | `X → null` | emp=null | retain T1–T3; prior X known from history | null + same transition id | expected=X | expected≠X |
| 4 | `null → Y` | emp=Y | retain T1–T4 | same as Wave 6 style + transition id | expected=null | expected≠null |

**Embedded-only conclusion:** Steps 2–4 cannot be represented without inventing history storage. Overwrite of current fields alone **violates DEC-REASSIGN-03**.

---

## 3. Persistence strategy comparison

### Option A — Embedded `operational_task.assignment_history[]`

| Criterion | Assessment |
| --------- | ---------- |
| SAFETY | PARTIAL — atomic with current state only if same JSON rewrite under lock |
| COMPLEXITY | Medium |
| SCHEMA_IMPACT | None (JSON shape change) |
| MIGRATION_IMPACT | Soft/compat readers |
| ATOMICITY | Possible under Wave 6 lock + FOR UPDATE |
| CONCURRENCY | Process lock + row lock; **cluster unproven**; whole-blob rewrite risk for sibling fields |
| REPORTING | Weak — parse JSON across plans |
| PRIVACY | Must redact notes; easy to dump full task blob |
| RECOVERY | Harder; no unique transition constraint at DB |
| RECOMMENDATION | **Reject for first reassignment build** under DEC-REASSIGN-03 + transition identity |

Owner decisions forbid inventing ad-hoc JSON history without proving safety; this audit finds it **not** sufficient for transition id uniqueness, reporting, and multi-process guarantees.

### Option B — Plan-level `tasks_json.assignment_events[]`

Same class as A with weaker task locality. Slightly better for plan-wide audit stream; same schema-less risks. **Not recommended** as primary.

### Option C — Separate assignment transition table

| Criterion | Assessment |
| --------- | ---------- |
| SAFETY | Highest for history integrity + CAS helpers |
| COMPLEXITY | Higher (migration + dual-write/read contract) |
| SCHEMA_IMPACT | **YES** — migration required |
| MIGRATION_IMPACT | Required Owner GO |
| ATOMICITY | Current assignee on task + insert transition in one DB transaction |
| CONCURRENCY | Unique/current constraints + expected-current CAS enforceable |
| REPORTING | First-class SQL |
| PRIVACY | Column-level control; no full `tasks_json` dump |
| RECOVERY | Clear rollback of transition row + current state |
| RECOMMENDATION | **Recommended** before any reassignment/unassignment implementation |

```text
PERSISTENCE_STRATEGY = SEPARATE_TRANSITION_TABLE_RECOMMENDED
SCHEMA_CHANGE_REQUIRED = YES
REASSIGNMENT_WITHOUT_SCHEMA = BLOCKED
```

---

## 4. Authorization readiness

| Question | Answer |
| -------- | ------ |
| `execution.task_reassign` exists? | **NO** |
| `execution.task_unassign` exists? | **NO** |
| Addable without DB schema? | **YES** — `PERMISSION_MATRIX` is declarative Python |
| Manager/admin distinct? | **YES** — roles in matrix (`admin`, `manager`, `operator`, …) |
| `execution.task_assign` includes operator? | **YES** — must **not** be reused as reassign authority (DEC-REASSIGN-01) |
| Direct-service bypass? | Direct assign **403** `direct_assign_blocked` |
| Mobile transition path? | Claim/start **403** frozen |
| Soft IDOR risk? | Order/plan/task scope exists on assign; reassign must keep it |

```text
REASSIGN_AUTHORIZATION_READINESS = PARTIAL
```

Keys and enforcement for reassign/unassign are not implemented; matrix can host them without SQL migration. Still blocked by persistence/schema decision.

---

## 5. State / session / scheduling / reservation / capacity guards

| Guard | Source of truth | Status |
| ----- | --------------- | ------ |
| Task operational | `operational_tasks[]` + readiness gate | `REUSABLE` |
| Not completed | `ExecutionReality` ended_at / Wave 6 stale check | `REUSABLE` (active path) |
| Not started / no active session | `ExecutionReality` started_at without ended_at | `REUSABLE` for **active** session |
| Historical session requiring handoff | Reality history | `PARTIAL` — policy needs explicit `NO_SESSION_HISTORY` vs `NO_ACTIVE_SESSION` (recommend **fail-closed: any reality row for task blocks pre-start reassign**) |
| Cancelled | operational_status / product status | `PARTIAL` / inventory needed at implement time |
| Scheduling lock | Placeholder `scheduling=HOLD` constants | `MISSING` real schedule — **fail-closed: treat unknown/non-HOLD inventories as blocked; current constant HOLD is “not scheduled”** |
| Machine reservation | `reservation_status=not_reserved` constants | `MISSING` real reservation tables — fail-closed via constants today |
| Capacity allocation | `capacity_allocation=not_started` | `MISSING` real allocator — fail-closed via constant |
| Current assignment exists | embedded `assigned_employee_id` | `REUSABLE` |
| Expected current matches | not on reassign API (assign uses different-employee conflict) | `PARTIAL` — pattern reusable, not implemented for reassign |

```text
STATE_GUARDS_READINESS = PARTIAL
```

No scheduling/reservation/capacity **tables** found for execution employee assignment. Boundary remains fail-closed placeholders — do not invent sources.

---

## 6. DEC-015 reuse

Wave 6 call graph inside lock already:

```text
lock plan → FOR UPDATE → readiness → build_employee_eligibility_read_model
→ task row → eligible_ids → active session check → CAS current assignee
```

For reassignment, same eligibility builder can revalidate **new** employee inside lock after expected-current check.

```text
DEC015_REUSE = SAFE_REUSABLE
```

(with new guards + history persist — not a duplicate eligibility engine)

---

## 7. CAS / idempotency readiness

| Concern | Status |
| ------- | ------ |
| Expected-current CAS pattern | Proven for “different employee conflict” on first assign; **not** exposed as request field yet |
| Transition / idempotency identity | **MISSING** — required for safe reassign/unassign retries under DEC-REASSIGN-07 |
| Unassignment retry when null | Needs transition id; clear-helper today has none |

```text
CAS_IDEMPOTENCY_READINESS = PARTIAL
```

Without stable transition identity in persistence, retry safety for reassignment is **not verified**.

---

## 8. Transactionality readiness

Wave 6 assign: process lock + `SELECT FOR UPDATE` + single `tasks_json` commit + embedded audit consistency check.  
App log failure does **not** roll back commit (ops log is best-effort).  
Cluster/multi-node lock **not proven**.  
Sibling JSON lost-update mitigated only within documented lock boundary.

For reassignment: current-state + history **must** be one transaction. Embedded history can share the blob write; separate table needs transactional insert + tasks_json update together.

```text
REASSIGN_TRANSACTIONALITY_READINESS = PARTIAL
```

Blocked for implementation until persistence strategy (Option C) is Owner-authorized.

---

## 9. API contract options (conceptual — not implemented)

**Preferred:** two explicit routes (clearer permissions):

```text
PATCH .../tasks/{task_id}/reassign
  { expected_current_employee_id, new_employee_id, reason_code, optional_note, transition_id }

PATCH .../tasks/{task_id}/unassign
  { expected_current_employee_id, reason_code, optional_note, transition_id }
```

**Alternative:** single `.../assignment-transition` with `action=reassign|unassign` — viable but easier to misuse permissions.

Do **not** reopen `allow_reassign` on the assign route.

---

## 10. Reason codes / privacy

Define as **code enum** (Python + OpenAPI), not free DB table for v1.  
`OTHER` requires short safe note; forbid medical/salary/CNP/pricing content at validation.  
Persist reason_code (+ optional note) on transition row — not in unstructured logs with PII.

---

## 11. UI readiness

No authorized desktop Reassign/Unassign/Change-employee/Clear controls found.  
Mobile Claim UI exists but backend frozen.  
Ops-Graph shows assignee display for first assign path.  
Future UI must wait for backend + schema; show non-scheduling warning; no “available/ready/scheduled”.

---

## 12. Test matrix (future build — not executed on QA DB)

Cover: manager/admin allow; operator/viewer deny; wrong order/task; wrong expected employee; unauthorized new employee; unstarted allow; started/completed/cancelled/session/schedule/reservation/capacity block; DEC-015 pass/fail; CAS match/stale; transition retry; concurrent managers; history retention/order; atomic fail/rollback; PII boundary.

---

## 13. Dead pieces (none removed)

| Piece | Class |
| ----- | ----- |
| `allow_reassign` public | `BLOCKED_LEGACY` |
| `allow_reassign` service param | `SUPERSEDED` |
| `clear_plan_task_assignment` | `ACTIVE_LEGACY` (unsafe for policy unassign — no history) |
| `assign_plan_task` | `BLOCKED_LEGACY` |
| Mobile claim / start_from_available | `BLOCKED_LEGACY` |
| Legacy reassignment tests | `ACTIVE_LEGACY` |
| Old reassignment UI | `UNKNOWN` / absent as product control |

```text
Dead pieces removed: NONE
```

---

## 14. Remaining blockers

1. **No append-only transition history** in embedded model.  
2. **No transition/idempotency identity** store.  
3. **`execution.task_reassign` / `execution.task_unassign` missing** (addable in code after schema GO sequencing).  
4. **Session-history policy** needs explicit fail-closed rule beyond active-only.  
5. **Scheduling/reservation/capacity** are placeholders — keep fail-closed.  
6. **Live SQLite writers** (`:8000` reload + `:8002`) can change global DB file hash without assignment mutations.

---

## 15. Next step

```text
OWNER DECISION:
REASSIGNMENT_TRANSITION_PERSISTENCE_SCHEMA
```

Do **not** start `CONTROLLED_PRE_START_REASSIGNMENT_IMPLEMENTATION` until schema Owner GO is recorded.
