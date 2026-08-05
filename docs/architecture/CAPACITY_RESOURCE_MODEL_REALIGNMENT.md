# Capacity Resource Model Realignment

**Task:** `CAPACITY_RESOURCE_MODEL_REALIGNMENT`  
**Owner GO:** `AUTHORIZE_CAPACITY_RESOURCE_MODEL_REALIGNMENT`  
**Date:** 2026-08-05  
**Status:** **PASS** · Conceptual realignment · Owner decision package **APPLIED** · **no implementation · no Capacity activation**  
**Starting HEAD:** `681f1ac0`  
**Worklog:** `docs/worklog/realignment/2026-08-05_capacity_resource_model_realignment.md`  
**Owner decisions:** `docs/architecture/MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md`

```text
CAPACITY_RESOURCE_MODEL_REALIGNMENT = PASS
OWNER_DECISION_PACKAGE = APPLIED
MACHINE_BOUND_MODEL = FINALIZED
MACHINE_EXCLUSIVITY = CONFIRMED
MACHINE_RUN = OWNER_CONFIRMED_CONCEPT
MANUAL_WORKSPACE_CLASSES = OWNER_CONFIRMED
WORKSPACE_SHARING = CONDITIONAL
HYBRID_WORKCENTERS = OWNER_CONFIRMED
PREPRESS = PERSON_DRIVEN_STAGE_1
FIELD_INSTALLATION = OUTSIDE_SHOP_CAPACITY
EMPLOYEE_RESOURCE_BOUNDARY = FINALIZED
TASK_RESOURCE_REQUIREMENT_CONTRACT = BOUNDED_MINIMAL
CAPACITY_STAGE_1_DISPOSITION = OPTION_D_KEEP_IMPLEMENTED_INACTIVE
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
CAPACITY_STAGE_1_QA_SEED_READINESS = SUPERSEDED_BY_RESOURCE_MODEL_REALIGNMENT
CAPACITY_QA_ACTIVATION = NOT_AUTHORIZED
CAPACITY_QA_SEED = NOT_AUTHORIZED
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_SOURCE_ROWS = 0
QA_CAPACITY_ALLOCATIONS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

Supersedes the prior seed-readiness push to configure workcenter-minutes for all WCs:

```text
Reason: single workcenter-minutes model was insufficient
for shared manual workspaces and multi-person operations
```

Prior report retained: `docs/architecture/CAPACITY_STAGE_1_QA_CONFIGURATION_AND_SEED_READINESS.md`.

---

## 0. Central principle

```text
MACHINE ≠ WORKTABLE
WORKTABLE ≠ EMPLOYEE
WORKCENTER ≠ PHYSICAL_RESOURCE
```

| Concept | Meaning |
| ------- | ------- |
| **Workcenter** | Organizational / routing zone (`WC_*`) |
| **Machine** | Technical resource; normally **one active run** per interval |
| **Manual workspace** | Table / area; **conditionally shareable** |
| **Employee** | Human with skills, assignment, real program — outside exclusive machine claim |
| **Task** | Concrete demand: duration, skills, machine/workspace needs, compatibility |

Do **not** apply one Capacity formula to all workcenters.

---

## 1. Confirmed Owner truths

```text
DECISIONS_CONFIRMED_FROM_CURRENT_DISCUSSION
```

1. Machines execute **one run** at a time.  
2. One CNC **batch/nesting/run** may contain parts from multiple jobs; the machine still runs **one** interval.  
3. Assembly tables may host **simultaneous** compatible operations.  
4. A table is **not** automatically exclusive.  
5. Manual capacity depends on size, space, people, compatibility, access, tools.  
6. No generic minutes per WC now.  
7. Capacity is **not** activated before this realignment.

```text
DECISIONS_INFERRED_FROM_REPO
```

- Machine Reservation already enforces exclusive overlap on `machine_id` (incl. `work_area` rows).  
- No production batch / nesting entity for multi-plan machine runs.  
- Capacity Stage 1 = workcenter DAY minutes pool — separate from Reservation.  
- Material nesting exists in Intake/commercial — not Resource State batch.  
- `required_people` / workspace share / occupation vs labor — **absent** on tasks.

```text
DECISIONS_REQUIRING_OWNER
```

See §17 (simple questions).

---

## 2. What exists today (repo)

| Layer | Exists | Notes |
| ----- | ------ | ----- |
| Machine Reservation (R9) | Yes | Exclusive open windows per `machine_id`; ACTIVE in QA; **0 rows** |
| Capacity Stage 1 source/alloc | Yes (code + s65) | NOT_CONFIGURED; **0 rows** |
| Scheduling | Yes | ACTIVE; **0 rows** |
| Workcenter routing | Yes | 12 canonical `WC_*` on EP tasks |
| `machines.resource_kind` | `machine` \| `tool` \| `work_area` | Work areas registered as machine rows |
| Production batch / MACHINE_RUN entity | **No** | |
| Shareable workspace occupancy | **No** | Work_area reserved = exclusive like machine |
| Employee assignment | Embedded + transitions | Availability calendar **out of triad** |
| `required_people*` | **No** | |
| Sessions / Reality | Separate | ≠ Capacity ≠ Reservation |

---

## 3. Workcenter classification (12 canonical)

Labels from `operational_catalog.py`. Classification is operational-family, not pricing.

| Code | Label | Family | Machines / areas (QA) | Exclusive? | Batchable? | Stage 1 WC-minutes suitability | Recommended future model |
| ---- | ----- | ------ | --------------------- | ---------- | ---------- | ------------------------------ | ------------------------ |
| WC_CNC_ROUTING | CNC router | **MACHINE_BATCHABLE** | MCH-CNC-4020, MCH-STYRO-CUTTER | Machine exclusive per run | Yes (multi-job nest) | Weak as sole control | Machine Reservation + MACHINE_RUN/batch |
| WC_LETTER_FORMING | Modelare cant litere | **MACHINE_BATCHABLE** | MCH-CNC-CANT-LITERE | Exclusive per run | Letters may share a program | Weak alone | Machine Reservation + optional batch |
| WC_LASER_CUTTING | Laser | **MACHINE_BATCHABLE** | MCH-LASER-CNC | Exclusive per run | Sheet nest | Weak alone | Machine Reservation + batch |
| WC_CUT | Cutter plotter | **MACHINE_BATCHABLE** | MCH-CUTTER-PLOTTER | Exclusive per run | Nest/queue | Weak alone | Machine Reservation + batch |
| WC_PRINT | Print | **MACHINE_BATCHABLE** | MCH-EPSON-60800 | Exclusive per run | Job queue / roll | Weak alone | Machine Reservation + queue/batch |
| WC_LAMINATE | Laminare | **MACHINE_EXCLUSIVE** | MCH-LAMINATOR-XPRO | One run | Rarely multi-job nest | Weak alone | Machine Reservation |
| WC_METAL_FAB | Sudură | **HYBRID** | Weld machines + WA-WELD-TABLE | Machines exclusive; table conditional | Limited | **Unsuitable** as single pool | Split machine claim vs workspace share |
| WC_VINYL_APPLICATION | Colantare | **HYBRID** | MCH-RIGID-FILM-LAMINATOR + manual table work | Laminator exclusive; table shareable | — | **Unsuitable** alone | Machine + MANUAL_SHARED_WORKSPACE |
| WC_ASSEMBLY | Ansamblare | **MANUAL_SHARED_WORKSPACE** | WA-ASSEMBLY-01/02 | Conditional share | N/A | **Misleading** if exclusive minutes | Workspace occupancy + people |
| WC_LED_ASSEMBLY | Electric | **MANUAL_SHARED_WORKSPACE** | No machine row; bench ops | Conditional share | N/A | Misleading alone | Workspace + skills/people |
| WC_PREPRESS | Grafică / Prepress | **MANUAL_PERSON_DRIVEN** | No machine | Person/station | N/A | Weak / person-bound | Employee availability + skills |
| WC_FIELD_INSTALLATION | Montaj teren | **FIELD_OPERATION** | No shop machine | Site/crew | N/A | **Out of shop WC-minutes** | Field teams / separate model |

**UNKNOWN:** none of the 12 — families assigned from Owner truths + registry evidence. Hybrid edges (metal/vinyl) need Owner confirm (§17).

Forbidden as Capacity seed identity: `WC_CNC`, pricing codes (`CNC_ROUTER`, …).

---

## 4. Machine-bound model

```text
one machine → one active reservation/run per time interval
```

### Confirmed in code

- Open reservation overlap on same `machine_id` → `overlap_conflict`.  
- Applies to **any** row in `machines`, including `resource_kind=work_area` (no exception).  
- Half-open windows; adjacency allowed.

### Must stay separate (never merge)

| Truth | Domain |
| ----- | ------ |
| Machine running minutes | Reservation / future MACHINE_RUN |
| Operator labor minutes | Assignment + sessions / Reality |
| Commercial machine rate | `workcenter_rates` / CostEngine |
| Internal machine cost | Cost / profitability |

### Future fields (not now)

setup / cleanup / downtime / maintenance — needed later for accurate run windows; **not** required to freeze exclusivity rule.

---

## 5. Machine batch / MACHINE_RUN (conceptual)

```text
MACHINE_RUN (preferred name)
≈ PRODUCTION_BATCH for shop floor
```

| Rule | Statement |
| ---- | --------- |
| Ownership | Batch/run **owns** the machine reservation interval |
| Participation | Many tasks / plans / parts **participate** |
| Machine time | Counted **once** for the run |
| Cost/runtime split | May allocate across participants later — provenance preserved |
| Exclusivity | Still one run on the machine |

Example:

```text
CNC run 101  →  reservation on MCH-CNC-4020 [t0,t1)
  ├── parts from product A (plan X)
  ├── parts from product B (plan Y)
  └── parts from product C (plan Z)
```

### Existing reusable truth?

| Candidate | Reuse? |
| --------- | ------ |
| Intake / flat material nesting | **No** as Resource State batch — commercial sheet qty |
| Machine Reservation | **Yes** — exclusive interval grain |
| Capacity allocation | **No** — minutes pool, not run identity |

```text
PRODUCTION_BATCH_ENTITY = FUTURE_GAP
Do not invent parallel batch system that ignores Reservation.
```

---

## 6. Manual shared-workspace model

Tables/zones are **not** implicit exclusive machines.

### Recommended minimum: OPTION_A (class)

```text
workspace_requirement ∈ { SMALL, MEDIUM, FULL_TABLE, LARGE_AREA }
```

| Class | Sharing (initial rules) |
| ----- | ----------------------- |
| SMALL | May share with SMALL / MEDIUM if compatible |
| MEDIUM | May share with SMALL if compatible |
| FULL_TABLE | Exclusive on that table |
| LARGE_AREA | Special zone; not a standard table share |

**OPTION_B** (abstract units) / **OPTION_C** (m²): defer — repo lacks workspace geometry; OPTION_C risks false precision.

### Occupation ≠ labor

```text
workspace_occupation_minutes  ≥  active_labor_minutes  (often)
```

Example: adhesive cure 60 min occupies table; person active 10 min.

---

## 7. Operation compatibility (conceptual)

Future contract necessities (design only):

```text
workspace_shareable
workspace_requirement          # OPTION_A class
workspace_compatibility_group  # or pairwise rules later
exclusive_workspace_reason
```

Examples (Owner-informed, not coded):

| Pair | Likely |
| ---- | ------ |
| Edge bonding + small vinyl on small parts | Compatible share |
| Large panel vinyl wrap | FULL_TABLE exclusive |
| Dusty sanding + vinyl | Incompatible |
| Cure wait + other piece work | Occupies space without continuous labor |

---

## 8. Employee boundary

```text
Employee Assignment ≠ Machine Reservation
≠ Workspace Occupancy ≠ Capacity Allocation ≠ Work Session
```

| Modeled | Not modeled (keep out of Stage 1 pool) |
| ------- | -------------------------------------- |
| `assigned_employee_id` + transitions | Availability calendar |
| Skills / WC authorizations | `required_people_min` / crew |
| Field teams (separate) | `employees × 480` as capacity |

Never compute employee capacity as headcount × 480 without real program, absences, overlaps, skills.

---

## 9. Duration categories (conceptual)

| Category | Meaning | Needed |
| -------- | ------- | ------ |
| `machine_runtime_minutes` | Machine busy in run | Later (with MACHINE_RUN) |
| `active_labor_minutes` | Hands-on person time | Later |
| `workspace_occupation_minutes` | Table/zone blocked | Later (manual model) |
| `waiting_curing_minutes` | Passive without labor | Later optional |
| `estimated_duration_minutes` | Task planning (exists, often null) | Keep; null preserved |

---

## 10. Task Resource Requirement Contract (bounded)

Do **not** approve a large field set. Minimal proportional map:

| Field | Verdict | Why now? |
| ----- | ------- | -------- |
| `resource_mode` | **needed later** | Discriminates MACHINE / WORKSPACE / PERSON / FIELD / HYBRID |
| `estimated_duration_minutes` + `duration_source` | **exists** | Keep null-preserving honesty |
| `machine_capability_required` / workcenter via ORR | **exists** | Routing already |
| `batch_eligible` / `batch_grouping_key` | **needed later** | After MACHINE_RUN decision |
| `workspace_requirement` (OPTION_A) | **needed later** | Manual WC family |
| `workspace_shareable` | **needed later** | Same |
| `workspace_occupation_minutes` | **needed later** | Cure/occupy split |
| `active_labor_minutes` | **needed later** | ≠ occupation |
| `required_people_min` / `recommended` | **needed later** | Multi-person ops |
| `required_skill_codes[]` | **exists on ORR** | Reuse; don't duplicate loosely |
| `parallelizable` | **optional later** | |
| Exact m² / unit capacity | **optional / avoid now** | OPTION_C/B deferred |

```text
TASK_RESOURCE_REQUIREMENT_CONTRACT = BOUNDED_MINIMAL
Next proportional step = Owner decision package, then optional readonly contract
```

---

## 11. Capacity Stage 1 disposition

| Option | Verdict |
| ------ | ------- |
| A — operational blocker for all WCs | **Reject** — wrong for shared tables / people |
| B — aggregate planning indicator for selected WCs | **Later reuse possible** |
| C — only homogeneous machine-bound WCs | **Later reuse possible** |
| **D — keep implemented, inactive** | **SELECTED now** |

```text
CAPACITY_STAGE_1_DISPOSITION = OPTION_D_KEEP_IMPLEMENTED_INACTIVE
```

### Why D

1. Code + s65 schema already land; deleting/refactoring is waste and risk.  
2. Activating WC-day minutes **before** machine-run vs workspace-share rules invites double-counting (reservation time + WC pool).  
3. Seed readiness PARTIAL was correct about missing minutes, but **insufficient** as the next product step — model family split comes first.  
4. Later, Stage 1 plumbing may feed **OPTION_B/C** for a narrow WC subset as soft planning — never as sole truth for MANUAL_SHARED_WORKSPACE.

```text
CAPACITY_QA_SEED = NOT_AUTHORIZED
CAPACITY_QA_ACTIVATION = NOT_AUTHORIZED
```

Mark prior seed readiness:

```text
CAPACITY_STAGE_1_QA_SEED_READINESS = SUPERSEDED_BY_RESOURCE_MODEL_REALIGNMENT
```

---

## 12. Do not duplicate

| Concern | Owner |
| ------- | ----- |
| Exclusive machine interval | Machine Reservation (+ future MACHINE_RUN) |
| Aggregate WC minutes (dormant) | Capacity Stage 1 (inactive) |
| Task responsibility | Employee Assignment |
| Real worked time | Work Session / Execution Reality |
| Table/zone occupation | Future Workspace Occupancy |
| Multi-job machine run | Future MACHINE_RUN / batch |

---

## 13. Scale (50 products) — analysis only

| Concern | Implication |
| ------- | ----------- |
| Machine exclusivity | Overlap query per `machine_id` — already indexed path; stays O(open rows on machine) |
| Batch grouping | Need run identity + participant links — without it, 50 products → false per-task exclusive blocks |
| Workspace sharing | Class + compatibility — avoid loading all tasks in memory; filter by workspace_id + day |
| Employee concurrency | Assignment ≠ calendar; don't fake with Capacity |
| Pagination / planner horizon | Day/week horizons; no auto-optimizer |
| Indexes | Reservation overlap + future (workspace_id, day); Capacity indexes already for WC+day |

No optimization engine. No auto-scheduling.

---

## 14. Schema gaps (future — not this GO)

```text
MACHINE_RUN / batch participant          = FUTURE_GAP
WORKSPACE_OCCUPANCY                      = FUTURE_GAP
work_area shareable mode (≠ exclusive reservation) = FUTURE_GAP
task resource_mode + OPTION_A fields     = FUTURE_GAP
required_people*                         = FUTURE_GAP
occupation vs labor minutes              = FUTURE_GAP
recurring capacity rules                 = FUTURE_GAP (unchanged)
```

---

## 15. Phase B / Phase C

```text
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

Capacity NOT_CONFIGURED still fail-closes aggregate. Richer resource model does **not** unlock Phase B.

---

## 16. `/modules` · `/governance`

| Surface | Impact |
| ------- | ------ |
| `/modules` | **NO_IMPACT** UI now — document mentally: Machine Reservation ACTIVE; Capacity Stage 1 inactive; Batch Run & Manual Workspace = future boundaries |
| `/governance` | **NO_IMPACT** UI — authority split: machine / workspace / employee / task requirements / Capacity (dormant) |

---

## 17. Owner decisions — applied

The six questions from the realignment pass are **Owner-confirmed** and recorded in:

`docs/architecture/MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md`

```text
D1 HYBRID task-driven demand
D2 SMALL / MEDIUM / FULL_TABLE / LARGE_AREA
D3 CONDITIONAL workspace sharing
D4 MACHINE_RUN owns one Machine Reservation
D5 PREPRESS PERSON_DRIVEN
D6 FIELD outside shop Capacity
```

---

## 18. Future candidate

```text
NEXT_TASK = NOT_AUTHORIZED
```

No runtime task is started from the decision package. A later explicit Owner GO may authorize a bounded readonly task resource contract or MACHINE_RUN design — not implied by this document.

---

## 19. QA boundary

```text
QA Alembic = s65
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
capacity source rows = 0
capacity allocation rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA unchanged (read-only task)
```
