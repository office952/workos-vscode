# Capacity Stage 1 — QA Configuration and Seed Readiness

**Task:** `CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_AND_SEED_READINESS`  
**Owner GO:** `AUTHORIZE_CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_AND_SEED_READINESS`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `5b2bc568`  
**Architecture:** `docs/architecture/CAPACITY_STAGE_1_QA_CONFIGURATION_AND_SEED_READINESS.md`  
**Prerequisite:** `CAPACITY_STAGE_1_QA_SCHEMA_ROLLOUT = PASS` (tip `5b2bc568`)

---

## Verdict

```text
CAPACITY_STAGE_1_QA_SEED_READINESS = PARTIAL_BLOCKED
BLOCKER = MISSING_OWNER_CONFIRMED_OR_ACCEPTED_AVAILABLE_MINUTES
TASK_TO_WORKCENTER_MAPPING = COMPLETE_ON_PROTECTED_PLANS
CANONICAL_WORKCENTERS = 12
READY_FOR_SEED_STRUCTURE = WC_CNC_ROUTING, WC_LETTER_FORMING, WC_METAL_FAB, WC_ASSEMBLY, WC_LED_ASSEMBLY, WC_VINYL_APPLICATION, WC_PREPRESS
DEFER_FIRST_SEED = WC_PRINT, WC_LAMINATE, WC_CUT, WC_LASER_CUTTING, WC_FIELD_INSTALLATION
FORBIDDEN = WC_CNC, pricing codes, catalog-only extras
AVAILABLE_MINUTES_SOURCE = UNKNOWN
OWNER_CONFIRMED_VALUES = 0
AI_DECISION_VALUES = PROPOSED_NOT_WRITTEN (optional 480 LOW confidence)
UNKNOWN_VALUES = all available_minutes + timezone confirmation
SEED_PLAN = PREPARED_AWAITING_OWNER_VALUES
RECURRING_CAPACITY_RULE = FUTURE_GAP
OVER_ALLOCATION_DEFAULT = WARN_ONLY
CAPACITY_ACTIVATION_READINESS = PARTIAL_BLOCKED
CAPACITY_ACTIVATION = NOT_AUTHORIZED
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_SOURCE_ROWS = 0
QA_CAPACITY_ALLOCATIONS = 0
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## Preflight

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = 5b2bc568
no foreign tracked changes
code Alembic = s65
QA Alembic = s65
foreign_key_check = 0
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity config = absent
capacity source rows = 0
capacity allocations = 0
assignment transitions = 7
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4 (unchanged)
```

---

## Findings (short)

1. **12 ACTIVE_CANONICAL** operational `WC_*` codes (`operational_workcenters.py`); no Capacity FK table.  
2. Protected plans **21 / 22 / 23** all have complete canonical WC stamps — **not** blocked by task routing.  
3. Plan 23 LED task → `WC_LED_ASSEMBLY` · employee 7. Almost all planned minutes are **null**.  
4. **Zero** Owner-confirmed daily available minutes in QA or RS SoT. Dashboard 8h shift util is **rejected** as Capacity supply.  
5. Optional AI_DECISION `480` proposals listed for the 7 pilot WCs — **not written**; Owner must confirm or replace.  
6. Schema supports **one concrete DAY row** only → recurring rules = **FUTURE_GAP**.  
7. Activation remains **PARTIAL_BLOCKED** until minutes are Owner-gated.

---

## Owner decisions required

| # | Decision |
| - | -------- |
| 1 | Pilot WC set (recommend 7 from plan 23) |
| 2 | Exact `available_minutes` per WC (OWNER_CONFIRMED or accept AI_DECISION) |
| 3 | Timezone (candidate `Europe/Bucharest`) |
| 4 | Which calendar days to materialize |
| 5 | Confirm WARN_ONLY |
| 6 | Authorize seed+activation GO separately |

---

## QA zero-mutation proof

```text
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_CAPACITY_SOURCE_ROWS_CREATED = 0
QA_CAPACITY_CONFIGURATION_ROWS_CREATED = 0
QA_CAPACITY_ALLOCATIONS_CREATED = 0
```

---

## `/modules` · `/governance`

| Surface | Verdict |
| ------- | ------- |
| `/modules` | **NO_IMPACT** — Capacity schema exists; inactive; minutes readiness PARTIAL |
| `/governance` | **NO_IMPACT** — Owner vs AI_DECISION gating documented; no UI change |

---

## Files

| Path | Change |
| ---- | ------ |
| `docs/architecture/CAPACITY_STAGE_1_QA_CONFIGURATION_AND_SEED_READINESS.md` | new |
| `docs/worklog/realignment/2026-08-05_capacity_stage_1_qa_configuration_and_seed_readiness.md` | this worklog |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | next-step pointer |

**No push.**

---

## Next (future candidate only)

```text
FUTURE CANDIDATE:
CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_SEED_AND_ACTIVATION
```

Requires exact Owner-approved minutes. No automatic generic values.
