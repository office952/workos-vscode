# Worklog — CREATE_MACHINE_RUN minimal runtime implementation

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_CREATE_MACHINE_RUN_MINIMAL_RUNTIME_IMPLEMENTATION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `f959fe3a`  
**Tip HEAD:** `9d8d759b`  
**Verdict:** **PASS**  
**Scope:** CREATE only · isolated DB proof · QA zero-mutation · no UI · no push

---

## Verdict block

```text
CREATE_MACHINE_RUN_MINIMAL_RUNTIME_IMPLEMENTATION = PASS
COMMAND = CREATE_MACHINE_RUN
RUNTIME_IMPLEMENTATION = VERIFIED
MIN_PARTICIPANTS = 2
PARTICIPANT_IDENTITY = EXECUTION_PLAN_ID_PLUS_TASK_KEY
TASK_TRUTH = EXECUTION_PLAN_V2_OPERATIONAL_TASKS
MACHINE_BOUND_VALIDATION = VERIFIED
CAPABILITY_VALIDATION = VERIFIED
BATCH_ELIGIBILITY_VALIDATION = VERIFIED
MACHINE_SELECTION_VALIDATION = VERIFIED
INITIAL_RUN_STATUS = HELD
INITIAL_RESERVATION_STATUS = HELD
RUN_ROWS_CREATED_PER_SUCCESS = 1
RUN_RESERVATIONS_CREATED_PER_SUCCESS = 1
PARTICIPANT_ROWS_CREATED = N
ATOMIC_TRANSACTION = VERIFIED
IDEMPOTENCY = VERIFIED
SINGLE_OVERLAP_ENGINE = VERIFIED
ACTIVE_MEMBERSHIP_GUARD = VERIFIED
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
R6_POST_CREATE = VERIFIED
QA_MUTATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
AUTO_BATCH = NOT_IMPLEMENTED
MACHINE_RUN_LIFECYCLE = CREATE_ONLY
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## API

```text
POST /api/v1/execution/resource-state/machine-runs
permission = execution.machine_run.manage
```

---

## Proof commands

```text
pytest tests/test_create_machine_run_minimal_runtime.py -q
pytest tests/test_resource_state_r9_reservation_writer.py tests/test_resource_state_r10_activation_readiness.py tests/test_machine_run_reservation_grain_schema_foundation.py tests/test_face_cnc_cut_machine_requirement_e2e.py tests/test_vector_prep_duration_e2e_completeness.py -q
```

All PASS (isolated). QA not mutated.

---

## QA zero-mutation

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs/participants/transitions/reservations = 0
assign_tr = 7
fk_check = []
plan 21 SHA = 75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59
plan 22 SHA = 0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97
plan 23 SHA = 00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
plan 23 operational_tasks = 13
```

```text
PUSH = NO
FRONTEND_CHANGED = NO
```

---

## Method

1. Reused R9 window/machine/overlap/domain/transition patterns; added internal run-owned reservation create (no public task-only API change).
2. Demand stamps read from EP `operational_tasks[]`; client sends identities + machine + window only.
3. Atomic insert order: run → reservation → participants → histories; failures roll back all.
4. Machine inventory capability hard-join only when `machines.capabilities` non-empty (readiness MVP).
5. No lifecycle beyond CREATE; no QA POST; no UI.
