# MACHINE_RUN / Reservation grain — Controlled QA s66 schema rollout

**Task:** `MACHINE_RUN_RESERVATION_GRAIN_CONTROLLED_QA_S66_SCHEMA_ROLLOUT`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_RESERVATION_GRAIN_CONTROLLED_QA_S66_SCHEMA_ROLLOUT`  
**Date:** 2026-08-07  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `e584bee3`  
**Tip HEAD:** `42d163587e910d240c82ad03eef75bd62226a67a`  
**Prerequisite:** `MACHINE_RUN_RESERVATION_GRAIN_SCHEMA_FOUNDATION = PASS`

---

## Verdict

```text
MACHINE_RUN_RESERVATION_GRAIN_QA_S66_ROLLOUT = PASS
CONTROLLED_QA_S66_SCHEMA_ROLLOUT = VERIFIED
QA_ALEMBIC_BEFORE = s65_workcenter_capacity_source
QA_ALEMBIC_AFTER = s66_machine_run_reservation_grain
MACHINE_RUN_TABLES = PRESENT_EMPTY
MACHINE_RUN_ROWS = 0
MACHINE_RUN_PARTICIPANTS = 0
MACHINE_RUN_TRANSITIONS = 0
RESERVATION_OWNER_MODEL = TASK_OR_MACHINE_RUN
OWNER_XOR_CONSTRAINT = VERIFIED
TASK_RESERVATION_COMPATIBILITY = VERIFIED
SYNTHETIC_RUN_BACKFILL = 0
SINGLE_OVERLAP_ENGINE = VERIFIED
R6_REGRESSION = VERIFIED
SQLITE_FOREIGN_KEYS = VERIFIED_ON
QA_FOREIGN_KEY_VIOLATIONS = 0
PROTECTED_BASELINE_DIFF = NONE
QA_OPERATIONAL_DATA_DIFF = NONE
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## Mutation counters

```text
QA_ALEMBIC_UPGRADE_CALLS = 1
QA_ALEMBIC_DOWNGRADE_CALLS = 0
QA_SCHEMA_MUTATIONS = s65_TO_s66_ONLY
QA_DATA_MUTATIONS = 0
QA_MACHINE_RUN_COMMANDS = 0
QA_PARTICIPANT_COMMANDS = 0
QA_MACHINE_RESERVATION_COMMANDS = 0
QA_SCHEDULING_COMMANDS = 0
QA_CAPACITY_COMMANDS = 0
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
```

---

## Repo / QA identity

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `e584bee3` |
| QA path | `C:\w\psiso\backend\dev.db` |
| Code Alembic head | `s66_machine_run_reservation_grain` |
| QA Alembic before | `s65_workcenter_capacity_source` |
| QA Alembic after | `s66_machine_run_reservation_grain` |
| QA SHA before | `b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4` |
| QA SHA after | `b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1` |
| Schema fingerprint before | `a7f441fda6ac3048f92960ce4fbedba3f92e43d0157767d9566b5bf7d303cb3d` |
| Schema fingerprint after | `51e442d471529de20b69a2974be14a16525f77ce2e8838a9e6177dc2c0237644` |
| Backup | `backend/_qa_backups/s66_machine_run_reservation_grain/20260807_143324/dev.db.pre_s66.bak` |
| Backup SHA | `b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4` (= preflight QA SHA) |

Backup is **not** committed.

---

## Preflight

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = e584bee3
code Alembic = s66
QA Alembic = s65
Scheduling = ACTIVE
Machine Reservation = ACTIVE
Capacity = NOT_CONFIGURED
reservation rows = 0
machine_runs tables = absent
capacity source/alloc = 0
assignment transitions = 7
foreign_key_check = 0
```

Protected plans SHAs (unchanged through rollout):

| Plan | Order | tasks_json SHA |
| ---- | ----- | -------------- |
| 21 | 973019 | `75933211…` |
| 22 | 880811 | `0ec2dce6…` |
| 23 | 880750 | `00ee947c…` |

Plan 23: 13 tasks · LED → employee 7 · assigned=1 · unassigned=12 · assign_tr_fp `79aca87d…` · config_fp `8cc6cc88…`

---

## Migration

1. Maintenance stop (`stop-dev.ps1` + release leftover :8000 holder).
2. Byte backup verified open as s65, FK check empty, assign_tr=7, no `machine_runs`.
3. `alembic current` → s65.
4. `alembic upgrade s66_machine_run_reservation_grain` (single call).
5. `alembic current` → s66 (head).
6. No stamp / no `create_all` / no manual DDL.

---

## Structural verification

- Tables present empty: `machine_runs`, `machine_run_participants`, `machine_run_transitions`.
- Reservation XOR CHECK present; `machine_run_id` column present.
- Transition `owner_form` + `machine_run_id` present.
- Open task unique index retained with `machine_run_id IS NULL` predicate.
- FK check = 0 · foreign_keys ON at verification.
- Reservation / schedule / capacity / MACHINE_RUN row counts all 0.
- Synthetic run backfill = 0.

---

## Runtime

- Detached stack restarted; `GET /health` → `{"status":"healthy"}`.
- R6 read-only (plan 23 LED): Scheduling CLEAR · Reservation CLEAR · Capacity NOT_CONFIGURED · Aggregate BLOCKED_NOT_CONFIGURED.
- MACHINE_RUN runtime commands not present / not invoked.

---

## Isolated regressions

```text
test_machine_run_reservation_grain_schema_foundation.py
test_resource_state_r9_reservation_writer.py
test_resource_state_r6_read_evaluator.py
test_resource_state_r10_activation_readiness.py
test_face_cnc_cut_machine_requirement_e2e.py
test_vector_prep_duration_e2e_completeness.py
→ 64 passed
```

---

## `/modules` · `/governance`

```text
NO_UI_CHANGE
```

Pages do not expose Alembic / schema-foundation readiness chips. Architecture docs record: schema available in QA ≠ MACHINE_RUN runtime active.

---

## Rollback

```text
ROLLBACK = NOT_REQUIRED
```

---

## Boundaries

```text
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
QA_ROLLOUT_RUNTIME = NOT_AUTHORIZED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
PUSH = NO
```
