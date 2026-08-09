# Controlled Employee Assignment Command Safety

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_CONTROLLED_EMPLOYEE_ASSIGNMENT_COMMAND_SAFETY`  
**Decision:** `A — safe` (no bounded code hardening required)

---

## A. Verdict

```text
CONTROLLED_EMPLOYEE_ASSIGNMENT_COMMAND_SAFETY = PASS
HARDENING_APPLIED = NO
HARDENING_SCOPE = none
```

## B. Repo / HEAD

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = 5daa3b86
MACHINE_RUN_V1_E2E = STABLE_BASELINE_AFTER_HARDENING
MACHINE_RUN_NEXT_FEATURE_DOMAIN = NONE
```

## C. Owner GO

Authorized: current assignment command audit, controlled isolated validation, auth/eligibility/CAS/idempotency/transaction/pre-start/history proofs, bounded hardening only if deterministic safety defect without schema/policy expansion, tests, read-only UI, docs/evidence.

Not authorized / not started: `REASSIGNMENT_PHASE_E`, post-start transfer, session create, scheduling/Capacity activation, MachineRun changes, Employee Mobile, push/PR/merge/deploy.

## D. Current assignment architecture

Operational assignment is a persisted decision on `ExecutionPlan.tasks_json.operational_tasks[]`. Eligibility is a separate read/validation model. Phase B reassignment/unassignment is a distinct command family with append-only transitions and resource/session guards. Scheduling, sessions, Capacity, machine assignment, and MachineRun remain separate domains.

## E. Canonical task source

```text
CANONICAL_TASK_SOURCE = EXECUTION_PLAN_V2_OPERATIONAL_TASKS
```

Not used as assignment truth: `planned_tasks[]`, ProductDefinition/Aggregate, live Intake, frontend free-text, artwork.

## F. Call graph

See `docs/qa/controlled-employee-assignment-command-safety/call-graph.md`.

```text
HTTP assign/reassign/unassign
→ permission
→ controlled_* service
→ plan FOR UPDATE + (ASSIGN: asyncio order lock)
→ eligibility revalidation
→ state/session/(Phase B resource) guards
→ CAS / idempotency
→ atomic persist
→ response
```

## G. Eligibility / write parity

Writer reloads eligibility inside the transactional lock and requires `assigned_employee_id ∈ eligible_employees`. Inactive employees rejected before and inside lock. Read path that advertises eligible must match write acceptance under unchanged state. Dynamic divergence (session active, completed, already assigned) is documented as writer-only guards — not advertised as “eligible = assignable now”.

```text
ELIGIBILITY_WRITE_PARITY = VERIFIED
```

## H. Initial assignment

Isolated tests prove unassigned operational task + eligible active employee → ASSIGN persists once; technical fields (workcenter etc.) unchanged; no session/scheduling/Capacity/machine/MachineRun mutation.

## I. Duplicate behavior

```text
same employee + same task → assignment_outcome already_same / already_assigned (no duplicate rewrite)
different employee via ASSIGN → already_assigned_to_different_employee (409)
```

ASSIGN does not silently become REASSIGN (`allow_reassign` ignored).

## J. Reassignment

Phase B REASSIGN: A→B with `transition_id` + `expected_current_employee_id`, eligibility, session-history + resource guards; one current state; transition recorded.

## K. Unassignment

Phase B UNASSIGN supported pre-start with same guard family; history preserved; no session stop automation.

## L. Phase E boundary

Post-start / active session history → fail-closed.

```text
POST_START_REASSIGNMENT = FAIL_CLOSED_REASSIGNMENT_PHASE_E
```

No pause/handoff/takeover implemented or attempted.

## M. Resource-state guard

Phase B always evaluates `evaluate_resource_guards`. Default non-test: all domains `NOT_CONFIGURED` → block. `WORKOS_PHASE_B_RESOURCE_GUARDS=CLEAR` is TEST_ONLY. Initial ASSIGN intentionally does not allocate/reserve resources (assignment ≠ scheduling).

## N. MachineRun boundary

```text
MACHINE_RUN_MUTATIONS = 0
```

QA `machine_runs = 0` before/after. Assignment does not create/cleanup/transfer MachineRun participants.

## O. Authorization

| Command | Permission | Roles |
|---------|------------|-------|
| assign | `execution.task_assign` | admin, manager, operator |
| reassign | `execution.task_reassign` | admin, manager |
| unassign | `execution.task_unassign` | admin, manager |

Operator/viewer denied reassign/unassign (HTTP 403 proven).

## P. IDOR / security

Unknown order, unknown/forged task, task not on requested plan → reject, zero mutation. Soft role-wide order access remains (not multi-tenant ACL) — expected for current WorkOS role model.

```text
IDOR_PROTECTION = VERIFIED_TASK_PLAN_SCOPE
```

## Q. PII boundary

Assignment logs/responses use employee ids + operational eligibility fields; no salary/hourly/private HR dumps in command path.

```text
PII_BOUNDARY = VERIFIED
```

## R. Pricing / cost boundary

No Pricing Registry / CPP / EIC / employee-cost ranking in assignment writer.

## S. Idempotency

```text
IDEMPOTENCY = PROVEN
ASSIGN = same-employee already_same
PHASE_B = transition_id + payload fingerprint; conflict on different payload
```

## T. CAS

```text
ASSIGN = plan lock + current assignee check
PHASE_B = expected_current_employee_id + transition uniqueness
CAS_CONCURRENCY = PROVEN
```

No last-write-wins overwrite path.

## U. Concurrency

Two-employee ASSIGN race → one winner. Two-session REASSIGN race → one ok + one stale/mismatch.

```text
TWO_EMPLOYEE_RACE = SAFE
```

## V. Eligibility-change race

Employee/eligibility revalidated inside lock before commit → reject if no longer eligible/active.

## W. Task-state race

Completed / active session checked under lock → conflict.

## X. Resource-state race

```text
RESOURCE_STATE_RACE = SAFE
```

Under current placeholder model there is no live CLEAR derived from commitment tables; production path cannot obtain CLEAR; evaluation is mandatory and fail-closed. (Not papered over — architecture does not yet support a live CLEAR→ACTIVE race.)

## Y. Transaction rollback

Phase B: transition insert + tasks_json update commit together; failures → rollback all. ASSIGN: single tasks_json commit with audit consistency check.

```text
TRANSACTIONALITY = PROVEN
```

## Z. Transition history

Phase B rows retain plan, task_key, previous/new employee, operation, actor, reason, timestamp, transition_id. Initial ASSIGN retains embedded provenance fields. History not rewritten.

## AA. Read-after-write parity

Command response matches refreshed plan / consistency `MATCH`.

## AB–AE. Boundaries

```text
SESSION_MUTATIONS = 0
SCHEDULING_MUTATIONS = 0
CAPACITY_MUTATIONS = 0
CAPACITY_ACTIVATION = NO
MACHINE_ASSIGNMENT_MUTATIONS = 0
MACHINE_RUN_MUTATIONS = 0
TASK_STATE_MUTATIONS = 0
```

## AF. Scenario matrix

See `docs/qa/controlled-employee-assignment-command-safety/scenario-matrix.md` (20/20 classified; no S3/S4).

## AG. Hardening applied

```text
HARDENING_APPLIED = NO
```

No deterministic in-scope safety defect requiring code change.

## AH. Regression

```text
77 passed
```

Suites listed in `docs/qa/controlled-employee-assignment-command-safety/regression.md`.

## AI. Browser / UI truth

Read-only: `/execution/880750`, `/modules`, `/governance`. No eligible=assigned / assigned=scheduled conflation on execution surface. Stale MachineRun “Phase B neautorizat” wording on `/modules` = `UI_HARDENING_CANDIDATE` (not fixed here).

## AJ. Dead Pieces

| Piece | Class |
|-------|-------|
| Controlled ASSIGN/REASSIGN/UNASSIGN | `ACTIVE_CANONICAL` |
| Eligibility + readiness GETs | `ACTIVE_CANONICAL` |
| `allow_reassign` on ASSIGN | `SUPERSEDED` / ignored |
| Public non-controlled assign | `DEAD_CANDIDATE` |
| Mobile claim / direct assign | `ACTIVE_LEGACY` (frozen) |
| FE reassign/unassign | absent (`DEAD_CANDIDATE` UI) |
| `clear_plan_task_assignment` | `ACTIVE_LEGACY` helper |

Nothing deleted.

## AK. Modules / Governance

```text
MODULES_IMPACT = NO_CODE_CHANGE
GOVERNANCE_IMPACT = NO_CODE_CHANGE
```

Separation preserved: eligibility ≠ assignment ≠ scheduling ≠ session. Optional future factual sync of Phase B/assignment-safety status on truth pages remains a separate UI hardening candidate.

## AL. QA protection

Before/after baseline JSON identical for plan 23 assignment counts, transitions=7, machine_runs=0.

```text
QA_ASSIGNMENT_COMMANDS = 0
QA_REASSIGNMENT_COMMANDS = 0
QA_UNASSIGNMENT_COMMANDS = 0
QA_MUTATIONS = 0
```

## AM. Schema

```text
DB_SCHEMA_CHANGES = 0
ALEMBIC_REVISION_CREATED = NO
alembic head remains s67_machine_run_execution_status
```

## AN. Docs / evidence

```text
docs/worklog/realignment/2026-08-09_controlled_employee_assignment_command_safety.md
docs/qa/controlled-employee-assignment-command-safety/
```

## AO. Commits

Docs/evidence commit only (this GO found no code defect).

## AP. No-push confirmation

```text
PUSH = NO
PR = NO
MERGE = NO
DEPLOY = NO
```

---

## PASS block

```text
CONTROLLED_EMPLOYEE_ASSIGNMENT_COMMAND_SAFETY = PASS
CANONICAL_TASK_SOURCE = EXECUTION_PLAN_V2_OPERATIONAL_TASKS
CANONICAL_ASSIGNMENT_COMMAND = VERIFIED
INITIAL_ASSIGNMENT = VERIFIED
PRE_START_REASSIGNMENT = VERIFIED
PRE_START_UNASSIGNMENT = VERIFIED
POST_START_REASSIGNMENT = FAIL_CLOSED_REASSIGNMENT_PHASE_E
ELIGIBILITY_WRITE_PARITY = VERIFIED
AUTHORIZATION = VERIFIED
IDOR_PROTECTION = VERIFIED_TASK_PLAN_SCOPE
PII_BOUNDARY = VERIFIED
IDEMPOTENCY = PROVEN
CAS_CONCURRENCY = PROVEN
TRANSACTIONALITY = PROVEN
TWO_EMPLOYEE_RACE = SAFE
ELIGIBILITY_CHANGE_RACE = SAFE
TASK_STATE_RACE = SAFE
RESOURCE_STATE_RACE = SAFE
ASSIGNMENT_TRANSITION_HISTORY = VERIFIED
READ_AFTER_WRITE_PARITY = VERIFIED
TASK_STATE_MUTATIONS = 0
SESSION_MUTATIONS = 0
SCHEDULING_MUTATIONS = 0
CAPACITY_MUTATIONS = 0
MACHINE_ASSIGNMENT_MUTATIONS = 0
MACHINE_RUN_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
NEW_FEATURES = 0
HARDENING_APPLIED = NO
HARDENING_SCOPE = none
QA_ASSIGNMENT_COMMANDS = 0
QA_REASSIGNMENT_COMMANDS = 0
QA_UNASSIGNMENT_COMMANDS = 0
QA_MUTATIONS = 0
MODULES_IMPACT = NO_CODE_CHANGE
GOVERNANCE_IMPACT = NO_CODE_CHANGE
REASSIGNMENT_PHASE_E = DEFERRED
EMPLOYEE_SESSION_COUPLING = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
NEXT_TASK = NOT_AUTHORIZED
```

## Roadmap awareness

```text
Roadmap awareness: 8/10
Cât sunt în direcția stabilită: 95/100%
Metoda de lucru și logica abordării:
  Confirm HEAD + QA fixture → inventory call graph without rebuilding assignment
  → run isolated regression matrix → classify gaps (none S3/S4) → docs/evidence only
Ce este demonstrat sigur:
  Pre-start assign/reassign/unassign command safety under controlled validation
Ce rămâne intenționat separat:
  Phase E post-start transfer, Employee Sessions, Scheduling activation,
  Capacity Stage 1 activation, MachineRun (already closed), ranking/optimization
Dead Pieces Check:
  Catalogued; none removed
Forbidden Scope Respected:
  YES
```

**Next domain (identification only — not authorized):** Owner selects among deferred roadmap items (`REASSIGNMENT_PHASE_E`, Employee Session coupling, Capacity activation, or UI truth sync). Do not auto-start.
