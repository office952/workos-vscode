# Task Resource Requirement — Read-Only Contract

**Task:** `TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT`  
**Owner GO:** `AUTHORIZE_TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT`  
**Date:** 2026-08-05  
**Status:** **PASS** · Contract finalized · **no runtime · no schema**  
**Starting HEAD:** `9b3d95ff`  
**Prerequisites:** Owner decision package PASS · Resource model realignment PASS  
**Worklog:** `docs/worklog/realignment/2026-08-05_task_resource_requirement_readonly_contract.md`

```text
TASK_RESOURCE_REQUIREMENT_READONLY_CONTRACT = PASS
TASK_DEMAND_BOUNDARY = FINALIZED
RESOURCE_AVAILABILITY_BOUNDARY = FINALIZED
MINIMAL_CONTRACT = FINALIZED
NOW_FIELDS = see §5
LATER_FIELDS = see §6
FIELD_OWNERSHIP = FINALIZED
SOURCE_PROVENANCE = FINALIZED
NULL_BEHAVIOR = PRESERVED
MACHINE_IDENTITY_SELECTION = DEFERRED_TO_RESERVATION
EMPLOYEE_SELECTION = DEFERRED
WORKSPACE_BOOKING = DEFERRED
MACHINE_RUN = NOT_IMPLEMENTED
WORKSPACE_MODEL = NOT_IMPLEMENTED
EMPLOYEE_AVAILABILITY = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
CAPACITY_ACTIVATION = NOT_AUTHORIZED
QA_MUTATIONS = 0
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Central principle

```text
Task declares demand.
Resource systems declare availability.
```

| Layer | Role |
| ----- | ---- |
| ProductDefinition / ProductAggregate | Technical demand for the operation |
| ExecutionPlan task | Frozen demand for the concrete job |
| Machine Reservation | Concrete machine interval availability |
| Employee / HR | People eligibility + future availability |
| Workspace model (future) | Table/zone availability + compatibility |
| Capacity Stage 1 | Inactive; not demand; not commitment |

```text
resource requirement ≠ resource commitment
workcenter_code ≠ automatic bottleneck / reservation
```

---

## 2. Existing task contract (repo today)

Materialize path: `execution_plan_task_parser.py` ← planned_tasks ← Aggregate/ORR freeze.

| Present on operational task | Absent |
| --------------------------- | ------ |
| `task_id` / keys, `source_operation_code` | `resource_mode` |
| `workcenter`, `machine_requirement.{workcenter,mapping_source,resolution_status}` | `machine_capability_code`, `machine_id` (product-time) |
| `estimated_time_minutes` (null OK), `planning_minutes_source` | `workspace_*`, `required_people*` |
| `assigned_employee_id` (post-assign; not demand) | `batch_eligible`, `batch_grouping_key` |
| Optional unused `employee_role_requirement` | Duration splits (labor/occupation/cure) |

ORR `required_skill_codes` / `allowed_resource_codes` are **live read** (eligibility/readiness) — **not** stamped on the task JSON.

Readiness enum `resource_requirement_mode` (`workcenter_only` / `orr_allowlist` / …) is **not** Capacity `resource_mode` and is **not** task demand.

---

## 3. Demand vs availability

| Concern | Owner |
| ------- | ----- |
| What the task needs | Task resource requirement (this contract) |
| Which machine instance | Machine Reservation (selects `machine_id`) |
| Which employees | Assignment + eligibility (+ future availability) |
| Which table slot | Future workspace occupancy |
| Soft WC day minutes | Capacity Stage 1 — **inactive** |

Phase B must not treat missing declarative requirements as clearance. Pre-start remains gated by **runtime commitments** already in the triad/writers — not by this contract alone.

---

## 4. `resource_mode` — do not invent from WC alone

Candidate values:

```text
MACHINE_BOUND | MANUAL_WORKSPACE | PERSON_DRIVEN | HYBRID | FIELD
```

| WC family (classification) | Soft read-only hint | Authoritative `resource_mode` |
| -------------------------- | ------------------- | ---------------------------- |
| MACHINE_BATCHABLE / MACHINE_EXCLUSIVE | MACHINE_BOUND | Only if later explicit or accepted soft default |
| MANUAL_SHARED_WORKSPACE | MANUAL_WORKSPACE | Same |
| MANUAL_PERSON_DRIVEN | PERSON_DRIVEN | Same |
| HYBRID (METAL_FAB, VINYL) | **none** | **Must be explicit** (Owner D1) |
| FIELD_OPERATION | FIELD | Same |

```text
WC family hint = DERIVABLE inference for display only
≠ silent persistence
≠ reservation / booking
```

---

## 5. NOW fields (minimal contract)

These are the bounded **NOW** set: either already on the task, or defined as required semantics for the next readonly projection — **without** inventing values.

| Field | Status | Why now | If missing |
| ----- | ------ | ------- | ---------- |
| `task_key` / `task_id` | **EXISTS** | Identity | Task invalid |
| `operation_code` (`source_operation_code`) | **EXISTS** | Join to ORR / Aggregate op | Live skill/resource resolve weakens |
| `workcenter_code` (`workcenter`) | **EXISTS** | Routing zone | Routing unknown |
| `estimated_task_duration_minutes` ↔ `estimated_time_minutes` | **EXISTS** nullable | Planning duration honesty | Duration UNKNOWN — **not** 0 |
| `duration_source` ↔ `planning_minutes_source` | **EXISTS** nullable | Provenance of minutes | Source UNKNOWN |
| `resource_requirement_status` | **DERIVED** (contract) | Honesty when demand fields absent | — |
| `resource_mode_hint` | **DERIVED** soft (non-HYBRID only) | Operator orientation from WC family | Hint absent; HYBRID → no hint |

```text
resource_requirement_status:
  PARTIAL_EXISTING_ROUTING_AND_DURATION  — workcenter and/or minutes present
  RESOURCE_REQUIREMENTS_UNKNOWN          — demand fields (mode/people/workspace/batch) not declared
```

Missing demand contract **never** means “no resources needed”.

### Explicitly NOT NOW (even as defaults written into tasks)

| Field | Why not now |
| ----- | ----------- |
| Authoritative `resource_mode` | Hybrids + no product-source yet |
| `machine_capability_code` | No capability stamp on task; ORR allowlist is live |
| `required_people_min` | No source; no consumer |
| `workspace_class` / `workspace_shareable` | No source; no booking consumer |
| `batch_eligible` persisted | MACHINE_RUN not implemented; soft hint only |
| Duration splits | No canonical sources |

---

## 6. LATER fields

| Field | When justified |
| ----- | -------------- |
| `resource_mode` (authoritative) | Product/Aggregate can declare; especially HYBRID |
| `machine_capability_code`, `machine_count_required` (default 1 when machine explicit), `machine_exclusive` (default true for machine runs) | Machine-bound consumers + Reservation |
| `batch_eligible` (default false), `batch_grouping_key` | After MACHINE_RUN; eligible ≠ grouped |
| `required_people_min`, `required_people_recommended`, `simultaneous_people_required` | Multi-person ops |
| `required_skill_codes[]` on task (optional freeze) | If eligibility must survive ORR drift |
| `workspace_class`, `workspace_shareable`, `workspace_exclusive`, `workspace_compatibility_group` | Manual workspace model |
| `machine_runtime_minutes`, `active_labor_minutes`, `workspace_occupation_minutes`, `waiting_or_curing_minutes` | When sources exist |

---

## 7. Field ownership matrix

| Field | Owner system | Source | Editable by | Derived/manual | Required | Runtime consumer | Commercial | Execution |
| ----- | ------------ | ------ | ----------- | -------------- | -------- | ---------------- | ---------- | --------- |
| workcenter | Aggregate → EP | ORR freeze | Product/ops authoring | derived at freeze | for shop routing | ORR/readiness | no | routing |
| estimated_time_minutes | Aggregate → EP | formula / manager / AI | planning | either | optional nullable | capacity alloc later; display | no | planning |
| planning_minutes_source | Aggregate → EP | stamp | system | derived | with minutes | audit | no | honesty |
| resource_mode | Aggregate/PD (future) | OWNER / COMPONENT / AI | Owner/manager | manual or soft | later | planners | no | demand |
| machine_capability | ORR/future | ORR | catalog | derived | later | Reservation match | no | match |
| machine_id | Reservation | planner | operator | selected | at reserve | Reservation | no | commitment |
| required_people_* | Aggregate/PD (future) | OWNER | Owner/manager | manual | later | employee schedule | no | demand |
| assigned_employee_id | Assignment | command | operator | selected | at assign | assignment | no | commitment |
| workspace_* | Aggregate/PD (future) | OWNER | Owner/manager | manual | later | workspace occupancy | no | demand |
| batch_eligible | Aggregate/PD (future) | OWNER / op | Owner | manual | later | MACHINE_RUN grouping | no | demand |
| skills | ORR (live) / optional task freeze | ORR | catalog | derived | live today | eligibility | no | gate |

Canonical composition rule:

```text
Component / Operation contract → technical demand
Product Template composes
ExecutionPlan freezes concrete task demand
Resource systems resolve concrete resources + availability
```

Do not put concrete `machine_id` / employee / table booking into Product Template.

---

## 8. Source / provenance

Allowed source labels for estimated / demand fields:

```text
OWNER_DEFINED
COMPONENT_CONTRACT
PRODUCT_AGGREGATE_DERIVED
OPERATION_CONTRACT
MANAGER_ESTIMATE
AI_DECISION
UNKNOWN
```

`AI_DECISION`: preview/planning only · explanation required · editable · never silent execution truth.

```text
unknown duration ≠ 0
unknown people ≠ 0
unknown workspace ≠ “no table needed”
```

---

## 9. Boundaries

### Machine

- Product/EP may declare capability / exclusivity / batch eligibility (**later**).  
- **Never** bind product definition to concrete `machine_id`.  
- Selection + exclusive interval = Machine Reservation (+ future MACHINE_RUN).

### Employee

- Demand: `required_people_*` / skills (**later**).  
- Selection: assignment command.  
- Availability calendar: future — not this contract.

### Workspace

- Demand: class + shareable (**later**).  
- Booking/compatibility evaluation: future.  
- Declaring SMALL+shareable does **not** reserve a table.

### Batch / MACHINE_RUN

```text
batch_eligible = true  → may participate in a common run
≠ already grouped
≠ reservation exists
≠ machine time allocated
```

MACHINE_RUN (future) owns the Reservation; participants keep provenance.

### Capacity

Stage 1 remains **IMPLEMENTED_INACTIVE**. This contract does not activate or seed Capacity.

---

## 10. Legacy compatibility

```text
missing resource demand fields
→ RESOURCE_REQUIREMENTS_UNKNOWN (or PARTIAL_EXISTING_ROUTING_AND_DURATION)
≠ assume no resource needed
```

Legacy tasks remain valid. Soft WC-family hints may be **shown** read-only; **no silent persistence** of invented `resource_mode` / workspace / people.

---

## 11. Plans 21 / 22 / 23 classification (QA read-only)

Labels: CONFIRMED | DERIVABLE | UNKNOWN | NOT_APPLICABLE  
(`resource_mode` DERIVABLE = soft WC-family hint only, not authoritative)

### Summary counts

| Plan | mode | machine need | people | workspace | duration | batch |
| ---- | ---- | ------------ | ------ | --------- | -------- | ----- |
| 21 (18 tasks) | DERIVABLE 17 · UNKNOWN 1 (HYBRID) | mostly N/A or DERIVABLE · 1 UNKNOWN | UNKNOWN 18 | UNKNOWN 13 · N/A 5 | CONFIRMED 1 · UNKNOWN 17 | mixed |
| 22 (5) | DERIVABLE 4 · UNKNOWN 1 | mixed | UNKNOWN 5 | UNKNOWN 3 · N/A 2 | UNKNOWN 5 | mixed |
| 23 (13) | DERIVABLE 11 · UNKNOWN 2 (METAL+VINYL) | mixed | UNKNOWN 13 | UNKNOWN 8 · N/A 5 | UNKNOWN 13 | mixed |

### Plan 23 highlights

| Task (suffix) | WC | mode | machine | people | workspace | duration | batch |
| ------------- | -- | ---- | ------- | ------ | --------- | -------- | ----- |
| vector_prep | PREPRESS | DERIVABLE | N/A | UNKNOWN | N/A | UNKNOWN | N/A |
| cnc_face_cut / back_cut / mounting_template | CNC_ROUTING | DERIVABLE | DERIVABLE | UNKNOWN | N/A | UNKNOWN | DERIVABLE |
| return_profile_forming | LETTER_FORMING | DERIVABLE | DERIVABLE | UNKNOWN | N/A | UNKNOWN | DERIVABLE |
| return_face_bonding | METAL_FAB | **UNKNOWN** | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| painting / assembly / qc / packaging | ASSEMBLY | DERIVABLE | N/A | UNKNOWN | UNKNOWN | UNKNOWN | N/A |
| led_install / electrical | LED_ASSEMBLY | DERIVABLE | N/A | UNKNOWN | UNKNOWN | UNKNOWN | N/A |
| vinyl_application | VINYL | **UNKNOWN** | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

No `tasks_json` rewrite. HYBRID tasks prove why authoritative `resource_mode` cannot be WC-derived.

---

## 12. Product System impact

Demand should originate from:

```text
Component / Operation contracts
→ ProductDefinition composition
→ ProductAggregate freeze
→ ExecutionPlan projection
```

Scheduling / Resource State must **not** invent per-product requirement logic.  
This GO does **not** change Product System runtime.

---

## 13. Schema / runtime gaps

```text
Authoritative resource_mode on task     = FUTURE_GAP
workspace_* / required_people*          = FUTURE_GAP
batch_eligible persistence              = FUTURE_GAP
MACHINE_RUN entity                      = NOT_IMPLEMENTED
Workspace booking                       = NOT_IMPLEMENTED
Employee availability calendar          = NOT_IMPLEMENTED
Duration splits                         = FUTURE_GAP
```

No migration required for this contract GO.

---

## 14. Overengineering check

| Candidate build | Verdict |
| --------------- | ------- |
| Optimizer / auto-scheduler | **No** |
| Workspace geometry engine | **No** |
| Skill matching engine beyond ORR live | **No** |
| Automatic batch composer | **No** |
| Persisting soft WC→mode defaults | **No** (HYBRID risk) |
| Readonly projection of **existing** stamps + UNKNOWN status | **Yes — next proportional slice** |

---

## 15. Recommended next slice

```text
RECOMMENDED_NEXT_SLICE =
TASK_RESOURCE_REQUIREMENT_READONLY_PROJECTION
```

**Why A over B/C:**

| Candidate | Decision |
| --------- | -------- |
| **A — READONLY_PROJECTION** | **Selected** — surface existing WC/minutes + `RESOURCE_REQUIREMENTS_UNKNOWN` / soft hints; no schema |
| B — SCHEMA_READINESS | Premature — no persistence consumer yet; hybrids need authoring source first |
| C — MACHINE_RUN_SCHEMA | Important later; blocked more by missing **demand declaration** than by missing run table |

```text
NEXT_TASK = NOT_AUTHORIZED
```

Do not start A without a separate Owner GO.

---

## 16. QA proof

```text
QA Alembic = s65
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
source/alloc rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
QA_MUTATIONS = 0
```

---

## 17. `/modules` · `/governance`

| Surface | Impact |
| ------- | ------ |
| `/modules` | **NO_IMPACT** UI — contract docs only |
| `/governance` | **NO_IMPACT** UI — demand vs availability ownership documented |
