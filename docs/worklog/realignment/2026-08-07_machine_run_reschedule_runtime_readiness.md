# Worklog — MACHINE_RUN reschedule runtime readiness

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `a36e7de3`  
**Tip HEAD:** _(set by tip commit)_  
**Verdict:** **PASS**  
**Scope:** docs-only · no runtime · no QA writes

---

## Verdict block

```text
MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS = PASS
RESCHEDULE_MACHINE_RUN = FINALIZED
ALLOWED_FROM = HELD,RESERVED
MACHINE_ID_CHANGE = FORBIDDEN
STATUS_CHANGE = FORBIDDEN
WINDOW_MUTATION = FINALIZED
OVERLAP_ENGINE = SINGLE_SHARED
CAS = FINALIZED
IDEMPOTENCY = FINALIZED
HISTORY_MODEL = FINALIZED
SCHEMA_SUFFICIENCY = VERIFIED
PARTICIPANTS_UNCHANGED = FINALIZED
R6_BEHAVIOR = ACTIVE_UNCHANGED
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
RUNTIME_IMPLEMENTATION = NOT_STARTED
QA_MUTATIONS = 0
NEXT_IMPLEMENTATION_SCOPE = RESCHEDULE_MACHINE_RUN_ONLY
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## Owner decisions

| ID | Decision |
| -- | -------- |
| D1 | HELD allowed |
| D2 | RESERVED allowed |
| D3 | machine_id unchanged |
| D4 | status unchanged |
| D5 | old+new window on reservation transition |
| D6 | schema sufficient (no migration); run transition is same-status event without window columns |

---

## Key facts

- R9 has no `RESCHEDULE_RESERVATION`; SUPERSEDE is wrong for MACHINE_RUN (status reset + 1:1 UNIQUE).
- Follow schedule-style in-place RESCHEDULE: same status, new window, `exclude_id` overlap.
- Window SoT remains reservation; matches CREATE history pattern.

---

## QA zero-mutation

```text
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
QA Alembic = s66
rows = 0
assign_tr = 7
fk = []
```

```text
PUSH = NO
```
