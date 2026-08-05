# Capacity Stage 1 — Controlled QA Schema Rollout (s65)

**Task:** `CAPACITY_STAGE_1_CONTROLLED_QA_SCHEMA_ROLLOUT`  
**Owner GO:** `AUTHORIZE_CAPACITY_STAGE_1_CONTROLLED_QA_SCHEMA_ROLLOUT`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `27a9248d`  
**Docs commit / Final HEAD:** `cd291b67`  
**Prerequisite:** `CAPACITY_STAGE_1_MIGRATION_READINESS = PASS` (tip `27a9248d`)

---

## Verdict

```text
CAPACITY_STAGE_1_QA_SCHEMA_ROLLOUT = PASS
CONTROLLED_QA_S65_ROLLOUT = VERIFIED
QA_ALEMBIC_BEFORE = s64_resource_state_persistence
QA_ALEMBIC_AFTER = s65_workcenter_capacity_source
WORKCENTER_CAPACITY_SOURCE_TABLES = 2
WORKCENTER_CAPACITY_SOURCE_ROWS = 0
WORKCENTER_CAPACITY_SOURCE_TRANSITIONS = 0
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_ALLOCATION_ROWS = 0
QA_CAPACITY_ALLOCATION_TRANSITIONS = 0
SQLITE_FOREIGN_KEYS = VERIFIED_ON
QA_FOREIGN_KEY_VIOLATIONS = 0
SCHEDULING_CONFIGURATION = ACTIVE_UNCHANGED
MACHINE_RESERVATION_CONFIGURATION = ACTIVE_UNCHANGED
QA_CAPACITY_STATE = NOT_CONFIGURED
QA_AGGREGATE = BLOCKED_NOT_CONFIGURED
PROTECTED_BASELINE_DIFF = NONE
QA_OPERATIONAL_STATE = UNCHANGED
CAPACITY_ACTIVATION = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Owner GO readback

Authorized: maintenance window, stop QA writes, byte backup, `alembic upgrade s64→s65`, structural/zero-row verification, backend restart, read-only smoke, documentation.

Forbidden: Capacity configuration, source/allocation inserts, schedule/reservation writes, Phase B/C, task mutation, frontend, Employee Mobile, stamp/`create_all`, push/PR/merge/deploy.

Mutation budget observed:

```text
QA_ALEMBIC_UPGRADE_CALLS = 1
QA_ALEMBIC_DOWNGRADE_CALLS = 0
QA_SCHEMA_MUTATIONS = s64_TO_s65_ONLY
QA_DATA_MUTATIONS = 0
QA_CAPACITY_CONFIGURATION_COMMANDS = 0
QA_CAPACITY_SOURCE_COMMANDS = 0
QA_CAPACITY_ALLOCATION_COMMANDS = 0
QA_SCHEDULE_COMMANDS = 0
QA_RESERVATION_COMMANDS = 0
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
| Starting HEAD | `27a9248d` |
| Served commit at smoke | `27a9248d` (docs tip after this GO) |
| QA path | `C:\w\psiso\backend\dev.db` |
| Code Alembic head | `s65_workcenter_capacity_source` |
| QA Alembic before | `s64_resource_state_persistence` |
| QA Alembic after | `s65_workcenter_capacity_source` |
| QA SHA before | `3b80f9a8b8071dd6a4addbf553ba372f018e131dde52e937c2d249fb02d5bea2` |
| QA SHA after | `b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4` |
| Schema fingerprint before (full) | `bc2e3d46f37fbfdd3ea42db454087ebe1490d52764b2bd40411008f3de095e60` |
| Schema fingerprint after (full) | `a7f441fda6ac3048f92960ce4fbedba3f92e43d0157767d9566b5bf7d303cb3d` |
| s65-owned fingerprint (QA = isolated) | `ffa4283c8b684d65f0556ced8d524dee6c1fb32524a78de722cee5efc14617f0` |

Full-DB fingerprint differs from a virgin upgrade (historical QA objects). **s65-owned** DDL fingerprint matches the isolated closure reference exactly.

---

## Preflight

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = 27a9248d
git status = no foreign tracked changes
code Alembic head = s65
QA Alembic = s64
foreign_key_check = 0
Scheduling = ACTIVE v1
Machine Reservation = ACTIVE v1
Capacity configuration = 0
schedule/reservation/capacity allocation rows = 0
workcenter_capacity_sources = absent
workcenter_capacity_source_transitions = absent
assignment transitions = 7
backend :8000 PID (pre-stop) = 28668
frontend :3000 PID (pre-stop) = 15876
```

---

## Protected baseline (before)

| Check | Value |
| ----- | ----- |
| order 880750 / plan 23 | present |
| operational tasks | 13 |
| LED task → employee 7 | yes (`…:led_install_letters`) |
| assigned / unassigned | 1 / 12 |
| assignment transitions | 7 |
| assignment transition fingerprint | `9b1f3f387fc03776a797c7e93e4c084d87ef71fd57457cd9e72b609f10304664` |
| plan 23 `tasks_json` SHA256 | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| plan 23 `updated_at` | `2026-08-04 19:16:57.407320` |
| execution_plan count | 21 |
| 880811 / plan 22 | present |
| 973019 / plan 21 | present |
| 88002 | absent |
| F7I | `ACM_BOXED_ASSEMBLY=15` · `ACM_PANEL_CUTTING=1.5` · `CNC_ROUTER=1.5` EUR active |
| sessions / machine assignments | tables absent |

---

## Backup

| Item | Value |
| ---- | ----- |
| Path | `backend/_qa_backups/s65_qa_schema_rollout/20260805_201404/dev.db` |
| SHA256 | `3b80f9a8b8071dd6a4addbf553ba372f018e131dde52e937c2d249fb02d5bea2` |
| Size | 36388864 (byte-match source) |
| integrity_check | ok |
| foreign_key_check | 0 |
| Alembic in backup | `s64_resource_state_persistence` |
| s65 tables in backup | absent |
| domains in backup | SCHEDULING ACTIVE · MACHINE_RESERVATION ACTIVE |

Stack stopped under this Owner GO (`.\scripts\stop-dev.ps1`) before backup. Backup is **not** committed.

---

## Migration

```text
DATABASE_URL = sqlite+aiosqlite:///C:/w/psiso/backend/dev.db
alembic current  → s64_resource_state_persistence
alembic upgrade s65_workcenter_capacity_source
alembic current  → s65_workcenter_capacity_source (head)
alembic heads    → s65_workcenter_capacity_source (single head)
```

No stamp, no manual `alembic_version` edit, no autogenerate, no `create_all`, no manual DDL.

---

## Structural verification

| Object | Result |
| ------ | ------ |
| `workcenter_capacity_sources` | present, empty |
| `workcenter_capacity_source_transitions` | present, empty |
| workload_* on allocations | present (nullable) |
| workload_* on allocation transitions | present (nullable) |
| checks (status/policy/label/minutes/version/…) | present in DDL |
| unique idempotency / transition UUID | present in DDL |
| partial unique ACTIVE (wc, day) | `uq_wc_capacity_source_active_wc_day` |
| indexes status / wc+day / tr source / tr wc+day+created | present |
| FKs superseded_by / source_id RESTRICT | present |
| `PRAGMA foreign_keys` | 1 |
| `PRAGMA foreign_key_check` | 0 |
| s65-owned fingerprint vs isolated | **MATCH** |

---

## Zero-row / configuration proof

```text
workcenter_capacity_sources = 0
workcenter_capacity_source_transitions = 0
execution_task_capacity_allocations = 0
execution_task_capacity_allocation_transitions = 0
execution_task_schedules = 0
execution_task_machine_reservations = 0
CAPACITY_ALLOCATION domain row = absent
SCHEDULING = ACTIVE v1 (unchanged)
MACHINE_RESERVATION = ACTIVE v1 (unchanged)
```

No default workcenter, minutes, AI estimate, Capacity configuration, or synthetic allocation/CLEAR.

---

## Existing-data preservation (after)

| Check | Result |
| ----- | ------ |
| tasks_json SHA | unchanged |
| plan updated_at | unchanged |
| assignment transitions + fingerprint | unchanged (7) |
| Scheduling / Reservation configs | unchanged |
| execution_plan count | 21 unchanged |
| protected orders | unchanged |
| F7I EUR rates | unchanged |

```text
PROTECTED_BASELINE_DIFF = NONE
OPERATIONAL_DATA_DIFF = NONE
SCHEDULING_CONFIGURATION_DIFF = NONE
RESERVATION_CONFIGURATION_DIFF = NONE
```

Allowed diffs only: Alembic revision, schema fingerprint, two empty s65 tables, nullable workload columns, QA DB SHA.

---

## Backend restart & runtime smoke

- Restarted via `.\scripts\dev-detached.ps1` (this Owner GO).
- Backend listen `:8000` PID `29356` · Frontend `:3000` PID `28828`.
- `GET /health` → `{"status":"healthy"}`.
- App FK ON, `foreign_key_check = 0`, Alembic `s65`.
- Capacity source tables exist; source rows = 0; allocations = 0.

R6 evaluator (plan 23 · LED task) — **read-only service call**, no writer commands:

```text
SCHEDULING = CLEAR
MACHINE_RESERVATION = CLEAR
CAPACITY_ALLOCATION = NOT_CONFIGURED
AGGREGATE = BLOCKED_NOT_CONFIGURED
aggregate_reason_code = domain_not_configured
```

`CLEAR` means ACTIVE with no blocking rows — not reassignment permission, not Phase B/C readiness.

---

## Rollback status

```text
ROLLBACK = NOT_REQUIRED
```

Verified backup retained for future Owner GO restore. Triggers (failed migration, wrong revision, FK violations, unexpected Capacity rows, config drift, baseline drift, smoke failure) did not fire.

---

## `/modules` and `/governance`

| Surface | Verdict |
| ------- | ------- |
| `/modules` | **NO_IMPACT** — no UI change; Capacity schema exists in QA but inactive / unconfigured. |
| `/governance` | **NO_IMPACT** — Alembic owns s65; Owner still gates Capacity truth + activation. |

---

## Boundaries held

```text
CAPACITY_ACTIVATION = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
no capacity minutes
no capacity allocations
no task mutation
no frontend / Mobile
no push
```

---

## Next (future candidate only)

```text
FUTURE CANDIDATE:
CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_AND_SEED_READINESS
```

Must inventory real workcenters and factual minutes/day — do **not** invent generic `480` without Owner review.
