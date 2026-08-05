# Capacity Stage 1 — QA Configuration and Seed Readiness

**Task:** `CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_AND_SEED_READINESS`  
**Owner GO:** `AUTHORIZE_CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_AND_SEED_READINESS`  
**Date:** 2026-08-05  
**Status:** **PARTIAL_BLOCKED** — workcenter routing ready; available minutes not Owner-confirmed  
**Starting HEAD:** `5b2bc568`  
**Worklog:** `docs/worklog/realignment/2026-08-05_capacity_stage_1_qa_configuration_and_seed_readiness.md`  
**Prerequisites:** Capacity Stage 1 code PASS · s65 QA schema rollout PASS · Capacity rows = 0

```text
CAPACITY_STAGE_1_QA_SEED_READINESS = PARTIAL_BLOCKED
BLOCKER = MISSING_OWNER_CONFIRMED_OR_ACCEPTED_AVAILABLE_MINUTES
TASK_TO_WORKCENTER_MAPPING = COMPLETE_ON_PROTECTED_PLANS
CANONICAL_WORKCENTERS = 12
READY_FOR_SEED_STRUCTURE = 7 (plan-23 pilot set)
BLOCKED_FOR_MINUTES = ALL (available_minutes = UNKNOWN)
OWNER_CONFIRMED_VALUES = 0
AI_DECISION_VALUES = PROPOSED_NOT_WRITTEN
UNKNOWN_VALUES = all daily available_minutes + timezone confirmation
SEED_PLAN = PREPARED_AWAITING_OWNER_VALUES
RECURRING_CAPACITY_RULE = FUTURE_GAP
CAPACITY_ACTIVATION_READINESS = PARTIAL_BLOCKED
CAPACITY_ACTIVATION = NOT_AUTHORIZED
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_SOURCE_ROWS = 0
QA_CAPACITY_ALLOCATIONS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

This document is **read-only evidence**. It does not activate Capacity, insert minutes, or create allocations.

---

## 1. Identity model (non-negotiable)

| Fact | Evidence |
| ---- | -------- |
| No app-owned relational `workcenters` PK for Capacity/ORR | String `workcenter_code` only |
| Operational SoT | `backend/data/operational_workcenters.py` + workforce seed + ORR + `machines.workcenter_code` |
| Pricing namespace is **different** | `workcenter_rates.code` (`CNC_ROUTER`, `ASSEMBLY`, …) ≠ operational `WC_*` |
| Capacity Stage 1 supply | `workcenter_capacity_sources.workcenter_code` (opaque string; no FK to rates) |
| Rejected as available-minutes SoT | rates · HR hours · dashboard `capacity_shift_model` (Mon–Fri 8h util) |

Dual-namespace cheat sheet:

```text
Operational / EP / Capacity string:
  WC_CNC_ROUTING, WC_ASSEMBLY, WC_LED_ASSEMBLY, …

Pricing / template.op.workcenter / workcenter_rates:
  CNC_ROUTER, ASSEMBLY, PREPRESS, ACM_BOXED_ASSEMBLY, …
```

Never seed Capacity using pricing codes.

---

## 2. Canonical workcenter inventory

Source: `CANONICAL_WORKCENTER_CODES` (12). Classification = **ACTIVE_CANONICAL** unless noted.

| Code | Label (RO catalog) | Machines in QA | Employee auth | Used on plan 23 | Classification |
| ---- | ------------------ | -------------- | ------------- | --------------- | -------------- |
| WC_CNC_ROUTING | CNC router | MCH-CNC-4020, MCH-STYRO-CUTTER | yes | 3 tasks | ACTIVE_CANONICAL |
| WC_LETTER_FORMING | Modelare cant litere | MCH-CNC-CANT-LITERE | yes | 1 | ACTIVE_CANONICAL |
| WC_METAL_FAB | Sudură | 4 machines/areas | (via ops) | 1 | ACTIVE_CANONICAL |
| WC_ASSEMBLY | Ansamblare | WA-ASSEMBLY-01/02 | yes | 4 | ACTIVE_CANONICAL |
| WC_LED_ASSEMBLY | Electric | **0 machines** (work-area ops) | yes | 2 (incl. LED) | ACTIVE_CANONICAL |
| WC_VINYL_APPLICATION | Colantare | MCH-RIGID-FILM-LAMINATOR | yes | 1 | ACTIVE_CANONICAL |
| WC_PREPRESS | Grafică / Prepress | **0 machines** | (ORR only) | 1 | ACTIVE_CANONICAL |
| WC_FIELD_INSTALLATION | Montaj teren | 0 machines | yes | 0 on 21–23 | ACTIVE_CANONICAL |
| WC_PRINT | Print | MCH-EPSON-60800 | yes | 0 | ACTIVE_CANONICAL |
| WC_LAMINATE | Laminare | MCH-LAMINATOR-XPRO | yes | 0 | ACTIVE_CANONICAL |
| WC_CUT | Cutter plotter | MCH-CUTTER-PLOTTER | yes | 0 | ACTIVE_CANONICAL |
| WC_LASER_CUTTING | Laser | MCH-LASER-CNC | — | 0 | ACTIVE_CANONICAL |

### Non-canonical / do-not-seed

| Code | Classification | Note |
| ---- | -------------- | ---- |
| WC_CNC | ACTIVE_LEGACY / NON_CANONICAL | Conflict with WC_CNC_ROUTING — never silent-alias |
| WC_FORMING, WC_PAINT, WC_LED, WC_VINYL, … | ACTIVE_LEGACY | Labor/pricing aliases |
| WC_METAL_CUTTING, WC_STYRO_CUTTING | ACTIVE_LEGACY catalog | Not in freeze set; machines use CNC_ROUTING / METAL_FAB |
| Pricing codes (CNC_ROUTER, …) | DIFFERENT_NAMESPACE | Not Capacity workcenter_code |
| Test fixtures (WC_UNKNOWN, WC_A, …) | TEST_ONLY | Never seed QA |

---

## 3. Task-to-workcenter mapping (QA protected plans)

```text
TASK_TO_WORKCENTER_MAPPING = COMPLETE_ON_PROTECTED_PLANS
CAPACITY_SEED_READINESS ≠ BLOCKED_BY_TASK_ROUTING
```

All operational tasks on plans **21 / 22 / 23** carry `machine_requirement.workcenter` with a **canonical** `WC_*` code. Missing WC count = **0**.

### Plan 23 · order 880750 · 13 tasks (primary pilot)

| task_key (suffix) | workcenter | planned minutes | minutes source | assigned |
| ----------------- | ---------- | --------------- | -------------- | -------- |
| vector_prep | WC_PREPRESS | null | null | — |
| cnc_face_cut | WC_CNC_ROUTING | null | null | — |
| back_cut | WC_CNC_ROUTING | null | null | — |
| return_profile_forming | WC_LETTER_FORMING | null | null | — |
| return_face_bonding | WC_METAL_FAB | null | null | — |
| painting | WC_ASSEMBLY | null | null | — |
| led_install_letters | WC_LED_ASSEMBLY | null | null | employee **7** |
| electrical_letters | WC_LED_ASSEMBLY | null | null | — |
| assembly_letters | WC_ASSEMBLY | null | null | — |
| vinyl_application | WC_VINYL_APPLICATION | null | null | — |
| mounting_template_cnc_cut | WC_CNC_ROUTING | null | null | — |
| qc_letters | WC_ASSEMBLY | null | null | — |
| packaging | WC_ASSEMBLY | null | null | — |

**Workload note:** Stage 1 allocation writer rejects null minutes (never coerce to 0). Seed of *available* capacity can still proceed independently of task planned minutes; allocation smoke later needs labeled workload.

### Plan 22 · 880811 · 5 tasks

WC set: CNC_ROUTING, LETTER_FORMING, METAL_FAB, ASSEMBLY (×2). All canonical. Minutes mostly null.

### Plan 21 · 973019 · 18 tasks

WC set: PREPRESS, CNC_ROUTING, LETTER_FORMING, METAL_FAB, LED_ASSEMBLY, ASSEMBLY. One task has minutes=10 (CONFIRM_GEOMETRY). LED modules assigned to employee 7.

---

## 4. Available-minutes sources audit

| Candidate source | Usable for Capacity Stage 1 supply? | Status |
| ---------------- | ----------------------------------- | ------ |
| Owner-confirmed daily minutes | **Yes — required** | **OWNER_CONFIRMED = 0 rows exist** |
| Company calendar Mon–Fri 8h (`capacity_shift_model` / CAP-002) | **No** — dashboard util denominator only; Capacity decision rejected | not EXISTING_CANONICAL for RS |
| Machine count × hours | **No** without Owner proof | forbidden auto |
| Employee count × hours | **No** — employee outside triad | forbidden auto |
| `workcenter_rates` | **No** — commercial EUR | forbidden |
| Legacy Capacity rows in QA | n/a | 0 rows |
| Documented production schedule as RS SoT | **Not found** | UNKNOWN |
| AI starting proposal | Allowed only as `AI_DECISION`, Owner-editable, not written without GO | see §5 |

```text
AVAILABLE_MINUTES_SOURCE = UNKNOWN (no Owner-confirmed; no existing Capacity SoT)
OWNER_CONFIRMED_VALUES = none
EXISTING_CANONICAL_CAPACITY_VALUES = none
```

**Do not invent** `480` / `8h` / machine×hours as `OWNER_CONFIGURED`.

---

## 5. AI decision policy (proposals only — not written)

AI may propose starting values **only** with:

```text
configurable = true
source_label = AI_DECISION
explanation = present
owner editable = true
not execution reality
```

### Optional AI_DECISION proposals (Owner must accept or replace)

These are **not** factual shop truth. Offered only as editable starting points for a **controlled seed GO**.

| workcenter_code | proposed available_minutes | confidence | reasoning |
| --------------- | -------------------------- | ---------- | --------- |
| WC_CNC_ROUTING | 480 | LOW | One primary CNC day-shift analogy; **not** Owner-confirmed; mirrors rejected dashboard 8h — must be Owner-edited |
| WC_LETTER_FORMING | 480 | LOW | Same |
| WC_METAL_FAB | 480 | LOW | Multi-machine WC — 480 may understate; Owner must decide |
| WC_ASSEMBLY | 480 | LOW | Two work areas — Owner must decide pool vs per-area |
| WC_LED_ASSEMBLY | 480 | LOW | No machine row; labor WC |
| WC_VINYL_APPLICATION | 480 | LOW | Single laminator WC |
| WC_PREPRESS | 480 | LOW | No machine; design WC |

```text
AI_DECISION_VALUES = PROPOSED_ABOVE (not written to QA)
UNKNOWN_VALUES = all available_minutes until Owner confirms or explicitly accepts AI_DECISION
```

If Owner rejects AI proposals without supplying replacements:

```text
available_minutes = UNKNOWN
→ do not seed
→ do not activate Capacity
```

---

## 6. Stage 1 candidate set (small factual rollout)

Prefer **plan-23 operational WC set** only — not all 12 at once.

```text
READY_FOR_SEED_STRUCTURE (routing + registry):
  WC_CNC_ROUTING
  WC_LETTER_FORMING
  WC_METAL_FAB
  WC_ASSEMBLY
  WC_LED_ASSEMBLY
  WC_VINYL_APPLICATION
  WC_PREPRESS

DEFER_FIRST_SEED (canonical but unused on protected volumetric pilot plans):
  WC_PRINT
  WC_LAMINATE
  WC_CUT
  WC_LASER_CUTTING
  WC_FIELD_INSTALLATION

NOT_READY / FORBIDDEN:
  WC_CNC (non-canonical)
  pricing codes
  catalog-only WC_METAL_CUTTING / WC_STYRO_CUTTING
```

Minutes status for every READY_FOR_SEED_STRUCTURE code: **UNKNOWN** until Owner GO.

---

## 7. Over-allocation policy

```text
DEFAULT = WARN_ONLY
```

No repo evidence that any workcenter requires HARD_BLOCK or ALLOW_WITH_REASON for Stage 1 QA seed. Keep WARN_ONLY unless Owner explicitly overrides per WC.

---

## 8. Recurrence / schema gap

Stage 1 schema stores **one concrete DAY row** per `(workcenter_code, bucket_date)` while ACTIVE (partial unique).

```text
RECURRING_CAPACITY_RULE = FUTURE_GAP
```

No recurring “template rule” table. Future seed GO must either:

1. materialize **N explicit calendar days** (e.g. next workweek), or  
2. add a future schema for recurring rules (separate Owner GO — **out of scope here**).

Timezone: recommend `Europe/Bucharest` as Owner-confirm / AI_DECISION default (company calendar is RO-oriented). Not written.

---

## 9. Seed plan (prepared — **not executed**)

### Shape

```text
operation = CREATE_WORKCENTER_CAPACITY (command path only — never SQL)
one row per (workcenter_code, bucket_date)
timezone = <Owner-confirmed, candidate Europe/Bucharest>
available_minutes = <Owner-confirmed OR accepted AI_DECISION>
over_allocation_policy = WARN_ONLY
source_label = OWNER_CONFIGURED | AI_DECISION
source_explanation = required if AI_DECISION
reason_code = QA_CONTROLLED_CAPACITY_SEED
actor = Owner / authorized admin
idempotency_key = UUID per create (stable per WC+day intent)
expected_version = 0
```

### Example rows (values TBD by Owner — placeholders shown as UNKNOWN)

| workcenter_code | bucket_date | timezone | available_minutes | policy | source_label |
| --------------- | ----------- | -------- | ----------------- | ------ | ------------ |
| WC_CNC_ROUTING | &lt;Owner day&gt; | Europe/Bucharest? | UNKNOWN | WARN_ONLY | TBD |
| WC_LETTER_FORMING | same day set | … | UNKNOWN | WARN_ONLY | TBD |
| WC_METAL_FAB | … | … | UNKNOWN | WARN_ONLY | TBD |
| WC_ASSEMBLY | … | … | UNKNOWN | WARN_ONLY | TBD |
| WC_LED_ASSEMBLY | … | … | UNKNOWN | WARN_ONLY | TBD |
| WC_VINYL_APPLICATION | … | … | UNKNOWN | WARN_ONLY | TBD |
| WC_PREPRESS | … | … | UNKNOWN | WARN_ONLY | TBD |

After sources exist for ≥1 WC+day, a **separate** GO may `configure_resource_domain(CAPACITY_ALLOCATION → ACTIVE)`.

Order for future execution GO:

```text
1. backup QA
2. CREATE_WORKCENTER_CAPACITY rows (Owner-approved values only)
3. verify source rows + history
4. configure CAPACITY_ALLOCATION ACTIVE (R7)
5. evaluator smoke (expect CLEAR when configured + no open alloc blockers)
6. still no Phase B wiring
```

---

## 10. Capacity activation readiness

| Prerequisite | Status |
| ------------ | ------ |
| ≥1 canonical workcenter | **PASS** (12; pilot 7) |
| Factual or Owner-accepted minutes | **FAIL** — UNKNOWN |
| Capacity writer implemented | PASS |
| Read evaluator implemented | PASS |
| Source history implemented | PASS |
| Permissions implemented | PASS |
| Seed plan structure verified | PASS (awaiting values) |
| No inconsistent Capacity rows | PASS (0 rows) |
| s65 schema in QA | PASS |

```text
CAPACITY_ACTIVATION_READINESS = PARTIAL_BLOCKED
CAPACITY_ACTIVATION = NOT_AUTHORIZED
```

---

## 11. Owner decisions required (next GO input)

1. Confirm pilot WC set (recommend plan-23 seven).  
2. For each WC: exact `available_minutes` (**OWNER_CONFIRMED**) **or** explicit accept of AI_DECISION proposal with editable explanation.  
3. Confirm timezone (`Europe/Bucharest` candidate).  
4. Confirm which calendar days to materialize (no recurrence).  
5. Confirm WARN_ONLY unless overriding.  
6. Authorize separate GO: `CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_SEED_AND_ACTIVATION`.

---

## 12. QA boundary (unchanged by this task)

```text
QA Alembic = s65_workcenter_capacity_source
Capacity config = 0
capacity source rows = 0
capacity allocations = 0
Scheduling = ACTIVE
Reservation = ACTIVE
assignment transitions = 7
foreign_key_check = 0
QA SHA unchanged (read-only)
```

---

## 13. `/modules` · `/governance`

| Surface | Impact |
| ------- | ------ |
| `/modules` | **NO_IMPACT** UI — document that QA has s65 schema; Capacity inactive; workcenter truth readiness = PARTIAL (minutes missing). |
| `/governance` | **NO_IMPACT** UI — Owner-confirmed vs AI_DECISION remains Owner-gated; seed/activation require separate GO. |

---

## 14. Future candidate

```text
FUTURE CANDIDATE:
CAPACITY_STAGE_1_CONTROLLED_QA_CONFIGURATION_SEED_AND_ACTIVATION
```

Requires exact Owner-approved values. **No automatic 480.**
