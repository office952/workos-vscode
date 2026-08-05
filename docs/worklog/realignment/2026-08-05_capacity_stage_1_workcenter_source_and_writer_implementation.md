# Capacity Stage 1 — Workcenter Source and Writer Implementation

**Task:** `CAPACITY_STAGE_1_WORKCENTER_SOURCE_AND_WRITER_IMPLEMENTATION`  
**Owner GO:** `AUTHORIZE_CAPACITY_STAGE_1_WORKCENTER_SOURCE_AND_WRITER_IMPLEMENTATION`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `f4fbf051`  
**Code commit:** `88469c1d`  
**Docs commit / Final HEAD:** `6c8c327c`  
**Prerequisite:** `CAPACITY_SOURCE_AND_WRITER_DECISION = PASS`

---

## Verdict

```text
CAPACITY_STAGE_1 = PASS
WORKCENTER_CAPACITY_SOURCE = IMPLEMENTED
CAPACITY_ALLOCATION_WRITER = IMPLEMENTED
RESOURCE_SCOPE = WORKCENTER_ONLY
CAPACITY_UNIT = minutes
PLANNING_BUCKET = DAY
CAPACITY_SOURCE_CAS = VERIFIED
CAPACITY_SOURCE_IDEMPOTENCY = VERIFIED
CAPACITY_ALLOCATION_CAS = VERIFIED
CAPACITY_ALLOCATION_IDEMPOTENCY = VERIFIED
WARN_ONLY = VERIFIED
HARD_BLOCK = VERIFIED
ALLOW_WITH_REASON = VERIFIED
TASK_WORKLOAD_NULL_PRESERVED = VERIFIED
SOURCE_LABELS = VERIFIED
ATOMIC_HISTORY = VERIFIED
CONCURRENCY = VERIFIED
R6_EVALUATOR_INTEGRATION = VERIFIED
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_SOURCE_ROWS = 0
QA_CAPACITY_ALLOCATION_ROWS = 0
QA_OPERATIONAL_STATE = UNCHANGED
CAPACITY_QA_ACTIVATION = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
PHASE_B_CAPACITY_CONSUMER = NOT_IMPLEMENTED
```

---

## Schema gap

```text
SCHEMA_CHANGE_REQUIRED = YES
code Alembic = s65_workcenter_capacity_source
QA Alembic = s64_resource_state_persistence
QA rollout = NOT_AUTHORIZED
```

No persistent Owner available-minutes authority existed before Stage 1. Rejected shortcuts: `capacity_metadata`, rates, HR, sessions.

---

## What landed

| Piece | Location |
| ----- | -------- |
| Migration s65 | `backend/alembic/versions/s65_workcenter_capacity_source.py` |
| Source ORM | `backend/models/workcenter_capacity_source.py` |
| Source commands | `workcenter_capacity_source_command_service.py` |
| Allocation writer | `execution_task_capacity_allocation_command_service.py` |
| DAY helpers | `capacity_day_bucket.py` |
| Routes | `/api/v1/execution/resource-state/workcenter-capacity*` · `/allocations*` |
| Permissions | `execution.capacity_source.manage` · `execution.capacity_allocation.manage` |
| Tests | `tests/test_capacity_stage_1_workcenter_source_and_writer.py` |

`DOMAIN_WRITER_READY["CAPACITY_ALLOCATION"] = True` in code. Activation still requires **s65 tables**; QA on s64 remains blocked with `ACTIVATION_BLOCKED_MISSING_WRITER_AND_SOURCE`.

---

## Contracts enforced

- Source: `workcenter_code` + DAY + `available_minutes` + policy + labels + CAS/idempotency + append-only history.
- Allocation: WORKCENTER only, `unit=minutes`, exact DAY bounds, labeled workload, null minutes rejected (never coerced to 0).
- Over-allocation: WARN_ONLY (default) / HARD_BLOCK / ALLOW_WITH_REASON — detail on result, not a fifth evaluator state.
- Aggregate SQL for open minutes by workcenter + exact DAY window.

---

## Isolated proof

```text
pytest tests/test_capacity_stage_1_workcenter_source_and_writer.py
pytest tests/test_resource_state_r10_activation_readiness.py
pytest tests/test_resource_state_r7_configuration_command.py (capacity activation case updated)
```

Temporary SQLite + alembic `upgrade head` (s65). Capacity domain activated only in isolated DB.

---

## QA zero-mutation

| Check | Value |
| ----- | ----- |
| QA SHA | `3b80f9a8…` (unchanged from R11) |
| Alembic | `s64` |
| Scheduling / Reservation | ACTIVE / ACTIVE |
| Capacity config | 0 |
| workcenter_capacity_sources table | absent |
| capacity allocation rows | 0 |
| assignment transitions | 7 |
| foreign_key_check | 0 |

---

## Phase B

```text
CAPACITY_WRITER = IMPLEMENTED
PHASE_B_CAPACITY_CONSUMER = NOT_IMPLEMENTED
PHASE_B_WIRING = NOT_AUTHORIZED
```

Future policy retained: open HELD/ALLOCATED blocks pre-start reassignment until transfer exists.

---

## Impact

```text
/modules:
Capacity Stage 1 writer exists in code
source = workcenter/day minutes
QA Capacity remains inactive

/governance:
Owner-configured capacity authority
source labels
AI preview limitation (execution_truth=false)
over-allocation policy
activation and QA rollout remain Owner-gated
```

---

## Next step (not started)

```text
FUTURE CANDIDATE:
CAPACITY_STAGE_1_CANONICAL_MIGRATION_AND_QA_ROLLOUT_READINESS
```

Push: **none**.
