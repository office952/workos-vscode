# Resource State Program R11 — Controlled QA Scheduling & Reservation Activation

**Task:** `RESOURCE_STATE_PROGRAM_R11_CONTROLLED_QA_SCHEDULING_AND_RESERVATION_ACTIVATION`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R11_CONTROLLED_QA_SCHEDULING_AND_RESERVATION_ACTIVATION`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `ac3ef4ed`  
**Prerequisite:** `RESOURCE_STATE_PROGRAM_R10 = PASS` (activation readiness; OPTION_A)

---

## Verdict

```text
RESOURCE_STATE_PROGRAM_R11 = PASS
CONTROLLED_QA_DOMAIN_ACTIVATION = VERIFIED
QA_SCHEDULING_CONFIGURATION = ACTIVE
QA_MACHINE_RESERVATION_CONFIGURATION = ACTIVE
QA_CAPACITY_CONFIGURATION = NOT_CONFIGURED
QA_CONFIGURATION_ROWS = 2
QA_CONFIGURATION_TRANSITIONS = 2
QA_SCHEDULE_ROWS = 0
QA_RESERVATION_ROWS = 0
QA_CAPACITY_ROWS = 0
QA_SCHEDULING_STATE = CLEAR
QA_MACHINE_RESERVATION_STATE = CLEAR
QA_CAPACITY_STATE = NOT_CONFIGURED
QA_AGGREGATE = BLOCKED_NOT_CONFIGURED
PROTECTED_BASELINE_DIFF = NONE
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
R12 = NOT_AUTHORIZED
```

---

## Owner GO readback

Authorized: maintenance window, QA backup, activate SCHEDULING then MACHINE_RESERVATION via R7 command, configuration transition history, CAS/idempotency verification, backend restart, read-only evaluator proof, rollback plan, documentation.

Forbidden: capacity activation, schedule/reservation/capacity row creation, Phase B wiring, Phase C, task mutation, frontend, Employee Mobile, new migration, push / PR / merge / deploy.

Mutation budget observed:

```text
QA_CONFIGURATION_ROWS_CREATED = 2
QA_CONFIGURATION_TRANSITIONS_CREATED = 2
QA_SCHEDULE_ROWS_CREATED = 0
QA_RESERVATION_ROWS_CREATED = 0
QA_CAPACITY_ROWS_CREATED = 0
QA_OPERATIONAL_TASK_MUTATIONS = 0
```

---

## Repo / QA identity

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `ac3ef4ed` |
| Served commit (post-restart) | `ac3ef4ed` |
| QA path | `C:\w\psiso\backend\dev.db` |
| QA Alembic | `s64_resource_state_persistence` |
| QA SHA before | `57fc48730108c8a9022d8151ddaa1f809a51cdfeff2174f2fb6f6ba293d463e9` |
| QA SHA after | `3b80f9a8b8071dd6a4addbf553ba372f018e131dde52e937c2d249fb02d5bea2` |
| Foreign tracked product changes | none (docs-only commit for this GO) |

---

## Preflight

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = ac3ef4ed
QA Alembic = s64
QA foreign_key_check = 0
QA configurations = 0
QA configuration transitions = 0
QA schedules = 0
QA reservations = 0
QA capacity allocations = 0
QA assignment transitions = 7
```

No unexpected Resource State configurations or operational RS rows → preflight continue.

---

## Backup

| Item | Value |
| ---- | ----- |
| Path | `backend/_qa_backups/r11_controlled_activation/20260805_120129/dev.db` |
| SHA | `57fc4873…` (byte-match source) |
| Size | 36388864 |
| integrity_check | ok |
| foreign_key_check | 0 |
| Alembic in backup | s64 |
| configs / transitions in backup | 0 / 0 |

Stack stopped under Owner R11 maintenance GO before backup (`stop-dev.ps1`; orphan uvicorn child cleared). Without this backup, activation would have STOPped.

---

## Activation (canonical R7 — no SQL, no legacy bypass)

Order: **1. SCHEDULING → 2. MACHINE_RESERVATION**.

Command path: `configure_resource_domain` (`resource_domain_configuration_command_service.py`).

| Field | Value |
| ----- | ----- |
| target_status | ACTIVE |
| expected_version | 0 |
| reason_code | `QA_CONTROLLED_DOMAIN_ACTIVATION` |
| actor | `qa-r11-authorized-admin` |
| application_scope_key | `application` |

| Domain | configuration_id | version | status | transition_id | idempotency_key |
| ------ | ---------------- | ------- | ------ | ------------- | --------------- |
| SCHEDULING | 1 | 1 | ACTIVE | `c8e045ec-79bf-4f57-b16c-1057ecd3e7df` | `df1260a9-f21b-47ed-9778-0dc22f614464` |
| MACHINE_RESERVATION | 2 | 1 | ACTIVE | `0746e3b9-cf73-48c5-a583-ef9a0e5f707f` | `b49c6a66-872b-4feb-91f8-20f5d75edc8f` |

CAS / idempotency:

- Stale `expected_version=0` after create → rejected (`cas_stale`).
- Idempotent replay of each key → `already_applied=True`, same transition_id, no extra rows.
- Capacity ACTIVE attempt → `ACTIVATION_BLOCKED_MISSING_WRITER_AND_SOURCE` (expected).

---

## Post-activation counts

| Table | Count |
| ----- | ----- |
| resource_domain_configurations | 2 |
| resource_domain_configuration_transitions | 2 |
| execution_task_schedules | 0 |
| execution_task_schedule_transitions | 0 |
| execution_task_machine_reservations | 0 |
| execution_task_machine_reservation_transitions | 0 |
| execution_task_capacity_allocations | 0 |
| execution_task_capacity_allocation_transitions | 0 |
| execution_task_assignment_transitions | 7 |

CAPACITY_ALLOCATION: **no configuration row**.

---

## Evaluator proof (plan 23 · LED task)

Task key: `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters`

```text
SCHEDULING = CLEAR          (configured=True, no blocking rows)
MACHINE_RESERVATION = CLEAR (configured=True, no blocking rows)
CAPACITY_ALLOCATION = NOT_CONFIGURED
AGGREGATE = BLOCKED_NOT_CONFIGURED
aggregate_reason_code = domain_not_configured
```

`CLEAR` here means the domain is ACTIVE and has no recorded blockers. It does **not** mean reassignment is allowed, Phase B is wired, or Phase C is ready.

---

## Protected baseline

| Check | Result |
| ----- | ------ |
| order 880750 / plan 23 | present |
| operational tasks | 13 |
| LED → employee 7 | yes |
| assigned / unassigned | 1 / 12 |
| assignment transitions | 7 |
| plan 23 `tasks_json` SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` (unchanged) |
| 880811 / plan 22 | unchanged |
| 973019 / plan 21 | unchanged |
| 88002 | absent |
| F7I EUR rates (ACM_BOXED_ASSEMBLY=15, ACM_PANEL_CUTTING/CNC=1.5 present) | unchanged |
| sessions / machine assignments tables | none / N/A (0) |

```text
PROTECTED_BASELINE_DIFF = NONE
```

---

## Backend restart & smoke

- Restarted via `.\scripts\dev-detached.ps1` (Owner R11 GO).
- Health: `GET /health` → healthy.
- Served commit = `ac3ef4ed` (repo HEAD; no code change in activation path).
- App session `PRAGMA foreign_keys = 1`, `foreign_key_check = 0`, Alembic `s64`.
- Configuration read: SCHEDULING ACTIVE v1 · MACHINE_RESERVATION ACTIVE v1 · CAPACITY absent.
- R6 evaluator (post-restart): CLEAR / CLEAR / NOT_CONFIGURED / BLOCKED_NOT_CONFIGURED.
- Schedule/reservation writers **not** invoked against QA.

---

## Rollback status

```text
ROLLBACK = NOT_REQUIRED
```

Triggers (config≠2, unexpected RS rows, FK≠0, baseline drift, aggregate CLEAR, Capacity configured, restart failure) did not fire. Verified backup retained at the path above for future Owner GO restore if needed.

---

## Boundaries held

```text
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
CAPACITY_ACTIVATION = NOT_PERFORMED
FRONTEND = UNCHANGED
EMPLOYEE_MOBILE = UNCHANGED
PUSH = NONE
```

---

## Impact — Harta sistemelor (`/modules`)

```text
Scheduling active in QA
Machine Reservation active in QA
Capacity not configured
no operational rows
```

## Impact — Guvernanța sistemului (`/governance`)

```text
domain activation performed by controlled Owner GO
configuration history canonical
Capacity activation still blocked
Phase B still unwired
```

---

## Next step (not started)

```text
FUTURE CANDIDATE:
CAPACITY_SOURCE_AND_WRITER_DECISION
```

Do **not** wire Phase B before Capacity truth exists. R12 / Capacity activation / Phase B remain **NOT_AUTHORIZED**.
