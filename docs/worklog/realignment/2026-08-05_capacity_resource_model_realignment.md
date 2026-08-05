# Capacity Resource Model Realignment

**Task:** `CAPACITY_RESOURCE_MODEL_REALIGNMENT`  
**Owner GO:** `AUTHORIZE_CAPACITY_RESOURCE_MODEL_REALIGNMENT`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `681f1ac0`  
**Architecture:** `docs/architecture/CAPACITY_RESOURCE_MODEL_REALIGNMENT.md`

---

## Verdict

```text
CAPACITY_RESOURCE_MODEL_REALIGNMENT = PASS
MACHINE_BOUND_MODEL = FINALIZED
MACHINE_EXCLUSIVITY = CONFIRMED
MACHINE_BATCH_MODEL = FINALIZED_CONCEPTUALLY
MANUAL_SHARED_WORKSPACE_MODEL = FINALIZED_CONCEPTUALLY
WORKSPACE_EXCLUSIVITY = CONDITIONAL
WORKSPACE_SHARING = SUPPORTED_CONCEPTUALLY
WORKSPACE_CLASS_MODEL = OPTION_A_RECOMMENDED
EMPLOYEE_RESOURCE_BOUNDARY = FINALIZED
TASK_RESOURCE_REQUIREMENT_CONTRACT = BOUNDED_MINIMAL
CAPACITY_STAGE_1_DISPOSITION = OPTION_D_KEEP_IMPLEMENTED_INACTIVE
CAPACITY_STAGE_1_QA_SEED_READINESS = SUPERSEDED_BY_RESOURCE_MODEL_REALIGNMENT
CAPACITY_QA_ACTIVATION = NOT_AUTHORIZED
CAPACITY_QA_SEED = NOT_AUTHORIZED
QA_MUTATIONS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Why seed readiness is superseded

Prior step prepared WC-day minute seeding. Owner clarified that **tables are shareable** and **machines batch multi-job runs**. A single workcenter-minutes model cannot express that honestly. Seed/activation stay **NOT_AUTHORIZED**. Prior report kept for history.

---

## Preflight / QA zero-mutation

```text
HEAD = 681f1ac0
QA Alembic = s65
Scheduling / Reservation = ACTIVE
Capacity config / source / alloc = 0
foreign_key_check = 0
QA SHA = b54d223f… (unchanged)
```

---

## Method

1. Preflight + QA read-only probe.  
2. Explore subagent on reservation / batch / work_area / employee / Stage 1 boundaries.  
3. Direct QA matrix: machines `resource_kind` × WC + ORR.  
4. Owner truths vs repo evidence → classification + disposition OPTION_D.  
5. Docs only — no code, no seed, no activation.

Subagent used for parallel code search; decisions and classification finalized in parent. Overengineering avoided: OPTION_A workspace classes; no m²; bounded task fields; no batch schema invented.

---

## Classification snapshot

| Family | Workcenters |
| ------ | ----------- |
| MACHINE_BATCHABLE | CNC_ROUTING, LETTER_FORMING, LASER, CUT, PRINT |
| MACHINE_EXCLUSIVE | LAMINATE |
| HYBRID | METAL_FAB, VINYL_APPLICATION |
| MANUAL_SHARED_WORKSPACE | ASSEMBLY, LED_ASSEMBLY |
| MANUAL_PERSON_DRIVEN | PREPRESS |
| FIELD_OPERATION | FIELD_INSTALLATION |

---

## Capacity Stage 1

```text
OPTION_D — keep implemented + s65 schema; leave inactive
```

Do not seed generic minutes. Do not activate. Possible later reuse as soft indicator for a narrow subset — not for shared tables.

---

## Next candidate

```text
FUTURE CANDIDATE:
MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISION_PACKAGE
```

---

## Files

| Path | Change |
| ---- | ------ |
| `docs/architecture/CAPACITY_RESOURCE_MODEL_REALIGNMENT.md` | new |
| `docs/worklog/realignment/2026-08-05_capacity_resource_model_realignment.md` | this |
| `docs/architecture/CAPACITY_STAGE_1_QA_CONFIGURATION_AND_SEED_READINESS.md` | superseded status |
| `docs/architecture/CAPACITY_SOURCE_AND_WRITER_DECISION.md` | pointer |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | route |

**No push.**
