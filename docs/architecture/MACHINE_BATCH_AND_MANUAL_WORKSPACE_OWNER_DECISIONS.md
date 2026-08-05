# Machine Batch and Manual Workspace — Owner Decisions

**Task:** `MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISION_PACKAGE`  
**Owner GO:** `AUTHORIZE_MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISION_PACKAGE`  
**Date:** 2026-08-05  
**Status:** **PASS** · Owner decisions applied · **docs-only · no runtime**  
**Starting HEAD:** `4ed8aaea`  
**Prerequisite:** `CAPACITY_RESOURCE_MODEL_REALIGNMENT = PASS`  
**Worklog:** `docs/worklog/realignment/2026-08-05_machine_batch_and_manual_workspace_owner_decisions.md`

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

Owner confirmation source: chat acceptance of the six-decision set (METAL_FAB/VINYL HYBRID; OPTION_A classes; conditional cant+vinyl share; MACHINE_RUN owns one Reservation; PREPRESS person-driven; FIELD outside shop Capacity). Recommendations were **not** treated as accepted until that Owner set was stated.

---

## 1. Owner decision matrix

### D1_HYBRID_WORKCENTERS

| | |
| - | - |
| **Plain language** | `WC_METAL_FAB` and `WC_VINYL_APPLICATION` are **HYBRID**. Each task declares machine / workspace / people needs (or a combination). |
| **Product meaning** | Workcenter code is routing/organization only — **not** a permanent bottleneck selector. |
| **Changes conceptually** | Demand lives on the **task**; availability stays in machine / workspace / employee systems. |
| **Unchanged** | Canonical WC registry; ORR workcenter stamps; Machine Reservation exclusivity for concrete `machine_id`. |
| **Deferred** | Runtime task resource-requirement fields; auto-inference of reservations from WC code (**forbidden**). |
| **Risks prevented** | Treating every metal/vinyl task as “always table” or “always machine”. |
| **Activation gate** | Future task contract GO after this package. |

### D2_MANUAL_WORKSPACE_CLASSES

| | |
| - | - |
| **Plain language** | Initial classes: **SMALL** · **MEDIUM** · **FULL_TABLE** · **LARGE_AREA**. |
| **Product meaning** | Operator-readable size class for table/zone demand — no false m² precision. |
| **Changes conceptually** | Manual WC family uses class-based occupancy language. |
| **Unchanged** | No geometry schema; no new tables in this GO. |
| **Deferred** | Exact m² (OPTION_C); abstract capacity units (OPTION_B). |
| **Risks prevented** | Premature geometry without a measurement SoT. |
| **Activation gate** | Readonly task contract / workspace occupancy GO. |

**Overengineering check:** exact workspace geometry is deferred — no canonical reliable measurement source in repo today.

### D3_CONDITIONAL_WORKSPACE_SHARING

| | |
| - | - |
| **Plain language** | Small vinyl + letter return/cant may share a table **conditionally**, not absolutely. |
| **Product meaning** | `SHARE_DEFAULT = CONDITIONAL`. |
| **Share allowed only when** | (1) each task permits sharing; (2) neither requires FULL_TABLE; (3) no explicit incompatibility. |
| **Unchanged** | Machine exclusivity rules; Capacity Stage 1 inactive. |
| **Deferred** | Hardcoded pairwise product rules; dust/fragile catalogs as code. |
| **Risks prevented** | Absolute “always share” ignoring large pieces, dust, blocked access, fragile goods. |
| **Activation gate** | Workspace occupancy + compatibility service (future). |

### D4_MACHINE_RUN_OWNS_RESERVATION

| | |
| - | - |
| **Plain language** | A **MACHINE_RUN** owns **exactly one** Machine Reservation. Many tasks/plans/products may participate. Machine time counted **once**. Provenance stays per task/product. |
| **Product meaning** | Batch/nest run = one exclusive machine interval with multiple participants. |
| **Changes conceptually** | Future run entity sits **above** Reservation; tasks **participate**, they do not each own the machine interval. |
| **Unchanged** | Existing Reservation writer exclusivity; no batch entity created now. |
| **Deferred** | Runtime MACHINE_RUN table/service; automatic grouping. |
| **Risks prevented** | Double-counting machine minutes; merging task/commercial identity. |
| **Activation gate** | Separate controlled grouping service + Owner GO. |

**Critical:** `batch_eligible` ≠ automatically grouped. Grouping requires a future controlled service and Owner GO.

### D5_PREPRESS_PERSON_DRIVEN

| | |
| - | - |
| **Plain language** | Stage-1 PREPRESS = **PERSON_DRIVEN**. No exclusive workstation by default. |
| **Product meaning** | Capacity/reservation for “any PC” is not invented. |
| **Later only if factual** | Unique workstation, RIP, license, or device inventory constraint. |
| **Unchanged** | WC_PREPRESS routing; employee skills/assignment. |
| **Deferred** | Exclusive station inventory for prepress. |
| **Risks prevented** | Fake exclusive booking of generic computers. |
| **Activation gate** | Factual station inventory + Owner GO. |

### D6_FIELD_OUTSIDE_SHOP_CAPACITY

| | |
| - | - |
| **Plain language** | `WC_FIELD_INSTALLATION` stays **outside shop Capacity**. |
| **Product meaning** | Field has team, vehicle, location, travel, client schedule, mount gear, weather — separate future boundary. |
| **Unchanged** | Shop CNC / tables / internal Capacity disposition. |
| **Deferred** | Field planner (no implementation now). |
| **Risks prevented** | Mixing field variables into shop WC-minutes or table sharing. |
| **Activation gate** | Dedicated field-planning Owner GO. |

---

## 2. MACHINE_RUN contract (conceptual)

```text
MACHINE_RUN
├── owns exactly one Machine Reservation (one machine, one interval)
├── participant tasks (may span plans/products when operationally valid)
├── machine time recorded once for the run
└── per-task / per-product / material provenance preserved
```

| Rule | Statement |
| ---- | --------- |
| Identity | One real machine execution interval |
| Reservation | Exactly one open/confirmed reservation owned by the run |
| Participants | Multiple tasks may participate |
| Cross-plan | Allowed when operationally valid — not automatic |
| Machine time | Counted once — not once per participant task |
| Task identity | Not merged |
| Commercial ownership | Not merged |
| Batch eligibility | Flag only — **does not** auto-group |

**Reuse:** Machine Reservation exclusivity (existing). **Do not** invent a parallel exclusive-time system.  
**Gap:** no production MACHINE_RUN entity yet — Intake material nesting is **not** this contract.

---

## 3. Manual workspace contract (conceptual)

### Classes (Owner-confirmed)

| Class | Conceptual behavior |
| ----- | ------------------- |
| SMALL | May normally share with other shareable SMALL/MEDIUM if compatible |
| MEDIUM | May share conditionally (size + compatibility) |
| FULL_TABLE | Exclusive on that table |
| LARGE_AREA | Needs a separately identified area (not a standard table share) |

### Additional rules

- Compatibility may **override** size-based sharing (block or allow).  
- `workspace_occupation_minutes` may exceed `active_labor_minutes` (e.g. adhesive cure).  
- No exact m² in this stage.

---

## 4. Operation compatibility (bounded initial rule)

Sharing allowed only when **all** hold:

1. Each task is marked shareable.  
2. Workspace classes fit (neither FULL_TABLE; LARGE_AREA not on a shared standard table).  
3. Neither task explicitly requires exclusivity.  
4. No incompatibility rule applies.

| Illustrative compatible | Illustrative potentially incompatible |
| ----------------------- | ------------------------------------- |
| Small vinyl + return/cant on separate small letters | Dust-producing work + vinyl |
| | Full-panel vinyl + another table task |
| | Task needing unobstructed full-table access |

Examples are explanatory — **not** hardcoded product rules.

---

## 5. Hybrid workcenter rule

For `WC_METAL_FAB` and `WC_VINYL_APPLICATION`:

```text
Workcenter classification ≠ single bottleneck
Task declares bounded resource requirement
Machine claim · workspace claim · people claim remain separate systems
No automatic machine/workspace reservation from workcenter code alone
```

Examples (demand declaration, not runtime):

```text
METAL_FAB task may need: weld machine + person + table/zone
VINYL_APPLICATION task may need: person + table/surface
  (+ cutting/plotter only as a separate task when required)
```

```text
Task contract = demand declaration
Resource systems = availability truth
```

---

## 6. PREPRESS and FIELD boundaries

| Domain | Stage-1 disposition |
| ------ | ------------------- |
| PREPRESS | PERSON_DRIVEN; exclusive station only from factual inventory later |
| FIELD_INSTALLATION | Outside shop Capacity; future field model (team/vehicle/travel/location/appointment/equipment/weather) — not implemented |

---

## 7. Capacity Stage 1 disposition (preserved)

```text
CAPACITY_STAGE_1_DISPOSITION = OPTION_D_KEEP_IMPLEMENTED_INACTIVE
```

| Keep | Do not |
| ---- | ------ |
| Code + s65 schema | Seed minutes |
| Writer/evaluator plumbing dormant | Activate Capacity domain |
| Possible later soft aggregate reuse (separate decision) | Treat WC-minutes as truth for shared manual workspaces |
| | Delete / refactor / repurpose Stage 1 in this GO |

```text
CAPACITY_ACTIVATION = NOT_AUTHORIZED
CAPACITY_SEED = NOT_AUTHORIZED
```

---

## 8. Existing code / schema impact

| Area | Impact |
| ---- | ------ |
| Machine Reservation | Unchanged; conceptual owner under future MACHINE_RUN |
| `work_area` as exclusive reservation today | Known tension with shareable tables — **not fixed here**; future workspace occupancy |
| Capacity Stage 1 | Remains inactive |
| ORM / migrations | **None** |
| Frontend / Mobile | **None** |

---

## 9. QA proof (read-only)

```text
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Machine Reservation = ACTIVE
Capacity = NOT_CONFIGURED
capacity source rows = 0
capacity allocation rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
QA_MUTATIONS = 0
```

---

## 10. `/modules` · `/governance`

| Surface | Impact |
| ------- | ------ |
| `/modules` | **NO_IMPACT** UI — document mentally: MACHINE_RUN future; manual workspace future; Capacity inactive |
| `/governance` | **NO_IMPACT** UI — Owner-confirmed splits: machine run, workspace class/share, hybrid task demand, prepress person, field outside shop |

---

## 11. Next task

```text
NEXT_TASK = NOT_AUTHORIZED
```

No runtime implementation candidate is started by this package. A later Owner GO may authorize a **readonly** task resource requirement contract or a MACHINE_RUN design spike — only after explicit GO.
