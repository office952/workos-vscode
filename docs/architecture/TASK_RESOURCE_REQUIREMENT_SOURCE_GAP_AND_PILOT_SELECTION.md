# Task Resource Requirement — Source Gap Audit and Pilot Selection

**Task:** `TASK_RESOURCE_REQUIREMENT_SOURCE_GAP_AND_PILOT_SELECTION`  
**Owner GO:** `AUTHORIZE_TASK_RESOURCE_REQUIREMENT_SOURCE_GAP_AND_PILOT_SELECTION`  
**Date:** 2026-08-05  
**Status:** **PASS** · docs-only · **no runtime · no persistence**  
**Starting HEAD:** `c37b1aec`  
**Prerequisites:** Read-only projection PASS · Task resource contract PASS · Owner D1–D6 APPLIED  
**Worklog:** `docs/worklog/realignment/2026-08-05_task_resource_requirement_source_gap_and_pilot_selection.md`

```text
TASK_RESOURCE_REQUIREMENT_SOURCE_GAP_AND_PILOT_SELECTION = PASS
SOURCE_GAP_INVENTORY = COMPLETE
FIELD_OWNERSHIP_MATRIX = FINALIZED
PILOT_SELECTION = COMPLETE
SELECTED_PILOT = VECTOR_PREP_DURATION_E2E_COMPLETENESS
VECTOR_PREP_DURATION_E2E = PASS
RUNTIME_IMPLEMENTATION = PILOT_COMPLETE
PLAN_23 = UNCHANGED_NULL_REFERENCE_CASE
TASKS_JSON_MUTATIONS = 0
QA_MUTATIONS = 0
PRODUCT_SYSTEM_WRITES = 0
MACHINE_RUN = NOT_IMPLEMENTED
WORKSPACE_BOOKING = NOT_IMPLEMENTED
EMPLOYEE_AVAILABILITY = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Central principle

```text
Read-only projection shows gaps.
It must not become the source of truth for filling them.
```

Canonical flow (unchanged):

```text
Component Template / Operation Contract / planning-duration contract
  → ProductDefinition / ProductAggregate (evaluate + freeze stamps)
  → ExecutionPlan snapshot (planned_tasks → operational_tasks)
  → read-only task requirement projection
  → resource systems (availability / commitment)
```

Forbidden shortcuts: inventing values in Scheduling, Resource State, Capacity, or the projection layer.

---

## 2. Projection baseline (QA plans 21 / 22 / 23)

Captured via `GET /api/v1/execution/plans/{id}/resource-requirements` (read-only).

| Plan | order | tasks | known_minimal | partial | duration_known | duration_unknown | safe_mode_hint | hybrid_unknown |
| ---- | ----- | ----: | ------------: | ------: | -------------: | ---------------: | -------------: | -------------: |
| 21 | 973019 | 18 | 1 | 17 | 1 | 17 | 17 | 1 |
| 22 | 880811 | 5 | 0 | 5 | 0 | 5 | 4 | 1 |
| 23 | 880750 | 13 | 0 | 13 | 0 | 13 | 11 | 2 |

Only **one** task across the three plans has known duration:

| Plan | Task suffix | Op | WC | Minutes | Source |
| ---- | ----------- | -- | -- | ------: | ------ |
| 21 | `CONFIRM_GEOMETRY` | `vector_prep` | `WC_PREPRESS` | 10.0 | `…formula:count_based_time` |

Plan 23 `vector_prep` is the same operation with **null** minutes — Aggregate already null at freeze.

`tasks_json` SHAs (unchanged by this GO):

```text
plan21 = 75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59
plan22 = 0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97
plan23 = 00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
```

---

## 3. Gap inventory (grouped)

Per-task detail for plans 21/22/23 is summarized below. Full row lists live in the worklog appendix.

### Always unknown on these fixtures (no stamp on Aggregate / EP)

| Concern | Plans 21/22/23 | Classification |
| ------- | -------------- | -------------- |
| Authoritative `resource_mode` | All shop tasks | `FIELD_NOT_PRESENT_IN_SOURCE` (soft hint only) |
| `machine_capability_code` | All | `FIELD_NOT_PRESENT_IN_SOURCE` (ORR allowlist is **live**, not stamped) |
| `required_people_min` / recommended | All | `FIELD_NOT_PRESENT_IN_SOURCE` |
| `workspace_class` / shareable | Manual / hybrid WCs | `FIELD_NOT_PRESENT_IN_SOURCE` |
| `batch_eligible` | Machine-bound candidates | `FIELD_NOT_PRESENT_IN_SOURCE` |

### Duration

| Situation | Classification | Evidence |
| --------- | -------------- | -------- |
| Plan 21 `vector_prep` = 10 min | Path works when inputs exist | Aggregate + EP carry formula provenance |
| Plan 23 `vector_prep` = null | `SOURCE_EXISTS_BUT_NOT_PROJECTED` **because geometry input missing** | Order 880750 snapshot has **zero** `letter_count` hits; Aggregate `estimated_minutes=null` |
| All other ops | `FIELD_NOT_PRESENT_IN_SOURCE` | Only `vector_prep` has a Product System planning-duration contract today |
| Dispatch dict `VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES` | **Not** Aggregate authority | Fallback labels/scheduling helpers — must not silently fill EP |

### Soft mode hints (derived, not ownership)

| WC family | Hint | Note |
| --------- | ---- | ---- |
| CNC / LETTER_FORMING / … | `MACHINE_BOUND` | Safe soft derivation |
| ASSEMBLY / LED_ASSEMBLY | `MANUAL_WORKSPACE` | Soft only |
| PREPRESS | `PERSON_DRIVEN` | Soft only |
| METAL_FAB / VINYL | `UNKNOWN` | HYBRID — Owner D1 |

---

## 4. Provenance tracing

### 4.1 Duration

```text
planning_duration_contract.py (Product System)
  → product_aggregate_planning_duration_service.resolve_operation_planning_duration
  → Aggregate op.estimated_minutes + planning_minutes_source
  → EP preview planned_tasks.estimated_minutes
  → materialize → operational_tasks.estimated_time_minutes
```

| Question | Answer |
| -------- | ------ |
| Missing from source? | For all ops except `vector_prep`: **yes** (no planning-duration contract) |
| Exists but not projected? | Plan 23 `vector_prep`: contract exists; **`letter_count` absent** on order 880750 → Aggregate left null → EP honest null |
| Other field? | Commercial `formula_id` on seed ops ≠ planning-duration authority |
| Calculable? | In principle via `COUNT_BASED_TIME` / perimeter formulas; **only wired for `vector_prep`** |
| Owner / history? | New op contracts need Owner basis; do not invent from dispatch defaults |

```text
null remains null without factual source
```

### 4.2 Machine requirement

| Layer | Finding |
| ----- | ------- |
| WC routing | **Exists** — ORR freeze stamps Aggregate `workcenter` → EP `machine_requirement.workcenter` |
| Capability stamp on task | **Absent** |
| ORR `allowed_resource_codes` | **Live read** (ORR readiness / eligibility) — not frozen on task |
| Process contracts `required_capabilities` | Parallel process graph IDs — **not** EP op capability codes |
| Concrete `machine_id` | Reservation only — **must not** move into Product System |

```text
Task may later declare capability.
Machine Reservation selects machine_id.
```

### 4.3 People

| Concept | Present? |
| ------- | -------- |
| `required_people_min` / recommended | **No** on template / Aggregate / EP |
| Skills | ORR `required_skill_codes` — **live**, not task demand |
| Concrete employees | Assignment commitment — **not** demand |
| `employee_role_requirement` on PlannedTask schema | Unused by preview |

Employee 7 on plan 23 LED ≠ people demand.

### 4.4 Workspace

| Concept | Present? |
| ------- | -------- |
| `workspace_class` / shareable / exclusive | **No** on demand path |
| Owner classes SMALL/MEDIUM/FULL_TABLE/LARGE_AREA | Decision package only |
| Machines registry `resource_kind=work_area` | ORR/live candidates — **not** table booking; **not** auto-reuse as `workspace_class` |
| Intake `workspace_id` | Different entity (Intake workspace) |

Do **not** reuse Machine Reservation `work_area` candidates as manual-table demand.

### 4.5 Batch eligibility

| Concept | Present? |
| ------- | -------- |
| `batch_eligible` / grouping key | **No** on product/EP path |
| Nesting / sheet / MACHINE_RUN | Docs + Owner D4 only — **not implemented** |

Must come from operation/material technical truth later — never from task name guessing.

---

## 5. Field ownership matrix

| Field | Needed now? | Owner system | Canonical source | Manual / derived | Required / optional | Projection path | Runtime consumer | Commercial | Execution | Owner decision now? |
| ----- | ----------- | ------------ | ---------------- | ---------------- | ------------------- | --------------- | ---------------- | ---------- | --------- | ------------------- |
| `estimated_task_duration_minutes` | **Yes (pilot)** | Product System → Aggregate | `planning_duration_contract` + geometry/static | derived or Owner static | optional nullable | Aggregate → EP → projection | planning honesty; later Capacity | no | planning | **Yes** for new ops; vector_prep basis already set |
| `planning_minutes_source` | **Yes (with minutes)** | Aggregate stamp | resolver provenance string | derived | with minutes | same | audit | no | honesty | No |
| `resource_mode` | No (soft hint OK) | Aggregate/PD (future) | explicit op declaration | manual (HYBRID must) | later | future stamp | planners | no | demand | Deferred (HYBRID) |
| `machine_capability_code` | Useful later | ORR / op contract | ORR allowlist or capability catalog | derived | later | optional freeze | Reservation match | no | match | Deferred |
| `required_people_min` | No for first pilot | Aggregate/PD | Owner/op truth | manual | later | future | employee schedule | no | demand | Deferred |
| `required_people_recommended` | No | same | same | manual | later | future | planning | no | demand | Deferred |
| `required_skill_codes` | Live OK | ORR | registry | derived live | live today | **not** on task (by design) | eligibility | no | gate | No |
| `workspace_class` | No for first pilot | Aggregate/PD | Owner/op | manual | later | future | workspace occupancy | no | demand | Deferred |
| `workspace_shareable` | No | Aggregate/PD | Owner/op | manual | later | future | sharing policy | no | demand | Deferred |
| `batch_eligible` | No | Aggregate/PD | Owner/op/material | manual | later | future | MACHINE_RUN | no | demand | Deferred |

---

## 6. Needed-now versus future-only

### Needed for the next pilot

```text
estimated_task_duration_minutes
planning_minutes_source
(+ factual geometry inputs required by the duration contract, e.g. letter_count)
```

### Useful, not blocking the first pilot

```text
machine_capability_code freeze (ORR already live)
soft resource_mode_hint (already projected)
```

### Future-only (do not pull into current build)

```text
workspace compatibility matrix
workspace occupation duration
active labor vs machine vs cure splits
automatic batch grouping / MACHINE_RUN
employee availability calendar
auto-scheduling / optimization
required_people_* persistence
authoritative resource_mode for HYBRID
Capacity activation / seed
```

---

## 7. Pilot candidates (max 3)

### Candidate A — CNC machine-bound (`face_cnc_cut`)

| | |
| - | - |
| Profile | `WC_CNC_ROUTING`, soft `MACHINE_BOUND`, non-HYBRID, no manual workspace for pilot |
| Real fixtures | Plan 22/23 `cnc_face_cut`; plan 21 `CUT_FACE` |
| Pros | Clear machine family; ORR has CNC resource allowlist |
| Cons | **No** planning-duration contract yet; formula basis unknown; dispatch `45` must not be promoted |
| Scope if chosen | New duration contract + Aggregate → EP only |

### Candidate B — Manual LED (`led_install_letters`, plan 23)

| | |
| - | - |
| Profile | `WC_LED_ASSEMBLY`, soft `MANUAL_WORKSPACE` |
| Pros | Protected plan; well-known task; projection already classifies PARTIAL |
| Cons | Duration + people + workspace all missing; employee 7 temptation; multi-field blast radius |
| Verdict | **Reject** as first pilot |

### Candidate C — PREPRESS `vector_prep` duration E2E completeness

| | |
| - | - |
| Profile | `WC_PREPRESS`, soft `PERSON_DRIVEN` |
| Pros | Contract **already exists**; plan 21 proves 10 min path; plan 23 proves missing `letter_count` → honest null; **smallest field set** |
| Cons | Does not introduce CNC duration; fixture 880750 geometry gap must be diagnosed carefully (no inventing letter_count) |
| Scope | Ensure geometry → Aggregate → EP for existing contract; projection shows duration_known |

---

## 8. Selected pilot

```text
PILOT_TASK_TYPE = PREPRESS_VECTOR_PREP_DURATION_E2E
PILOT_OPERATION_CODE = vector_prep
PILOT_WORKCENTER = WC_PREPRESS
FIELDS_TO_COMPLETE =
  estimated_task_duration_minutes
  planning_minutes_source
  (geometry input letter_count required by existing contract — not invented)
SOURCE_OWNER =
  Product System planning_duration_contract (LETTERS_VECTOR_PREP_DURATION)
  + ProductDefinition / quote geometry letter_count
  + ProductAggregate planning-duration resolver
PROJECTION_PATH =
  Aggregate op minutes/source
  → ExecutionPlan planned_tasks / operational_tasks
  → GET .../resource-requirements
FIELDS_DEFERRED =
  resource_mode (authoritative)
  machine_capability_code
  required_people_*
  workspace_*
  batch_eligible
  CNC and other op duration contracts
  MACHINE_RUN / Capacity / Phase B
WHY_THIS_PILOT =
  Only op with an existing Product System duration contract;
  plan 21 already proves the E2E path;
  plan 23 shows the real upstream gap (missing letter_count), not a Scheduling/Capacity defect;
  zero new demand schemas; non-HYBRID; no workspace/people/batch;
  maximum honesty with minimum blast radius.
```

**Why not CNC first:** CNC needs a **new** Owner formula decision before any truthful minutes exist. Completing `vector_prep` first reuses a proven Product System mechanism and makes the Aggregate→EP→projection path undeniable on the protected plan family.

**Why not LED first:** Would force simultaneous Owner invent for duration + people + workspace — overengineering for a first slice.

---

## 9. Future E2E path (not implemented in this GO)

```text
1. Canonical source already holds LETTERS_VECTOR_PREP_DURATION
2. Order/ProductDefinition supplies letter_count (factual)
3. ProductAggregate evaluates minutes + planning_minutes_source
4. ExecutionPlan freezes those stamps on planned/operational tasks
5. Read-only projection shows duration_known for vector_prep only
6. Other tasks remain PARTIAL / duration unknown
7. No reservation / schedule / Capacity / assignment side effects
```

Success proof shape (future implementation GO):

```text
plan 23 vector_prep: null → non-null only when letter_count factual
tasks_json SHA change only if Owner authorizes a controlled re-freeze
QA Capacity rows remain 0
```

---

## 10. Owner decisions

### OWNER_DECISIONS_REQUIRED_NOW

1. **Accept selected pilot = `vector_prep` duration E2E completeness** (not LED, not full CNC pack).  
2. **Confirm:** planning duration for Pregătire vector remains **2 minutes × letter_count** (existing TE2E-028B contract) — or state a different Owner basis.  
3. **Confirm:** when `letter_count` is missing, minutes must stay **null** (never invent; never use dispatch fallback `15`).  
4. **For plan 23 / order 880750:** should the next implementation GO (a) restore factual `letter_count` into the freeze inputs for a controlled re-materialization, or (b) prove the path on a **new** controlled fixture that already has letter_count (like plan 21) without mutating plan 23?

### OWNER_DECISIONS_DEFERRED

```text
CNC / forming / assembly duration formulas
authoritative resource_mode (esp. HYBRID)
workspace_class for LED/assembly
required_people_min
batch_eligible
machine_capability freeze vs live ORR
MACHINE_RUN / workspace booking
Capacity seed/activation
```

### NO_OWNER_DECISION_REQUIRED

```text
Keep soft resource_mode_hint read-only
Keep ORR skills/resources live (not stamped)
Keep projection non-authoritative
Keep Capacity IMPLEMENTED_INACTIVE
Keep Phase B / C blocked
Do not persist demand into Scheduling / Resource State
```

### Plain-language Owner questions (for the pilot)

```text
Pentru Pregătire vector (vector_prep):
- durata rămâne 2 minute × număr litere?
- dacă numărul de litere lipsește, lăsăm durata necunoscută?
- vrem să demonstrăm pe planul 23 (necesită geometrie factuală)
  sau pe o comandă nouă controlată ca planul 21?
```

---

## 11. Product System boundary

First truth for this pilot lives in:

```text
Product System planning-duration contract (already)
+ ProductDefinition / geometry letter_count (input)
→ ProductAggregate evaluation
→ ExecutionPlan freeze
```

Not in:

```text
UI hardcoding
per-product private scheduling rules
Scheduling / Resource State invention
read-only projection as writer
dispatch fallback dictionaries as Aggregate authority
```

If letter_count is unknown for a real job — **ask Owner / capture geometry**. Do not invent.

---

## 12. Implementation sequencing

| Order | Slice | Notes |
| ----- | ----- | ----- |
| 1 | Source gap audit | **PASS** |
| 2 | `VECTOR_PREP_DURATION_E2E` | **PASS** — see worklog `2026-08-05_vector_prep_duration_e2e_completeness.md` |
| 3 | First **new** machine-bound duration contract (`face_cnc_cut`) | After Owner formula decision |
| 4 | Manual workspace / people pilots | After Owner answers crew + class |
| 5 | HYBRID explicit `resource_mode` | After Product/Operation authoring |
| 6 | MACHINE_RUN / batch | After demand + Reservation ownership ready |

Owner D1–D5 applied. Positive proof = new controlled fixture; plan 23 remains null reference.

```text
NEXT_TASK = NOT_AUTHORIZED
```

---

## 13. QA proof (this GO)

```text
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
capacity source rows = 0
capacity allocation rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA unchanged
plans 21/22/23 tasks_json SHA unchanged
RUNTIME_IMPLEMENTATION = NOT_STARTED
PRODUCT_SYSTEM_WRITES = 0
```

---

## 14. `/modules` · `/governance`

| Surface | Impact |
| ------- | ------ |
| `/modules` | **NO_IMPACT** UI — docs only |
| `/governance` | Demand ownership clarified; first pilot named |
