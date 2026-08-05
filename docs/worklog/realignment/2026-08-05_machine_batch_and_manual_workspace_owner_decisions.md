# Machine Batch and Manual Workspace — Owner Decision Package

**Task:** `MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISION_PACKAGE`  
**Owner GO:** `AUTHORIZE_MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISION_PACKAGE`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `4ed8aaea`  
**Architecture:** `docs/architecture/MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md`  
**Prerequisite:** `CAPACITY_RESOURCE_MODEL_REALIGNMENT = PASS` (tip `4ed8aaea`)

---

## Verdict

```text
MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISION_PACKAGE = PASS
OWNER_DECISIONS_CONFIRMED = 6_OF_6
MACHINE_RUN_CONTRACT = FINALIZED_CONCEPTUALLY
MANUAL_WORKSPACE_CLASSES = FINALIZED
WORKSPACE_SHARING_POLICY = CONDITIONAL
HYBRID_WORKCENTER_POLICY = FINALIZED
PREPRESS_BOUNDARY = FINALIZED
FIELD_OPERATION_BOUNDARY = FINALIZED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
CAPACITY_ACTIVATION = NOT_AUTHORIZED
CAPACITY_SEED = NOT_AUTHORIZED
QA_MUTATIONS = 0
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## Six confirmed decisions (plain)

1. **HYBRID** — METAL_FAB / VINYL: task declares machine / workspace / people.  
2. **Classes** — SMALL / MEDIUM / FULL_TABLE / LARGE_AREA.  
3. **Share** — cant + small vinyl: conditional (shareable + not FULL_TABLE + no incompatibility).  
4. **MACHINE_RUN** — owns one Machine Reservation; multi-task participants; machine time once.  
5. **PREPRESS** — PERSON_DRIVEN; exclusive station only if factual later.  
6. **FIELD** — outside shop Capacity; separate future model.

---

## QA zero-mutation

```text
rev = s65 · Sched/Res ACTIVE · Capacity 0/0/0 · assign=7 · fk_check=0
SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
```

---

## Method

Docs-only application of Owner-confirmed decisions. Prior realignment read; no parallel contracts invented. No subagent writers. CE applied proportionally: plan = docs scope; self-check vs acceptance; durable decision matrix; conventional docs commit. No runtime, no `/lfg`.

---

## Files

| Path | Change |
| ---- | ------ |
| `docs/architecture/MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md` | new |
| `docs/worklog/realignment/2026-08-05_machine_batch_and_manual_workspace_owner_decisions.md` | this |
| `docs/architecture/CAPACITY_RESOURCE_MODEL_REALIGNMENT.md` | status pointer |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | route |

**No push. No next runtime task started.**
