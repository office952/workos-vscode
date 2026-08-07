# Worklog — MACHINE_RUN minimal command runtime readiness

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `1468e2d3`  
**Tip HEAD:** _(set by tip commit)_  
**Verdict:** **PASS**  
**Scope:** docs-only · no runtime · no QA writes

---

## Verdict block

```text
MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS = PASS
COMMAND = CREATE_MACHINE_RUN
REQUEST_CONTRACT = FINALIZED
RESPONSE_CONTRACT = FINALIZED
ERROR_CONTRACT = FINALIZED
PARTICIPANT_IDENTITY = EXECUTION_PLAN_ID_PLUS_TASK_KEY
MIN_PARTICIPANTS = 2
MACHINE_SELECTION = CLIENT_PROVIDES_MACHINE_ID
CAPABILITY_VALIDATION = FINALIZED
BATCH_ELIGIBILITY_VALIDATION = FINALIZED
FULL_BATCH_COMPATIBILITY = DEFERRED_EXPLICIT_CALLER_SELECTION
INITIAL_RUN_STATUS = HELD
INITIAL_RESERVATION_STATUS = HELD
ATOMIC_TRANSACTION = FINALIZED
IDEMPOTENCY = FINALIZED
OVERLAP_ENGINE = SINGLE_SHARED
ACTIVE_MEMBERSHIP_GUARD = FINALIZED
PERMISSION = execution.machine_run.manage_NEW
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
R6_POST_CREATE_BEHAVIOR = FINALIZED
RUNTIME_IMPLEMENTATION = NOT_STARTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_IMPLEMENTATION_SCOPE = CREATE_MACHINE_RUN_ONLY
NEXT_TASK = NOT_AUTHORIZED
```

---

## Method

1. Confirmed QA s66 empty baseline after rollout.
2. Parallel audits: R9 CREATE/idempotency/overlap; permissions/R6/API conventions.
3. Chose MIN_PARTICIPANTS=2 so MACHINE_RUN does not duplicate task-owned Reservation.
4. Kept demand on EP stamps; client sends identities + machine + window only.
5. Deferred full batch compatibility; explicit caller selection is MVP gate.
6. No runtime code.

---

## Key decisions

| Topic | Decision |
| ----- | -------- |
| Command | `CREATE_MACHINE_RUN` only |
| Min participants | 2 |
| Machine | Client `machine_id` |
| Statuses | run HELD + reservation HELD |
| Permission | new `execution.machine_run.manage` |
| Domain | gate on MACHINE_RESERVATION ACTIVE |
| Idempotency | sorted participant pairs |
| Overlap | reuse `overlap_conflict` |

---

## QA zero-mutation

```text
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
QA Alembic = s66
machine_runs/participants/transitions/reservations = 0
assign_tr = 7
fk_check = 0
```

```text
PUSH = NO
FRONTEND_CHANGED = NO
```
