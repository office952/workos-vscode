# Controlled Pre-Start Reassignment and Unassignment Decisions

**Status:** Owner decisions **RECORDED** (2026-08-04) · Phase B backend **VERIFIED** (Wave 11 closure) · Phase C QA readiness **BLOCKED** · UI **NOT AUTHORIZED**  
**Task:** `CONTROLLED_PRE_START_REASSIGNMENT_OWNER_DECISION_ONLY`  
**Related audit:** `ASSIGNMENT_OBSERVABILITY_AND_REASSIGNMENT_POLICY.md` (Wave 8)  
**Related hardening:** `ASSIGNMENT_COMMAND_REMEDIATION_DECISIONS.md` (DEC-ASSIGN-01…08)  
**Worklog:** `docs/worklog/realignment/2026-08-04_controlled_pre_start_reassignment_owner_decisions.md`  
**Phase B worklog:** `docs/worklog/realignment/2026-08-04_finalization_wave11_phase_b_controlled_pre_start_reassignment_backend.md`  
**Wave 11 closure:** `docs/worklog/realignment/2026-08-04_finalization_wave11_phase_b_runtime_and_guard_closure.md`

```text
CONTROLLED_PRE_START_REASSIGNMENT_OWNER_DECISIONS = RECORDED
REASSIGNMENT_IMPLEMENTED = YES_BACKEND
UNASSIGNMENT_IMPLEMENTED = YES_BACKEND
REASSIGNMENT_IMPLEMENTATION_AUTHORIZED = TRUE   # Wave 11 Phase B GO
UNASSIGNMENT_IMPLEMENTATION_AUTHORIZED = TRUE
REASSIGNMENT_EXECUTION_AUTHORIZED = FALSE       # no QA / Phase C
UNASSIGNMENT_EXECUTION_AUTHORIZED = FALSE
WAVE_9 = PARTIAL_BLOCKED_READINESS_AUDIT
SCHEMA_OWNER_DECISIONS = RECORDED
WAVE_10 = PASS_PHASE_A
WAVE_11 = PASS_PHASE_B_BACKEND
PHASE_A = VERIFIED
PHASE_B = BACKEND_VERIFIED
PHASE_C = NOT_AUTHORIZED
PHASE_C_QA_READINESS = BLOCKED
PHASE_C_BLOCKER = RESOURCE_GUARDS_HAVE_NO_CANONICAL_CLEAR_SOURCE
PHASE_C_RESOURCE_GUARD_OWNER_DECISION = RECORDED
DEC-PHASE-C-RESOURCE-01 = KEEP_PHASE_C_BLOCKED
```

Canonical QA fixture (unchanged by this decision task):

```text
order_id = 880750
execution_plan_id = 23
assigned_task = node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters
assigned_employee_id = 7
```

---

## Owner principle

Reassignment is **not** a silent overwrite of `assigned_employee_id`.  
It is a controlled operational transition requiring current employee, new employee, actor, reason, task/session/scheduling state, eligibility, audit history, and concurrency protection.

Forbidden forever under this policy family:

```text
last-write-wins
silent reassignment
caller-controlled allow_reassign
clear assigned_employee_id without policy
Mobile takeover
claim-based overwrite
```

Initial policy family: **minimal pre-start only**. Post-start operational transfer requires a **separate future architecture**.

---

## DEC-REASSIGN-01 — Who may reassign?

| Field | Value |
| ----- | ----- |
| Decision | **`MANAGER_AND_ADMIN_ONLY`** |
| Rationale | Initial assign permission must not automatically authorize overwrite of a persisted assignment. |
| Accepted constraints | Distinct conceptual permission (e.g. `execution.task_reassign`); actor authenticated; manager or admin; order/plan/task scope. Initial assigner does **not** auto-gain reassign. Assigned employee cannot self-reassign. |
| Rejected alternatives | Operator via `execution.task_assign` alone; original-assigner privilege; employee self-service. |
| Implementation implications | Must not reuse `execution.task_assign` as sufficient for reassign/unassign without Owner confirmation if matrix cannot host new keys. |
| Schema implications | None for this decision. |
| Owner gate | Implementation not authorized here. |

---

## DEC-REASSIGN-02 — When allowed?

| Field | Value |
| ----- | ----- |
| Decision | **`STRICT_PRE_START_ONLY`** |
| Rationale | First safe contract avoids handoff of in-progress work. |
| Accepted constraints | Allowed only when **all** hold: operational task; not completed; not cancelled; not started; no active session; no historical execution session requiring handoff; no machine reservation; no scheduling lock; no capacity allocation; current assignment exists; new employee active; new employee DEC-015 eligible inside lock. |
| Rejected alternatives | Reassign after start; ignore session/schedule/reservation. |
| Implementation implications | Any started/session/scheduled/reserved state → `REASSIGNMENT = BLOCKED`. |
| Owner gate | Post-start transfer = future separate contract. |

---

## DEC-REASSIGN-03 — History

| Field | Value |
| ----- | ----- |
| Decision | **`RETAIN_FULL_ASSIGNMENT_TRANSITION_HISTORY`** |
| Rationale | Overwriting employee without transition record is not auditable. |
| Accepted constraints | Minimum retained fields: order_id, execution_plan_id, task identity, previous_employee_id, new_employee_id, actor_id, actor_role, reason_code, optional safe note, timestamp, task state, eligibility result/reference, previous/new assignment audit references, request/correlation ID if available. |
| Rejected alternatives | Replace employee without history. |
| Implementation implications | First implementation audit must prove history can be retained safely. If embedded model cannot → `PARTIAL_BLOCKED` / `OWNER_DECISION_REQUIRED = REASSIGNMENT_PERSISTENCE_MODEL` or `SCHEMA_CHANGE`. No ad-hoc JSON list without architectural audit. |
| Schema implications | May require schema GO — **not** authorized now. |

---

## DEC-REASSIGN-04 — Reason code

| Field | Value |
| ----- | ----- |
| Decision | **`REASON_CODE_REQUIRED`** |
| Initial codes | `EMPLOYEE_UNAVAILABLE` · `EMPLOYEE_INACTIVE` · `ELIGIBILITY_CHANGED` · `INCORRECT_INITIAL_ASSIGNMENT` · `MANAGER_CORRECTION` · `PLANNING_CHANGE` · `OPERATIONAL_REBALANCE_PRE_START` · `OTHER` |
| `OTHER` | Short safe note **required**. |
| Forbidden note content | Medical data; salary; hourly cost; detailed HR discipline; CNP; unnecessary PII; pricing; commercial data. |

---

## DEC-REASSIGN-05 — Unassignment

| Field | Value |
| ----- | ----- |
| Decision | **`ALLOWED_ONLY_PRE_START_BY_MANAGER_OR_ADMIN`** |
| Accepted constraints | Same pre-start guards as reassignment; explicit unassign/reassign permission; reason code required; history retained; current `assigned_employee_id` → null without erasing prior transition history. |
| Rejected alternatives | Unassign after start in first build; silent clear; history wipe. |

---

## DEC-REASSIGN-06 — Employee acknowledgement

| Field | Value |
| ----- | ----- |
| Decision | **`NOT_REQUIRED_FOR_FIRST_PRE_START_BUILD`** |
| Rationale | Mobile frozen; no notification/acceptance workflow; pre-start only; manager/admin authority. |
| Future | `EMPLOYEE_NOTIFICATION = FUTURE` · `EMPLOYEE_ACKNOWLEDGEMENT = FUTURE_OWNER_DECISION` |
| Owner gate | Do not activate Employee Mobile. |

---

## DEC-REASSIGN-07 — Concurrency

| Field | Value |
| ----- | ----- |
| Decision | **`EXPECTED_CURRENT_EMPLOYEE_CAS`** |
| Conceptual request | `expected_current_employee_id` + `new_employee_id` + `reason_code` |
| Success | current assignee equals expected |
| Conflict | current changed; or different target on retry |
| Idempotent retry | current already equals requested new employee **and** audit proves same transition/request → deterministic no-op success |
| Forbidden | last-write-wins; blind overwrite; `allow_reassign=true` |

---

## DEC-REASSIGN-08 — Scheduling interaction

| Field | Value |
| ----- | ----- |
| Decision | **`BLOCK_WHEN_SCHEDULING_OR_RESERVATION_EXISTS`** |
| Accepted constraints | First build does not move/recalculate schedule, machine reservation, capacity, availability, or sessions. Any of those present → reassignment **and** unassignment **BLOCKED**. |
| Future | Atomic operational transfer coordinating employee + schedule + reservation + capacity + sessions — **not authorized now**. |

---

## Resulting future contract (not implemented)

```text
1. Manager/admin only
2. Separate explicit permission
3. Pre-start only
4. No active session
5. No completed/cancelled task
6. No scheduling lock
7. No machine reservation
8. No capacity allocation
9. Current employee must match expected employee
10. New employee must pass DEC-015 inside lock
11. Reason code required
12. Full transition history retained
13. No silent overwrite
14. No last-write-wins
15. Unassignment allowed only under same pre-start guards
16. Employee acknowledgement not required in first build
17. Employee Mobile remains frozen
18. Post-start transfer requires a separate future architecture
```

---

## Persistence decision boundary (pre-implementation)

Before any implementation GO, audit whether full transition history can be retained safely in the current embedded model. Evaluate: current audit shape; append-only capability; payload growth; ordering; deduplication; retry identity; lost-update risk; reporting; privacy; mutation atomicity.

If complete safe history requires a separate table or schema change:

```text
IMPLEMENTATION = BLOCKED
OWNER_DECISION_REQUIRED = SCHEMA_CHANGE
```

Do not invent an ad-hoc JSON history list without architectural audit.

---

## Authorization implications

Conceptual targets:

```text
execution.task_reassign
execution.task_unassign
```

Must validate: actor · permission · order scope · plan scope · task scope · current employee context · new employee context.  
Do **not** silently reuse `execution.task_assign` as sufficient. If matrix cannot host new keys without policy change → document and return to Owner before implementation.

---

## Observability implications (future events)

```text
TASK_REASSIGNMENT_SUCCEEDED
TASK_REASSIGNMENT_CONFLICT
TASK_REASSIGNMENT_BLOCKED_STATE
TASK_REASSIGNMENT_ELIGIBILITY_DENIED
TASK_REASSIGNMENT_AUTH_DENIED
TASK_REASSIGNMENT_IDEMPOTENT_RETRY
TASK_UNASSIGNMENT_SUCCEEDED
TASK_UNASSIGNMENT_BLOCKED_STATE
TASK_UNASSIGNMENT_AUTH_DENIED
```

Allowed fields: safe actor ID, role, order/plan/task IDs, previous/new employee IDs, reason code, result code, task state, timestamp, correlation ID.  
Forbidden: salary, hourly cost, CNP, address, phone, private email, JWT, Authorization, commercial/internal cost, complete `tasks_json`, full employee object.

---

## UI policy (future — not this task)

Backend + persistence contract must be proven before any reassignment UI. Future UI may show current employee, new eligible employee, reason code, task state, and an explicit warning that reassignment does not schedule or start work. Must not claim available now / ready to start / scheduled / machine reserved.

---

## Dead pieces (record only — nothing removed)

| Piece | Class |
| ----- | ----- |
| Public `allow_reassign=true` | `BLOCKED_LEGACY` |
| `clear_plan_task_assignment` | `ACTIVE_LEGACY` (Mobile rollback helper; not public unassign) |
| Direct reassignment / overwrite helpers | `BLOCKED_LEGACY` / `SUPERSEDED` |
| Mobile claim takeover | `BLOCKED_LEGACY` (frozen) |
| Mobile `start_from_available` | `BLOCKED_LEGACY` (frozen) |
| Old UI reassignment actions | `UNKNOWN` / absent as authorized product controls |
| Legacy tests exercising bypass reassign | `ACTIVE_LEGACY` / migrate under future GO |

```text
Dead pieces removed: NONE
```

---

## Next step

Phase A schema + backfill **VERIFIED** — see Wave 10 worklog and `REASSIGNMENT_TRANSITION_PERSISTENCE_SCHEMA_DECISIONS.md`.

```text
FUTURE CANDIDATE:
PHASE_B_CONTROLLED_PRE_START_REASSIGNMENT_BACKEND_IMPLEMENTATION
```

Do **not** implement reassignment or unassignment without a Phase B Owner GO.
