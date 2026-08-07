# Worklog — RESCHEDULE_MACHINE_RUN runtime implementation

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_RESCHEDULE_MACHINE_RUN_RUNTIME_IMPLEMENTATION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `7021982d`  
**Tip HEAD:** `ef95cd2e`  
**Verdict:** **PASS**  
**Scope:** RESCHEDULE only · same machine/participants/status · window move · isolated DB · QA zero-mutation · no UI · no push

---

## Verdict block

```text
RESCHEDULE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
RESCHEDULE_MACHINE_RUN = VERIFIED
ALLOWED_FROM = HELD_RESERVED
TERMINAL_STATES_REJECTED = VERIFIED
MACHINE_ID_UNCHANGED = VERIFIED
PARTICIPANTS_UNCHANGED = VERIFIED
STATUS_UNCHANGED = VERIFIED
WINDOW_MUTATION = VERIFIED
OVERLAP_ENGINE = SINGLE_SHARED
SELF_RESERVATION_EXCLUDED = VERIFIED
CAS = VERIFIED
IDEMPOTENCY = VERIFIED
RUN_HISTORY = VERIFIED
RESERVATION_OLD_NEW_WINDOW_HISTORY = VERIFIED
R6_AFTER_RESCHEDULE = ACTIVE
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
CREATE_MACHINE_RUN = STILL_PASS
CONFIRM_RELEASE_CANCEL = STILL_PASS
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
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/reschedule
```

Request: `reservation_start`, `reservation_end`, `timezone`, `expected_version`, `idempotency_key`, reason*  
Response: shared `CreateMachineRunResult` (`operation=RESCHEDULE_MACHINE_RUN`)

---

## Behavior

```text
HELD     → HELD     + new window
RESERVED → RESERVED + new window
machine_id / participants / status unchanged
R6 remains ACTIVE
overlap via find_overlapping_open(exclude_id=self)
reservation history stores previous_start/end + new_start/end
run history is same-status RESCHEDULE_MACHINE_RUN
```

```text
moving machine reservation window
≠
moving actual shop-floor execution
```

---

## Proof commands

```text
pytest tests/test_reschedule_machine_run_runtime.py -q
pytest tests/test_create_machine_run_minimal_runtime.py tests/test_machine_run_confirm_release_cancel_runtime.py -q
pytest tests/test_resource_state_r6_read_evaluator.py tests/test_resource_state_r9_reservation_writer.py tests/test_resource_state_r9_scheduling_writer.py tests/test_resource_state_r10_activation_readiness.py tests/test_machine_run_reservation_grain_schema_foundation.py tests/test_face_cnc_cut_machine_requirement_e2e.py tests/test_vector_prep_duration_e2e_completeness.py -q
```

Results (this GO): RESCHEDULE **11 passed**; combined regression suite **113 passed** (1 transient domain-test fix then green); no INTRODUCED failures.

---

## QA zero-mutation

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs/participants/transitions/reservations = 0
assign_tr = 7
fk_check = []
plan SHAs unchanged (21/22/23)
QA_RESCHEDULE_COMMANDS = 0
QA_DATA_MUTATIONS = 0
```

```text
PUSH = NO
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
```

---

## Method

Schedule-style in-place window move for MACHINE_RUN commitment. Reuses shared overlap engine with self-exclusion, CAS/idempotency helpers, domain gate, and dual history writers. Does not call SUPERSEDE, does not change machine/participants/status, and does not invent RUNNING/COMPLETED. No Capacity/Phase/UI/QA writes.
