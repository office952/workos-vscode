# Capacity Source and Writer Decision

**Task:** `CAPACITY_SOURCE_AND_WRITER_DECISION`  
**Owner GO:** `AUTHORIZE_CAPACITY_SOURCE_AND_WRITER_DECISION`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `efc3b190`  
**Docs commit / Final HEAD:** `6072686b`  
**Architecture:** `docs/architecture/CAPACITY_SOURCE_AND_WRITER_DECISION.md`

---

## Verdict

```text
CAPACITY_SOURCE_AND_WRITER_DECISION = PASS
CAPACITY_SOURCE = WORKCENTER_CONFIGURED_CAPACITY
RESOURCE_SCOPE = WORKCENTER_PRIMARY | MACHINE_DEFERRED_STAGE_2
CAPACITY_UNIT = minutes
PLANNING_BUCKET = DAY
TASK_WORKLOAD_SOURCE = LABELED_MINUTES_WITH_NULL_PRESERVED
AI_ESTIMATE_POLICY = PREVIEW_PLANNING_ONLY_NEVER_SILENT_EXECUTION_TRUTH
OVER_ALLOCATION_POLICY = CONFIGURABLE_PER_WORKCENTER_DEFAULT_WARN_ONLY
CAPACITY_WRITER_CONTRACT = FINALIZED
CAPACITY_EVALUATOR_SEMANTICS = FINALIZED
PHASE_B_CAPACITY_POLICY = FINALIZED
IMPLEMENTATION_STRATEGY = OPTION_D_STAGED
CAPACITY_ACTIVATION = NOT_AUTHORIZED
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_ROWS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Owner GO readback

Authorized: read-only audit, capacity domain model, source/scope/unit/bucket decisions, allocation + over-allocation policy, writer contract (design), evaluator + Phase B impact analysis, scale review, staged implementation recommendation, documentation, route update.

Forbidden: capacity writer implementation, QA capacity configuration/allocations, schedule/reservation QA writes, Phase B/C wiring, task mutation, migration, frontend/Mobile, push/PR.

```text
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
```

---

## Preflight

| Check | Result |
| ----- | ------ |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `efc3b190` |
| Foreign tracked changes | none |
| Code / QA Alembic | `s64` |
| Scheduling / Reservation configs | ACTIVE / ACTIVE |
| Capacity configs | 0 |
| schedule / reservation / capacity rows | 0 / 0 / 0 |
| assignment transitions | 7 |
| foreign_key_check | 0 |
| QA SHA | `3b80f9a8b8071dd6a4addbf553ba372f018e131dde52e937c2d249fb02d5bea2` (unchanged from R11) |

---

## Capacity definition (five values)

```text
available  = Owner-configured WC minutes in a DAY bucket
requested  = task workload minutes for allocate intent
allocated  = open HELD|ALLOCATED quantity (demand table exists)
consumed   = Execution Reality actuals (out of triad)
remaining  = available − allocated (derived)
```

Allocation ≠ worked time. Reservation ≠ allocation. Schedule ≠ allocation.

---

## Source / scopes / unit / bucket

| Decision | Value |
| -------- | ----- |
| Source | `WORKCENTER_CONFIGURED_CAPACITY` |
| Strategy | `OPTION_D_STAGED` |
| Scopes | WORKCENTER primary; MACHINE available pool Stage 2; EMPLOYEE out; no RESOURCE_POOL |
| Unit | `minutes` |
| Bucket | `DAY` (SHIFT not canonical RS SoT) |

Rejected supply candidates reconfirmed: rates, HR hours, `capacity_metadata`, dashboard shift util, demand table itself.

---

## Workload / AI / over-allocation

- EP `estimated_time_minutes` may be null — never invent 0; label sources (`OWNER_CONFIGURED` / `SYSTEM_DERIVED` / `AI_DECISION` / `MANUAL_MANAGER` / `UNKNOWN`).
- AI estimates: preview/planning only; never silent execution truth.
- Over-allocation: per-workcenter policy; default `WARN_ONLY`; `HARD_BLOCK` / `ALLOW_WITH_REASON` available later.

---

## Writer / evaluator / Phase B

- Writer commands (design): CREATE / ADJUST / RELEASE / CANCEL / SUPERSEDE — R8 platform (CAS, idempotency, history, plan lock).
- Evaluator: `ACTIVE` = open HELD|ALLOCATED; over-allocation = details/reason, not a new state.
- Phase B (policy only): any open allocation blocks pre-start reassignment until controlled transfer; **not wired**.

---

## Scale

Generic keys `(execution_plan_id, task_key, scope, bucket, minutes)`. Existing WC/machine bucket indexes support Stage-1 sum checks. No per-product capacity logic.

---

## QA zero-mutation proof

Post-decision probe (read-only): configs still Scheduling+Reservation only; capacity rows 0; SHA unchanged; no configure/writer calls.

---

## Impact

```text
/modules:
Capacity source and ownership decision
no Capacity runtime active

/governance:
who configures capacity = Owner (WC available minutes + policy)
source labels + AI decision policy
over-allocation policy
activation Owner gate remains
```

---

## Next step (not started)

```text
FUTURE CANDIDATE:
CAPACITY_STAGE_1_WORKCENTER_SOURCE_AND_WRITER_IMPLEMENTATION
```

---

## Files

| File | Action |
| ---- | ------ |
| `docs/architecture/CAPACITY_SOURCE_AND_WRITER_DECISION.md` | created |
| `docs/worklog/realignment/2026-08-05_capacity_source_and_writer_decision.md` | created |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | updated |

Push: **none**.
