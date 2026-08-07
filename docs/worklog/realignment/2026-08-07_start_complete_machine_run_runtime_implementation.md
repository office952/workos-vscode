# Worklog — START / COMPLETE MACHINE_RUN runtime implementation

**Owner GO:** `AUTHORIZE_START_COMPLETE_MACHINE_RUN_RUNTIME_IMPLEMENTATION`  
**Date:** 2026-08-07  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `d4ee200f`  
**Tip HEAD:** `4ad5d3d2`  
**Impl commit:** `b614b92f` · **Docs commit:** `87ea354e`

---

## Verdict

```text
START_COMPLETE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
START_MACHINE_RUN = VERIFIED
COMPLETE_MACHINE_RUN = VERIFIED
RELEASE_AFTER_COMPLETED = VERIFIED
START_TRANSITION = RESERVED_TO_RUNNING
COMPLETE_TRANSITION = RUNNING_TO_COMPLETED
RUNNING_RESERVATION_STATE = RESERVED
COMPLETED_RESERVATION_STATE = RESERVED
STARTED_AT = VERIFIED
COMPLETED_AT = VERIFIED
ACTUAL_RUNTIME = DERIVED_NOT_PERSISTED
PHASE_AWARE_COUPLING = VERIFIED
RUN_RESERVATION_VERSIONING = DUAL_BUMP
TASK_STATE_MUTATIONS = 0
EMPLOYEE_SESSION_MUTATIONS = 0
ASSIGNMENT_MUTATIONS = 0
R6_RUNNING = ACTIVE
R6_COMPLETED = ACTIVE
R6_RELEASED = CLEAR
PERMISSION_START_COMPLETE = execution.machine_run.execute
RELEASE_PERMISSION = execution.machine_run.manage
PAUSE_RESUME = DEFERRED
QA_RUNTIME_MUTATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## Preflight (starting state)

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = d4ee200f
CODE_ALEMBIC = s67_machine_run_execution_status
QA_ALEMBIC = s67_machine_run_execution_status
CREATE / ADD|REMOVE / CONFIRM / RESCHEDULE / RELEASE / CANCEL = PASS
START / COMPLETE = were NOT_IMPLEMENTED → now PASS
```

QA baseline (unchanged after GO — read-only):

```text
QA SHA = bee5f5f74c428fd03cf30ffd7377db00be3fa64716a29ce2652ae9f93b161322
plans 21/22/23 =
  75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59
  0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97
  00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
machine_runs / participants / transitions / reservations = 0
assignment transitions = 7
foreign_key_check = []
domains = MACHINE_RESERVATION ACTIVE · SCHEDULING ACTIVE
QA_START_COMMANDS = 0
QA_COMPLETE_COMMANDS = 0
QA_RUNTIME_WRITES = 0
NEW_QA_DRIFT = NONE
```

---

## What changed (code)

| Area | Change |
| ---- | ------ |
| Coupling | `_assert_coupled` → phase-aware matrix (`RUNNING/RESERVED`, `COMPLETED/RESERVED`, …) + version equality |
| START | `start_machine_run` · RESERVED→RUNNING · reservation stays RESERVED · sets `started_at` · dual version bump · dual history |
| COMPLETE | `complete_machine_run` · RUNNING→COMPLETED · reservation stays RESERVED · sets `completed_at` · dual bump · dual history |
| RELEASE | allowed sources `RESERVED` **or** `COMPLETED` · reservation history uses true previous reservation status |
| Permission | `execution.machine_run.execute` for START/COMPLETE; manage unchanged for RELEASE |
| Routes | `POST …/machine-runs/{id}/start` · `POST …/machine-runs/{id}/complete` |
| Schemas | `StartMachineRunCommand` · `CompleteMachineRunCommand` · result `started_at`/`completed_at` |
| R6 | no code change (still reservation HELD\|RESERVED → ACTIVE) |

**Not touched:** task state · employee sessions · assignments · Capacity · Phase B · frontend · QA writes · PAUSE/RESUME.

---

## Workshop plain language

**START** = “utilajul a început efectiv această rulare.”  
Rezervarea rămâne activă (mașina e încă a noastră). Nu pornește task-uri de angajat și nu creează sesiuni de muncă.

**COMPLETE** = “lucrul pe mașină pentru această rulare s-a terminat.”  
Rezervarea rămâne până la **RELEASE** (eliberarea ferestrei). Nu marchează task-urile ca done și nu închide sesiuni.

**Ce NU fac aceste comenzi:** nu mută starea task-urilor, nu creează/închid sesiuni angajat, nu reasignează oameni, nu schimbă Capacity, nu deschid UI.

---

## Proofs

Isolated (`tmp` DB / alembic head s67):

```text
tests/test_start_complete_machine_run_runtime.py = PASS
```

Regression suite (152 passed):

```text
START/COMPLETE · CREATE · ADD/REMOVE · CONFIRM/RELEASE/CANCEL · RESCHEDULE
R6 · R9 reservation · R9 scheduling · R10 · s67 schema foundation
face_cnc · vector_prep
```

Classification: all green on this branch for the listed suite — **INTRODUCED** coverage for START/COMPLETE; no **PREEXISTING** failures observed in this run.

---

## Phase B boundary (documented only)

```text
MACHINE_RUN RUNNING = future signal for reassignment/unassignment/handoff
PHASE_B_MUTATIONS = 0
PHASE_B = NOT_AUTHORIZED
```

---

## `/modules` · `/governance`

```text
NO_UI_CHANGE (deferred)
```

Truth for docs-backed status:

```text
MachineRun execution lifecycle:
  START + COMPLETE implemented backend
  UI = not implemented
  employee/session coupling = not implemented
  Phase B coupling = not implemented
```

---

## Files

- `backend/services/machine_run_command_service.py`
- `backend/schemas/resource_state_machine_run.py`
- `backend/routers/execution_plan_v2.py`
- `backend/dependencies/permissions.py`
- `backend/tests/test_start_complete_machine_run_runtime.py`
- docs readiness + route + this worklog
