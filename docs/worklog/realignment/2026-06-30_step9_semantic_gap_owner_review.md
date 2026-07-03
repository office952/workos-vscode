# Step 9 — Semantic Gap Owner Review (Decision Table)

**Date:** 2026-06-30  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**HEAD:** `d712802`  
**Prior audit:** `2026-06-30_step9_semantic_alignment_audit.md`  
**Scope:** Audit-only owner decision tables — no implementation  
**Status:** **OWNER_DECISIONS_REQUIRED_BEFORE_MATERIALIZATION**

---

## 1. Status / verdict

**Verdict:** `OWNER_DECISIONS_REQUIRED_BEFORE_MATERIALIZATION`

Plan draft `id=2` / order `88002` is semantically anchored on frozen `task_rules`. Gaps are classifiable and require owner choices before POST materialize GO. Step 9B UI read-only is **safe with gap badges** (`SAFE_FOR_UI_READONLY_ONLY`).

**Not:** `SAFE_FOR_MATERIALIZATION_GO` — duplicate lateral ops + missing workcenter/minutes sources block confident materialization.

---

## 2. Scope

**What I did:** Git preflight; read semantic audit worklog; DB read (`dev.db`) for order `88002`, plan `2`; built owner decision tables (operations, workcenter, minutes, dependencies, duplicates); central DEC-001..DEC-009 table.

**What I did not do:** implementation, backend/UI changes, POST materialize, execution_tasks, sessions, Employee Mobile, pricing paths, migration, seed, docs sync mare, commit, push.

---

## 3. Preflight

| Item | Value |
|------|-------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `d712802` |
| Git tracked code | clean |
| Untracked | worklogs including this file + prior semantic audit |

---

## 4. Gap review — operations without planned task

| Operation code | Source path in snapshot / plan | Product / module / component | Why no planned task? | Should become operational task? | If no, why? | Required owner decision | Risk if ignored |
|----------------|-------------------------------|------------------------------|----------------------|--------------------------------|-------------|-------------------------|-----------------|
| `svg_geometry_analysis` | `snapshot_v2_json` → `product_aggregate_snapshot.operations[]`; in `planned_operations[]` only; **no** `task_rules` entry | Parent `TPL-VOLUMETRIC-LETTERS_v2`; `comp_face_litere`; `priced=false`; formula `svg_geometry_readiness_gate` | Task graph driven by `task_contract.task_rules`, not all aggregate ops. No task_rule maps to this op. Overlaps READINESS_GATE (`vector_file_verification`) semantically. | **no** (default) / **later** if owner wants explicit PREPRESS analytics task | Analytics / readiness support op — not in dossier task_rules as operational step | **DEC-001:** classify as non-operational analytics vs fold into READINESS_GATE vs add task_rule | Operators may expect PREPRESS step; aggregate shows op without execution task |
| `premount_bar_preparation` | `operations[]`; provenance `linked_module`; `TPL-METAL-PREMOUNT-STRUCTURE_v1`; `comp_premount_bars`; `priced=false` | Linked module `structura_suport`; separate template product per dossier notes | No matching `task_rule`; unpriced module op — cost/BOM only in aggregate | **later** / **no** for this job if premount not selected | Module cost path without execution contract row | **DEC-002:** task_rule when premount enabled vs stay BOM-only | Missing shop step if premount jobs need metal fab task |
| `RETURN_PROFILE_MACHINE_FORMING` | `operations[]`; `linked_module`; `TPL-VOLUM-ALUMINIU_v1`; `WC_FORMING`; `priced=true` | Duplicate lateral of parent `side_forming` (task `return_profile_forming` uses parent code) | task_rules reference **parent** `priced_operation=side_forming`, not module code | **no** — duplicate | Same semantic step as planned task #4; module row is lateral aggregate expansion (`02` NEEDS_OWNER_DECISION) | **DEC-003:** canonical code + exclude module row from materialization | **Double execution** if both materialized |
| `RETURN_PROFILE_FACE_BONDING` | Same pattern; `WC_ASSEMBLY`; maps to parent `return_face_bonding` | Duplicate of planned task #5 | task_rules use parent `return_face_bonding` | **no** — duplicate | Module lateral duplicate | **DEC-003** (pair with forming) | Double bonding tasks |
| `PAINTING` (module) | Same pattern; `WC_PAINT`; maps to parent `painting` | Duplicate of planned task #6 | task_rules use parent `painting` (lowercase) | **no** — duplicate | Module lateral duplicate | **DEC-004:** canonical paint op code | Double paint tasks / wrong WC if alias wrong |

---

## 5. Workcenter review (12 planned tasks)

| planned_task_key | title | current workcenter | recommended workcenter | confidence | source evidence | owner decision needed |
|------------------|-------|-------------------|------------------------|------------|-----------------|----------------------|
| vector_prep | Vector Prep | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent op `vector_prep`: WC null in aggregate + PD roles | **DEC-005** |
| vector_prep | (suggestion only) | — | PREPRESS | low | orphan op `svg_geometry_analysis` uses PREPRESS; not linked in task_rule | suggestion only |
| cnc_face_cut | Cnc Face Cut | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent op WC null | **DEC-005** |
| cnc_face_cut | (suggestion only) | — | WC_CNC | medium | dossier mini_module `debitare_fata`; test fixtures use WC_CNC — **not in frozen snapshot** | suggestion only |
| cnc_back_cut | Cnc Back Cut | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent op WC null | **DEC-005** |
| cnc_back_cut | (suggestion only) | — | WC_CNC | medium | mini_module `debitare_spate`; fixtures | suggestion only |
| return_profile_forming | Return Profile Forming | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent `side_forming` WC null | **DEC-003 + DEC-005** |
| return_profile_forming | (suggestion only) | — | WC_FORMING | medium | module duplicate `RETURN_PROFILE_MACHINE_FORMING` has WC_FORMING — **different operation_code** | suggestion only |
| return_face_bonding | Return Face Bonding | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-003 + DEC-005** |
| return_face_bonding | (suggestion only) | — | WC_ASSEMBLY | medium | module `RETURN_PROFILE_FACE_BONDING` | suggestion only |
| painting | Painting | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-004 + DEC-005** |
| painting | (suggestion only) | — | WC_PAINT | medium | module `PAINTING` | suggestion only |
| vinyl_application | Vinyl Application | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-005** |
| led_installation | Led Installation | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-005** |
| electrical_wiring | Electrical Wiring | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-005** |
| electrical_wiring | (suggestion only) | — | WC_ELECTRICAL | medium | test fixtures only — **not in live snapshot** | suggestion only |
| mounting_template | Mounting Template | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null; conditional trigger | **DEC-005** |
| mounting_template | (suggestion only) | — | WC_CNC | low | same family as CNC ops | suggestion only |
| qc_internal_check | Qc Internal Check | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-005** |
| packaging | Packaging | **null** | SOURCE_MISSING_NEEDS_OWNER_DECISION | — | Parent WC null | **DEC-005** |

**Summary:** No authoritative workcenter in frozen snapshot for parent-priced ops. Module duplicates carry WC but are excluded from planned tasks by design of task_rules mapping.

---

## 6. Estimated minutes review (12 planned tasks)

| planned_task_key | estimated_minutes current | planning minutes source exists? | should remain null? | suggested source type | owner decision needed |
|------------------|---------------------------|--------------------------------|---------------------|----------------------|----------------------|
| all 12 tasks | **null** | **no** in snapshot/plan (`planning_minutes_source=null`; warning `PLANNING_MINUTES_SOURCE_REQUIRED`) | **yes until source policy chosen** — materialization audit allows null with warning | Capacity planning from: (A) dossier `time_assumptions_json` when populated; (B) internal cost snapshot non-commercial time hints; (C) workcenter capacity registry; (D) manual planner entry post-materialize — **none frozen at convert today** | **DEC-006** |

**Rule applied:** Minutes are **not** commercial price. They are capacity / scheduling / post-job comparison only. Step 9 preview intentionally does not read commercial/internal pricing snapshots for task generation.

---

## 7. Dependency review

| planned_task_key | current dependency | likely real dependency model | parallelizable? | risk | owner decision |
|------------------|-------------------|------------------------------|-----------------|------|----------------|
| vector_prep | none | after READINESS_GATE (excluded) / customer files | no (first op) | low | — |
| cnc_face_cut | vector_prep | needs approved vector / CAM | no | low | — |
| cnc_back_cut | cnc_face_cut | usually after face program; same machine queue | no | med if shop runs parallel machines | **DEC-007** |
| return_profile_forming | cnc_back_cut | needs cut blanks | no | med | — |
| return_face_bonding | return_profile_forming | needs formed return | no | low | — |
| painting | return_face_bonding | needs bonded assembly; skip if no paint finish | **unknown** — trigger says perimeter present not finish type | **high** — vinyl-only jobs may not need paint but chain forces paint before vinyl | **DEC-007** |
| vinyl_application | painting | should depend on **face finish** not paint step | **unknown** | **high** — wrong order for vinyl-only | **DEC-007** |
| led_installation | vinyl_application | needs enclosed letter body | partial — may parallel paint in some builds | med | **DEC-007** |
| electrical_wiring | led_installation | after LED modules placed | no | low | — |
| mounting_template | electrical_wiring | likely **independent branch** — template CNC from separate stock / early vector | **yes** — likely parallel with letter CNC early | **high** — current chain puts template after electrical | **DEC-007** |
| qc_internal_check | mounting_template | should depend on **all production branches complete** | no | med | **DEC-007** |
| packaging | qc_internal_check | after QC | no | low | — |

**Linear chain issue:** `_build_dependencies` in preview service creates **immediate-predecessor-only** chain — documented simplification, not shop DAG.

---

## 8. Duplicate lateral / return profile decision

### Questions

1. **Same thing?** Semantically **yes** for shop intent — parent `side_forming` task and module `RETURN_PROFILE_MACHINE_FORMING` describe return profile forming on the same volumetric letter job.
2. **Parent vs module?** **Parent task_rule + parent priced_operation** drive execution plan. **Module rows** are aggregate/BOM expansion from `TPL-VOLUM-ALUMINIU_v1` linked module (`04` duplicate lateral — `NEEDS_OWNER_DECISION`).
3. **Canonical code for execution:** Recommend **parent codes** already in task_rules: `side_forming`, `return_face_bonding`, `painting` (lowercase parent ops) — **owner must confirm**.
4. **Alias mapping:** Module codes `RETURN_PROFILE_*` and `PAINTING` should be **aggregate-only aliases** for costing/provenance — **not** separate operational tasks unless owner rejects parent canonical.
5. **Exclude from materialization:** **Yes** — exclude module duplicate ops from ever becoming operational tasks while parent tasks exist.
6. **Risk if both materialized:** Duplicate shop tasks, double time booking, wrong profitability, operator confusion, conflicting WC (null parent vs WC_FORMING module).

---

## 9. Owner decision table (central)

| Decision ID | Topic | Options | Recommended option | Reason | Blocks materialization? |
|-------------|-------|---------|-------------------|--------|-------------------------|
| DEC-001 | `svg_geometry_analysis` | A) non-operational analytics; B) merge into READINESS; C) new task_rule | **A** — non-operational analytics | `priced=false`; readiness gate exists; not in task_rules | **no** if labeled non-operational |
| DEC-002 | `premount_bar_preparation` | A) BOM-only; B) conditional task_rule when premount module active | **A** for default job; **B** when premount selected | unpriced; no task_rule today | **yes** if premount jobs need fab task without rule |
| DEC-003 | RETURN duplicate / `side_forming` canonical | A) parent canonical; B) module canonical; C) both (reject) | **A** parent canonical; module = aggregate alias only | planned task already uses `side_forming`; avoids double exec | **yes** until decided |
| DEC-004 | `PAINTING` module duplicate | A) parent `painting` canonical; B) module `PAINTING`; C) both | **A** parent canonical | same as DEC-003 pattern | **yes** until decided |
| DEC-005 | workcenter source | A) enrich parent aggregate at compile; B) map from module alias WC; C) manual post-materialize; D) registry pass | **A + B** upstream fix before materialize | snapshot has null WC on parent ops | **yes** for assignment/scheduling quality |
| DEC-006 | estimated_minutes source | A) remain null (warn); B) dossier time_assumptions; C) capacity registry; D) planner entry only | **B or C** long-term; **A** short-term with warnings | no frozen source at convert | **no** for audit dry-run; **yes** for production scheduling GO |
| DEC-007 | dependency model | A) keep linear MVP; B) finish-aware DAG; C) parallel branches (template/premount) | **B** before production GO; **A** ok for draft audit | vinyl/paint/template ordering wrong | **yes** for realistic shop scheduling |
| DEC-008 | Step 9B UI read-only before gap fix | A) proceed with gap badges; B) wait for upstream fix | **A** proceed read-only | no writes; improves visibility | **no** |
| DEC-009 | POST materialize | A) remain blocked; B) GO after DEC-003/004/005/007 | **A** remain blocked | duplicates + WC + DAG gaps | **yes** — stays blocked |

---

## 10. Path options after owner review

| Path | When |
|------|------|
| **A** Materialization audit next (GET only) | Already done (`d712802`); can re-run after decisions — no POST |
| **B** UI read-only Step 9B | **Safe now** with orphan/duplicate badges |
| **C** Fix upstream ProductAggregate / task_contract | After DEC-003..007 — new snapshot chain job |
| **D** Stop until owner decision | **Current state** for POST materialize |

---

## 11. Forbidden path confirmation

| Path | Touched? |
|------|----------|
| execution_tasks / operational_tasks write | **No** |
| POST materialize | **No** |
| sessions / ExecutionActuals | **No** |
| Employee Mobile | **No** |
| UI | **No** |
| backend implementation | **No** |
| pricing recalculation / `/price` / CE / QO | **No** |
| migration / seed / push | **No** |

---

## 12. Tests / validation

No pytest run in this pass (audit-only tables). Prior semantic audit: 13 pytest passed.

---

## 13. Next recommended step

Owner fills DEC-001..DEC-009 (minimum **DEC-003, DEC-004, DEC-009** before POST materialize). Then either **Step 9B UI read-only** (DEC-008=A) or **upstream aggregate/task_contract fix** (path C).

---

## 14. Direction score

**Cat sunt in directia stabilita: 92/100%**

(-8 pending owner decisions on duplicates, WC source, dependency DAG)

---

## 15. Files changed

| File | Change |
|------|--------|
| `docs/worklog/realignment/2026-06-30_step9_semantic_gap_owner_review.md` | **NEW** |

**Commit:** none (owner GO required)
