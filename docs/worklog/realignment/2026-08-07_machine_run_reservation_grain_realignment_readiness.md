# Worklog — MACHINE_RUN reservation grain realignment readiness

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `7aef85e1`  
**Tip HEAD:** _(set by tip commit)_  
**Verdict:** **PASS**  
**Scope:** docs-only · read-only audit · **no ORM · no migration · no runtime**

---

## Verdict block

```text
MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS = PASS
CURRENT_RESERVATION_GRAIN = TASK_OWNED
TARGET_RESERVATION_GRAIN = TASK_OR_MACHINE_RUN_OWNED
OWNERSHIP_MODEL = OPTION_B_EXPLICIT_DUAL_OWNERSHIP_FIELDS
OWNER_CONSTRAINT = TASK_OWNER_XOR_RUN_OWNER
TASK_RESERVATION_COMPATIBILITY = PRESERVED
RUN_RESERVATION_MODEL = FINALIZED
OVERLAP_ENGINE = SINGLE_SHARED
CAS_IDEMPOTENCY = FINALIZED
TRANSITION_HISTORY = FINALIZED
R6_TASK_TO_RUN_RESERVATION_PATH = FINALIZED
MACHINE_RUN_CREATE_RESERVATION_FLOW = FINALIZED
SCHEMA_GAP = RESERVATION_OWNER_COLUMNS_PLUS_MACHINE_RUN_TABLES
MIGRATION_ORDER = SINGLE_ATOMIC_SCHEMA_SLICE
BACKFILL_POLICY = NO_SYNTHETIC_RUN_BACKFILL
RUNTIME_IMPLEMENTATION = NOT_STARTED
RESERVATION_SCHEMA_CHANGE = NOT_IMPLEMENTED
MACHINE_RUN_RUNTIME = NOT_IMPLEMENTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## Method

1. Preflight HEAD `7aef85e1` + QA fingerprint (reservation rows = 0, no `machine_runs`).
2. Parallel read-only tracks: (A) reservation schema/writer/API, (B) R6 readers, orchestrator option compare.
3. Selected OPTION_B over polymorphic (A) and dual tables (C) to keep one overlap/CAS/history engine.
4. Docs-only reconciliation; no schema mutation.

---

## Key decisions

| Topic | Decision |
| ----- | -------- |
| Dual forms | Task-owned remains; run-owned added |
| Model | OPTION_B explicit fields + XOR |
| Create flow | Single orchestration command (run + reservation + participants) |
| API | MACHINE_RUN service owns run-level create; keep task POST |
| R6 | Union task-owned rows + participant→run→reservation |
| Migration | One atomic slice: MACHINE_RUN tables + reservation grain |
| Backfill | No synthetic MACHINE_RUN |

---

## QA zero-mutation

```text
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
QA Alembic = s65
Scheduling + Reservation ACTIVE
Capacity NOT_CONFIGURED
reservation rows = 0
machine_runs absent
plans 21/22/23 SHA unchanged
```

---

## Artifacts

| Path | Action |
| ---- | ------ |
| `docs/architecture/MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS.md` | created |
| `docs/architecture/MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS.md` | updated |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | updated |
| this worklog | created |

```text
PUSH = NO
FRONTEND_CHANGED = NO
```
