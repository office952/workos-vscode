# Worklog — MACHINE_RUN execution status schema foundation

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_EXECUTION_STATUS_SCHEMA_FOUNDATION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `de0f43f4`  
**Tip HEAD:** `d5cbcb52`  
**Verdict:** **PASS**  
**Scope:** s67 schema only · ORM/CHECK parity · migration tests · runtime regression · docs · no START/COMPLETE · no QA migrate · no push

---

## Verdict block

```text
MACHINE_RUN_EXECUTION_STATUS_SCHEMA_FOUNDATION = PASS
CODE_ALEMBIC_HEAD = s67_machine_run_execution_status
QA_ALEMBIC = s66_machine_run_reservation_grain
MACHINE_RUN_STATUS_RUNNING = SUPPORTED
MACHINE_RUN_STATUS_COMPLETED = SUPPORTED
STARTED_AT = IMPLEMENTED_NULLABLE
COMPLETED_AT = IMPLEMENTED_NULLABLE
RESERVATION_STATUS_MODEL = UNCHANGED
MACHINE_RUN_TRANSITION_STATUS_EXPANSION = VERIFIED
ORM_MIGRATION_PARITY = VERIFIED
FRESH_MIGRATION = VERIFIED
S66_TO_NEW_HEAD = VERIFIED
DOWNGRADE_REUPGRADE = VERIFIED_OR_GUARDED
FK_CHECK = 0
EXISTING_MACHINE_RUN_RUNTIME = STILL_PASS
START_MACHINE_RUN = NOT_IMPLEMENTED
COMPLETE_MACHINE_RUN = NOT_IMPLEMENTED
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## Migration

```text
revision = s67_machine_run_execution_status
down_revision = s66_machine_run_reservation_grain
```

Changes:

```text
ck_machine_run_status += RUNNING, COMPLETED
machine_runs.started_at nullable
machine_runs.completed_at nullable
no actual_runtime_minutes column (derive later)
no Reservation status change
```

Downgrade:

```text
blocked if any machine_runs.status IN (RUNNING, COMPLETED)
no remap RUNNING→RESERVED / COMPLETED→RESERVED
otherwise drop columns + restore commitment-only CHECK
```

---

## Coupling matrix (structural; runtime equality unchanged)

```text
run HELD       ↔ reservation HELD
run RESERVED   ↔ reservation RESERVED
run RUNNING    ↔ reservation RESERVED
run COMPLETED  ↔ reservation RESERVED
run RELEASED   ↔ reservation RELEASED
run CANCELLED  ↔ reservation CANCELLED
```

```text
RELEASE_AFTER_COMPLETED = FUTURE_RUNTIME_ADJUSTMENT_REQUIRED
```

---

## Proof commands

```text
pytest tests/test_machine_run_execution_status_schema_foundation.py -q
pytest tests/test_machine_run_reservation_grain_schema_foundation.py tests/test_create_machine_run_minimal_runtime.py tests/test_machine_run_add_remove_participant_runtime.py tests/test_machine_run_confirm_release_cancel_runtime.py tests/test_reschedule_machine_run_runtime.py tests/test_resource_state_r6_read_evaluator.py tests/test_resource_state_r9_reservation_writer.py tests/test_resource_state_r10_activation_readiness.py tests/test_face_cnc_cut_machine_requirement_e2e.py -q
pytest tests/test_resource_state_r3_migration_closure.py tests/test_resource_state_r4_canonical_migration_closure.py tests/test_capacity_stage_1_canonical_migration_closure.py tests/test_finalization_wave10_canonical_migration_closure.py tests/test_capacity_stage_1_workcenter_source_and_writer.py tests/test_vector_prep_duration_e2e_completeness.py -q
```

Results:

```text
s67 foundation = 7 passed
MACHINE_RUN + R6/R9/R10 + face_cnc suite = 123 passed
migration closure + vector_prep = 53 passed, 1 skipped
INTRODUCED failures = 0
```

---

## QA zero-mutation

```text
QA Alembic = s66_machine_run_reservation_grain
CODE Alembic = s67_machine_run_execution_status
QA SHA = 7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
prior tip SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs/participants/transitions/reservations = 0
assign_tr = 7
fk_check = []
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
```

Plans (git hash-object at capture):

```text
21 = 620bffa3834880d21279f874663c551d8f608763
22 = 80bcff38d6e2d29e108159edd5d345a64ff48052
23 = eda962509e8fe16fc945edc97c8cbba739389442
```

```text
PUSH = NO
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
PERMISSION_CHANGES = 0
```

Architecture: `docs/architecture/MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS.md`
