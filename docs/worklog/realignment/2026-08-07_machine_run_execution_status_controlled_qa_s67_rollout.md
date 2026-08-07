# Worklog — MACHINE_RUN execution status controlled QA s67 schema rollout

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_ACCEPT_CURRENT_QA_BASELINE_AND_CONTROLLED_S67_ROLLOUT`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `7cee40b1`  
**Tip HEAD:** `88e30810`  
**Verdict:** **PASS**  
**Scope:** accept QA SHA baseline · stop writers · backup · alembic upgrade s66→s67 · read-only smoke · isolated lifecycle regression · docs · no START/COMPLETE · no push

---

## Verdict block

```text
MACHINE_RUN_EXECUTION_STATUS_QA_S67_ROLLOUT = PASS
QA_BASELINE_ACCEPTED =
7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
KNOWN_BASELINE_DRIFT =
intake_requests.id=50
QA_ALEMBIC_BEFORE =
s66_machine_run_reservation_grain
QA_ALEMBIC_AFTER =
s67_machine_run_execution_status
QA_SHA_AFTER_MIGRATION =
bee5f5f74c428fd03cf30ffd7377db00be3fa64716a29ce2652ae9f93b161322
SCHEMA_FP_AFTER =
4b835caf5bdbcec6272bbabb29e16b69aca1ce44990c4759940c45d0d2ee9489
MACHINE_RUN_RUNNING_COMPLETED_SCHEMA = VERIFIED
STARTED_AT_COMPLETED_AT = VERIFIED
MACHINE_RUN_ROWS = 0
MACHINE_RUN_PARTICIPANTS = 0
MACHINE_RUN_TRANSITIONS = 0
MACHINE_RESERVATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
KNOWN_INTAKE_BASELINE_DIFF = NONE_AFTER_ACCEPTANCE
QA_ALEMBIC_UPGRADE_CALLS = 1
QA_RUNTIME_WRITE_COMMANDS = 0
QA_MACHINE_RUN_COMMANDS = 0
QA_RESERVATION_COMMANDS = 0
QA_ASSIGNMENT_COMMANDS = 0
QA_CAPACITY_COMMANDS = 0
QA_FOREIGN_KEY_VIOLATIONS = 0
EXISTING_MACHINE_RUN_RUNTIME = STILL_PASS
START_MACHINE_RUN = NOT_IMPLEMENTED
COMPLETE_MACHINE_RUN = NOT_IMPLEMENTED
MACHINE_RUN_EXECUTION_STATUS_SCHEMA_FOUNDATION = ACCEPTED_FINAL
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## Maintenance window

```text
stop-dev.ps1 + force-stop orphaned uvicorn worker PID 15560 (parent 29356)
NO_LISTEN_8000 confirmed before backup/migrate
```

---

## Backup (not committed)

```text
path = backend/_qa_backups/s67_machine_run_execution_status/20260807_200138/dev.db.pre_s67.bak
source SHA = 7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
backup SHA = 7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
Alembic at backup = s66_machine_run_reservation_grain
```

---

## Migration

```text
alembic current → s66_machine_run_reservation_grain
alembic upgrade s67_machine_run_execution_status
alembic current → s67_machine_run_execution_status (head)
```

No stamp / create_all / manual SQL.

---

## Schema proof

```text
machine_runs.started_at = present nullable
machine_runs.completed_at = present nullable
ck_machine_run_status includes
  HELD RESERVED RUNNING COMPLETED CANCELLED RELEASED SUPERSEDED
reservation DDL RUNNING/COMPLETED = absent
indexes ix_machine_run_status / ix_machine_run_machine_id preserved
PRAGMA foreign_keys=ON → foreign_key_check = []
```

---

## Protected baseline after

```text
plans 21/22/23 tasks_json SHAs = unchanged
assign_tr_fp = 79aca87d… unchanged
config_fp = 8cc6cc88… unchanged
intake_requests.id=50 delivery_type/updated_at = unchanged accepted baseline
machine_runs/participants/transitions/reservations = 0
capacity rows = 0
```

---

## Restart + read-only smoke

```text
dev-detached.ps1 → :8000/:3000 healthy
served HEAD at restart = 7cee40b1
GET /api/v1/execution/plans/23/resource-requirements → 13 tasks
GET R6 plan 23 LED task →
  Scheduling=CLEAR
  Reservation=CLEAR
  Capacity=NOT_CONFIGURED
  Aggregate=BLOCKED_NOT_CONFIGURED
QA_RUNTIME_WRITE_COMMANDS = 0
post_smoke SHA = same as after migration
```

---

## Isolated lifecycle regression

```text
pytest CREATE + ADD/REMOVE + CONFIRM/RELEASE/CANCEL + RESCHEDULE
= 62 passed
START/COMPLETE not tested (not implemented)
```

---

## UI

```text
NO_UI_CHANGE
MACHINE_RUN execution schema = available in QA
START/COMPLETE = NOT_IMPLEMENTED
```

```text
PUSH = NO
```
