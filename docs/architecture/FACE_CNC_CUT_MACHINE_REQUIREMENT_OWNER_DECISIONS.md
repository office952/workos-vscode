# Face CNC Cut — Machine Requirement Owner Decisions

**Task:** `FACE_CNC_CUT_MACHINE_REQUIREMENT_OWNER_DECISION_PACKAGE`  
**Owner GO:** `AUTHORIZE_FACE_CNC_CUT_MACHINE_REQUIREMENT_OWNER_DECISION_PACKAGE`  
**Date:** 2026-08-05  
**Status:** **PASS** · docs-only · **no runtime**  
**Starting HEAD:** `5e92a88b`  
**Prerequisites:** vector_prep duration E2E PASS · TRR source gap + pilot PASS · Owner D1–D6 machine/workspace package APPLIED  
**Worklog:** `docs/worklog/realignment/2026-08-05_face_cnc_cut_machine_requirement_owner_decisions.md`

```text
FACE_CNC_CUT_MACHINE_REQUIREMENT_OWNER_DECISION_PACKAGE = PASS
OPERATION = face_cnc_cut
WORKCENTER = WC_CNC_ROUTING
MACHINE_CAPABILITY = CNC_ROUTER_CUTTING
CAPABILITY_OWNER = OPERATION_CONTRACT
RESOURCE_MODE = MACHINE_BOUND
MACHINE_EXCLUSIVE = true
BATCH_ELIGIBLE = true
BATCH_ELIGIBLE_MEANING = MAY_PARTICIPATE_IN_FUTURE_SHARED_CNC_RUN
MACHINE_ID_SELECTION = DEFERRED_TO_RESERVATION
MACHINE_RUN = NOT_IMPLEMENTED
BATCH_GROUPING = NOT_IMPLEMENTED
NEXT_PILOT_FIELDS = machine_capability_code · resource_mode · batch_eligible
RUNTIME_IMPLEMENTATION = NOT_STARTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Objective

Close the minimum technical demand decisions for:

```text
operation_code = face_cnc_cut
workcenter = WC_CNC_ROUTING
```

before any runtime pilot that stamps machine requirement fields onto Aggregate → ExecutionPlan → read-only projection.

---

## 2. Repo identity map (do not collapse)

| Layer | Exact code | Role |
| ----- | ---------- | ---- |
| Priced / Aggregate op | `face_cnc_cut` | Product / Aggregate operation |
| Dossier task rule | `cnc_face_cut` | Task short / EP technical name |
| Process-graph process | `CUT_FACE` | Product-process contract on FACE |
| ORR registry op | `cnc_cutting` | Live eligibility / allowlist join |
| Canonical WC | `WC_CNC_ROUTING` | Already frozen on Aggregate / EP |
| Pricing rate code | `CNC_ROUTER` | Commercial EUR/ml — **not** capability |
| Machine instance | `MCH-CNC-4020` | ORR allowlist — **not** capability stamp |
| Inventory type | `cnc_router` | Machine type — **not** capability stamp |
| Skill | `SK_CNC_OPERATOR` | ORR live — **not** task demand stamp |
| Process capability | `CNC_ROUTER_CUTTING` | Canonical capability demand |

Evidence roots:

- `backend/data/product_process/catalogs.py` — `CAPABILITY_CODES`, `CUT_FACE` → `face_cnc_cut`
- `backend/data/product_process/volumetric_letters_v1.py` — `CUT_FACE.required_capabilities=["CNC_ROUTER_CUTTING"]`
- `backend/seeds/seed_operational_workforce_registry.py` — ORR `cnc_cutting` → `WC_CNC_ROUTING` / `MCH-CNC-4020`
- Soft projection today: `WC_CNC_ROUTING` → `resource_mode_hint=MACHINE_BOUND`

---

## 3. Owner decisions

### D1 — Canonical machine capability

| | |
| - | - |
| **Decision** | `MACHINE_CAPABILITY = CNC_ROUTER_CUTTING` |
| **Plain language** | Face CNC cut needs a CNC router cutting capability — not a named machine. |
| **Why this code** | Only capability in `CAPABILITY_CODES` attached to `CUT_FACE` / priced `face_cnc_cut`. |
| **Rejected as capability stamp** | `MCH-CNC-4020` (instance) · `cnc_cutting` (ORR op) · `WC_CNC_ROUTING` (routing) · `CNC_ROUTER` (pricing) · `cnc_router` (type) · invented `CNC_ROUTER` / `ROUTER_CUTTING` aliases |
| **Unchanged** | ORR live allowlist continues to list concrete machines for readiness |
| **Deferred** | Binding `machines.capabilities` column to this code (seed CNC-4020 has no capabilities list today) |

```text
task declares CNC_ROUTER_CUTTING
Machine Reservation selects machine_id (e.g. MCH-CNC-4020)
```

### D2 — Ownership

| | |
| - | - |
| **Decision** | Capability requirement owned by **Operation / Process Contract** |
| **Operation Contract owns** | `machine_capability_code = CNC_ROUTER_CUTTING` · machine-bound mode · exclusivity · batch eligibility flag |
| **FACE Component Contract owns** | Geometry / material / process truth that **feeds** the operation (`FACE_SHEET`, cut process `CUT_FACE`) — not `machine_id` |
| **Product Template** | Composes only — does not invent private CNC demand rules |
| **ORR** | Live availability / allowlist / skills — not the Product System demand SoT for capability stamp |
| **Rejected** | Putting concrete `machine_id` into Component or Product Template |

### D3 — Machine-bound exclusivity

| | |
| - | - |
| **Decision** | `RESOURCE_MODE = MACHINE_BOUND` · `machine_exclusive = true` |
| **Plain language** | This task needs an exclusive machine interval while running — not a shared table story. |
| **Does not mean** | A specific `machine_id` is chosen at product/definition time |
| **Who selects machine** | Machine Reservation (existing writer) |
| **Soft hint today** | Projection already derives `MACHINE_BOUND` from `WC_CNC_ROUTING` — next pilot may stamp authoritative `resource_mode` |

### D4 — Batch eligibility

| | |
| - | - |
| **Decision** | `BATCH_ELIGIBLE = true` |
| **Meaning now** | Task **may participate** in a future shared CNC run / plate nest (`MACHINE_RUN`) |
| **Does not mean** | Already batched · already reserved · already grouped · machine time already allocated |
| **Aligns with** | Owner package D4 (`MACHINE_RUN` owns one Reservation; participants keep provenance) |
| **Material nesting** | Intake sheet nesting (plexi/forex) is **not** `MACHINE_RUN` and does not satisfy this flag by itself |
| **Deferred** | `batch_grouping_key` · run id · auto-grouper · MACHINE_RUN entity |

```text
batch_eligible = true
≠ automatically grouped
≠ MACHINE_RUN exists
```

### D5 — Minimum fields for the next implementation pilot

| Include in next pilot | Defer |
| --------------------- | ----- |
| `machine_capability_code` (= `CNC_ROUTER_CUTTING`) | `machine_id` |
| authoritative `resource_mode` (= `MACHINE_BOUND`) **or** keep soft hint until stamp path ready | `batch_grouping_key` / `run_id` |
| `batch_eligible` (= `true`) | machine runtime / setup minutes |
| (existing) `workcenter` = `WC_CNC_ROUTING` | people / workspace |
| | CNC planning duration (separate Owner formula GO) |
| | Capacity activation · Phase B/C |

```text
NEXT_PILOT_FIELDS =
  machine_capability_code
  resource_mode
  batch_eligible
```

Path (future implementation GO only):

```text
Operation / process contract (CNC_ROUTER_CUTTING + MACHINE_BOUND + batch_eligible)
  → ProductAggregate freeze
  → ExecutionPlan operational task snapshot
  → read-only resource requirement projection
```

No recalculation in Scheduling, Capacity, or the projection layer.

---

## 4. Field ownership matrix (this pilot)

| Field | Needed for next pilot? | Owner | Source | Manual / derived | Consumer |
| ----- | ---------------------- | ----- | ------ | ---------------- | -------- |
| `workcenter` | Already present | Aggregate ORR freeze | ORR WC allowlist | derived at freeze | routing / projection |
| `machine_capability_code` | **Yes** | Operation / process contract | `CNC_ROUTER_CUTTING` | declared | Reservation match (later) · projection |
| `resource_mode` | **Yes** (authoritative) | Operation contract | `MACHINE_BOUND` | declared | planners · projection |
| `machine_exclusive` | Implied by mode; stamp optional | Operation contract | `true` | declared | Reservation exclusivity semantics |
| `batch_eligible` | **Yes** | Operation contract | `true` | declared | future MACHINE_RUN eligibility |
| `machine_id` | No | Reservation | selected | selected | commitment |
| `batch_grouping_key` | No | MACHINE_RUN (future) | — | — | grouping |
| `estimated_time_minutes` | Not this pilot | Planning duration contract (future) | — | — | planning |

---

## 5. Needed-now versus future-only

### Closed by this package (decision only)

```text
capability code
ownership
MACHINE_BOUND + exclusive
batch_eligible meaning
next pilot field set
```

### Still future / separate GO

```text
runtime stamp Aggregate → EP → projection
MACHINE_RUN entity + auto grouping
machines.capabilities inventory join
CNC duration contract
people / workspace
Capacity seed/activation
Phase B wiring
```

---

## 6. Answers to the GO questions

| # | Question | Answer |
| - | -------- | ------ |
| 1 | What capability? | **`CNC_ROUTER_CUTTING`** |
| 2 | Who owns it? | **Operation / Process Contract**; FACE feeds geometry/material/process |
| 3 | Machine-bound exclusive? | **Yes** — `MACHINE_BOUND`, `machine_exclusive=true` |
| 4 | Batch-eligible? | **Yes** |
| 5 | Meaning now? | May participate in a future shared CNC run — not already batched |
| 6 | Deferred to MACHINE_RUN? | Grouping, run id, shared reservation ownership, machine-time-once accounting |
| 7 | Minimal EP fields next? | `machine_capability_code` · `resource_mode` · `batch_eligible` (+ existing WC) |

---

## 7. Overengineering check

| Candidate | Verdict |
| --------- | ------- |
| New capability vocabulary | **No** — reuse `CNC_ROUTER_CUTTING` |
| Stamp `MCH-CNC-4020` on product | **No** — Reservation selects instance |
| Implement MACHINE_RUN now | **No** |
| CNC duration in same slice | **No** — needs separate formula Owner decision |
| People / workspace | **No** |

---

## 8. QA proof (this GO)

```text
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
capacity source/alloc rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
QA_MUTATIONS = 0
RUNTIME_IMPLEMENTATION = NOT_STARTED
```

---

## 9. Roadmap awareness checkpoint

```text
Nota roadmap awareness: 9/10
Poziția curentă: face_cnc_cut machine requirement decision (docs-only)
Cât sunt în direcția stabilită: 85/100%
Dead Pieces Check:
  - no invented capability codes
  - no MACHINE_RUN runtime
  - no Capacity activation
  - no plan mutations
Impact Harta sistemelor:
  - Product/Operation demand clarified
  - Reservation remains machine_id selector
  - Projection remains consumer
Impact Guvernanța sistemului:
  - demand vs availability boundary preserved
  - batch_eligible honesty preserved
Forbidden scope respected: YES
No runtime implementation
No MACHINE_RUN
No batch grouping
No Capacity activation
No Phase B
No Phase C
No frontend/Mobile
```

---

## 10. Next task

```text
RECOMMENDED_NEXT_SLICE =
FACE_CNC_CUT_MACHINE_REQUIREMENT_READONLY_PROJECTION_OR_STAMP_PILOT
```

Implementation only with a **separate** Owner GO.  
Do not start MACHINE_RUN, Capacity, or CNC duration in that slice unless explicitly authorized.
