# Worklog — MACHINE_RUN + Reservation grain schema foundation

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_RESERVATION_GRAIN_SCHEMA_FOUNDATION`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `dbbc7015`  
**Tip HEAD:** _(set by tip commit)_  
**Verdict:** **PASS**  
**Scope:** schema + ORM + read compatibility · **no MACHINE_RUN command runtime** · QA not migrated

---

## Verdict block

```text
MACHINE_RUN_RESERVATION_GRAIN_SCHEMA_FOUNDATION = PASS
CODE_ALEMBIC_HEAD = s66_machine_run_reservation_grain
QA_ALEMBIC = s65_workcenter_capacity_source
RESERVATION_OWNER_MODEL = TASK_OR_MACHINE_RUN
OWNER_XOR_CONSTRAINT = VERIFIED
TASK_RESERVATION_BACKWARD_COMPATIBILITY = VERIFIED
MACHINE_RUN_TABLES = IMPLEMENTED
PARTICIPANT_TABLE = IMPLEMENTED
TRANSITION_HISTORY = IMPLEMENTED
SINGLE_OVERLAP_ENGINE = VERIFIED
CAS_IDEMPOTENCY_FOUNDATION = VERIFIED
R6_RUN_RESERVATION_READ_PATH = VERIFIED
ATOMIC_RUN_RESERVATION_PARTICIPANT_PERSISTENCE = VERIFIED
FRESH_MIGRATION = VERIFIED
S65_TO_NEW_HEAD = VERIFIED
DOWNGRADE_REUPGRADE = VERIFIED
FK_CHECK = 0
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
QA_ROLLOUT = NOT_AUTHORIZED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## Design choices

| Topic | Decision |
| ----- | -------- |
| Ownership link | One-direction `reservation.machine_run_id → machine_runs.id` UNIQUE (no `machine_runs.reservation_id`) to avoid circular FK |
| Semantic ownership | Unchanged D4: MACHINE_RUN owns the reservation; lookup by `machine_run_id` |
| XOR | CHECK on reservation current row + transition owner snapshot |
| Overlap | Unchanged `find_overlapping_open` (machine-centric) |
| R6 | `list_reservations_visible_to_task` = task-owned ∪ participant→run-owned |
| Runtime | No CREATE_RUN / ADD_PARTICIPANT APIs |

---

## Migration

```text
s66_machine_run_reservation_grain
revises s65_workcenter_capacity_source
```

- Creates `machine_runs`, `machine_run_participants`, `machine_run_transitions`
- Relaxes reservation plan/task/order nullability; adds `machine_run_id`
- Transition `owner_form` + `machine_run_id` snapshot
- Existing rows remain TASK-owned; no synthetic MACHINE_RUN
- Downgrade blocked if run-owned reservations exist

---

## Tests run

```text
test_machine_run_reservation_grain_schema_foundation.py
test_resource_state_r9_reservation_writer.py
test_resource_state_r6_read_evaluator.py
test_resource_state_r10_activation_readiness.py
test_face_cnc_cut_machine_requirement_e2e.py
test_vector_prep_duration_e2e_completeness.py
test_capacity_stage_1_canonical_migration_closure.py
test_resource_state_r4_canonical_migration_closure.py
```

---

## QA zero-mutation

```text
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
QA Alembic = s65
machine_runs tables = absent
reservation rows = 0
assignment transitions = 7
foreign_key_check = 0
```

```text
PUSH = NO
FRONTEND_CHANGED = NO
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
```
