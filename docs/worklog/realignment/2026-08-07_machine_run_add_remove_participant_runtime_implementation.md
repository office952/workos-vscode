# Worklog — MACHINE_RUN ADD/REMOVE participant runtime implementation

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `6e8d774b`  
**Tip HEAD:** `51a0d4ee`  
**Verdict:** **PASS**  
**Scope:** HELD-only ADD/REMOVE · soft REMOVED · version lockstep · isolated DB · QA zero-mutation · no UI · no push

---

## Verdict block

```text
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
ADD_MACHINE_RUN_PARTICIPANT = VERIFIED
REMOVE_MACHINE_RUN_PARTICIPANT = VERIFIED
ALLOWED_FROM = HELD_ONLY
MIN_ACTIVE_PARTICIPANTS = 2
MACHINE_ID_UNCHANGED = VERIFIED
RESERVATION_WINDOW_UNCHANGED = VERIFIED
RESERVATION_STATUS_UNCHANGED = VERIFIED
RUN_STATUS_UNCHANGED = VERIFIED
SOFT_REMOVE = VERIFIED
ACTIVE_MEMBERSHIP_GUARD = VERIFIED
RUN_VERSION_INCREMENT = VERIFIED
RESERVATION_VERSION_INCREMENT_LOCKSTEP = VERIFIED
CAS = VERIFIED
IDEMPOTENCY = VERIFIED
PARTICIPANT_HISTORY = VERIFIED
R6_ADD = ACTIVE
R6_REMOVE = CLEAR
MULTI_PLAN_ADD = VERIFIED
CREATE_MACHINE_RUN = STILL_PASS
CONFIRM_RELEASE_CANCEL = STILL_PASS
RESCHEDULE_MACHINE_RUN = STILL_PASS
QA_MUTATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
AUTO_BATCH = NOT_IMPLEMENTED
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
POST /api/v1/execution/resource-state/machine-runs/{id}/add-participant
POST /api/v1/execution/resource-state/machine-runs/{id}/remove-participant
```

---

## Behavior

```text
HELD only
ADD → ACTIVE (insert or reactivate REMOVED row)
REMOVE → soft REMOVED (removed_at/by); ACTIVE count ≥ 2
run.version += 1 AND reservation.version += 1
machine / window / status unchanged
R6 ADD → ACTIVE; R6 REMOVE → CLEAR
```

---

## Proof commands

```text
pytest tests/test_machine_run_add_remove_participant_runtime.py -q
pytest tests/test_create_machine_run_minimal_runtime.py tests/test_machine_run_confirm_release_cancel_runtime.py tests/test_reschedule_machine_run_runtime.py -q
pytest tests/test_resource_state_r6_read_evaluator.py tests/test_resource_state_r9_reservation_writer.py tests/test_resource_state_r9_scheduling_writer.py tests/test_resource_state_r10_activation_readiness.py tests/test_machine_run_reservation_grain_schema_foundation.py tests/test_face_cnc_cut_machine_requirement_e2e.py tests/test_vector_prep_duration_e2e_completeness.py -q
```

Results (this GO): ADD/REMOVE **18 passed**; combined regression suite **132 passed**; INTRODUCED failures = 0.

---

## QA zero-mutation

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs/participants/transitions/reservations = 0
assign_tr = 7
fk_check = []
QA_ADD_PARTICIPANT_COMMANDS = 0
QA_REMOVE_PARTICIPANT_COMMANDS = 0
```

```text
PUSH = NO
FRONTEND_CHANGED = NO
```

---

## Method

HELD-only membership edit reusing CREATE eligibility, active-membership guard, domain gate, and dual version lockstep. Soft REMOVED preserves audit; ADD stamps participant.idempotency_key for structured identity; reservation companion transition records lockstep without window change. No machine reassignment, execution lifecycle, Capacity, or UI.
