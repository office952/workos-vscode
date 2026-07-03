# Step 9 — Semantic Alignment Audit (ExecutionPlan V2 vs ProductSystem)

**Date:** 2026-06-30  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**HEAD:** `d712802` — `feat(step9): add read-only materialization audit`  
**Scope:** Audit-only — semantic bridge Order Snapshot V2 → ExecutionPlan draft `tasks_json`  
**Status:** **PARTIAL_ALIGNMENT_GAPS_FOUND**

---

## 1. Status

**PARTIAL_ALIGNMENT_GAPS_FOUND**

Plan draft `id=2` / order `88002` is a **correct frozen bridge** from `product_aggregate_snapshot.task_contract.task_rules` inside Order Snapshot V2. READINESS_GATE is excluded. No pricing recalculation. No forbidden imports on Step 9 path.

**Gaps:** 5 aggregate operations have no planned task; workcenter missing on all 12 planned tasks; duplicate lateral module operations (TPL-VOLUM-ALUMINIU) coexist with parent-priced ops; planning minutes null (`PLANNING_MINUTES_SOURCE_REQUIRED`); linear dependency chain may not match real parallelizable shop flow.

---

## 2. Scope

Audit-only semantic alignment for:

- order `88002`
- `quote_snapshot_v2_id=3`
- `execution_plan.id=2`
- `orders.snapshot_v2_json`
- `execution_plan.tasks_json`

**In scope:** docs read, DB read, code path read, targeted pytest.

**Out of scope:** implementation, new endpoints, UI, POST materialize, execution_tasks, sessions, Employee Mobile, docs sync mare, commit, push.

Repo: `C:\Users\offic\Desktop\workos-active` only.

---

## 3. What I did

### Git / preflight

| Item | Value |
|------|-------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `d712802` |
| Tracked code | clean (worklog untracked files pre-existing) |
| Doc lag | `20_ROADMAP` cites older HEAD `b12889c`; worklogs through `e9f8033` / materialization audit not fully synced in roadmap |

### Docs read

- `README.md`, `00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md`
- `02_PRODUCT_SYSTEM_TEMPLATE_CONTRACT.md`, `03_PRODUCT_DEFINITION_COMPILER.md`, `04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md`
- `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md`, `10_EXECUTION_PLAN_TASK_GRAPH.md`, `11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md`
- `20_ROADMAP_STEPS_7G_TO_12.md`
- Worklogs: Step 9 preview/persist/HTTP fresh/materialization audit

### DB inspection (dev.db)

| Entity | Value |
|--------|-------|
| Order | `88002` — `ORD-IV6-V2-1782815703-1` |
| `quote_snapshot_v2_id` | **3** |
| `snapshot_v2_json` | present (~66 KB) |
| Plan | `id=2`, `order_id=88002`, `source_quote_snapshot_v2_id=3`, `plan_source=order_snapshot_v2` |
| `tasks_json` | present (~14 KB) |
| `planned_tasks[]` | **12** |
| `planned_operations[]` | **17** |
| `operational_tasks[]` | **0** |
| `execution_tasks_created` | **false** |
| Duplicate plans for 88002 | **1** row |

### Code path confirmed

| Service | Source for tasks | Pricing? |
|---------|-------------------|----------|
| `execution_plan_v2_preview_service.py` | `OrderSnapshotV2.product_aggregate_snapshot.task_contract.task_rules` + `product_definition_snapshot.operation_roles` | **No** — ignores commercial/internal pricing snapshots |
| `execution_plan_v2_persist_service.py` | Persists preview envelope | **No** |
| `execution_plan_v2_materialization_audit_service.py` | Dry-run from frozen `planned_tasks[]` | **No** |

Provenance on all 12 tasks: `product_aggregate_snapshot.task_contract.task_rules`.

---

## 4. What I did not do

- POST `materialize-tasks`
- Create `operational_tasks[]`
- Sessions / ExecutionActuals / assignment / start-stop
- `/price`, CostEngine, QuoteOrchestrator
- UI changes
- DB migration / seed / reset
- Full backend pytest suite
- HTTP runtime call (DB + code sufficient for this audit)
- Commit / push

---

## 5. Semantic classification

### 5.1 Snapshot task rules (13 total)

| task_name | task_type | seq | priced_operation | Class | Materializable | Risk |
|-----------|-----------|-----|------------------|-------|----------------|------|
| vector_file_verification | READINESS_GATE | 0 | — | readiness/dossier | **no** | Low — correctly excluded from plan |
| vector_prep | file_preparation | 1 | vector_prep | operational_task_candidate | later | Med — no workcenter on task |
| cnc_face_cut | cnc_routing | 2 | face_cnc_cut | operational_task_candidate | later | Med |
| cnc_back_cut | cnc_routing | 3 | back_cut | operational_task_candidate | later | Med — trigger owner-dependent |
| return_profile_forming | edge_bending | 4 | side_forming | operational_task_candidate | later | Med — duplicates module op naming |
| return_face_bonding | volumetric_letter_assembly | 5 | return_face_bonding | operational_task_candidate | later | Med |
| painting | volumetric_letter_assembly | 6 | painting | operational_task_candidate | later | Med |
| vinyl_application | vinyl_cutting | 7 | vinyl_application | operational_task_candidate | later | Med |
| led_installation | led_assembly | 8 | led_install_letters | operational_task_candidate | later | Med |
| electrical_wiring | led_wiring | 9 | electrical_letters | operational_task_candidate | later | Med |
| mounting_template | cnc_routing | 10 | mounting_template_cnc_cut | operational_task_candidate | later | Med — conditional trigger |
| qc_internal_check | quality_control | 13 | qc_letters | operational_task_candidate | later | Low |
| packaging | packaging | 14 | packaging_letters | operational_task_candidate | later | Low |

**Evidence:** all rules frozen in `orders.snapshot_v2_json` → `product_aggregate_snapshot.task_contract.task_rules`.

### 5.2 Planned tasks in plan 2 (12 — matches rules minus READINESS_GATE)

All 12 rows in `execution_plan.tasks_json.planned_tasks[]` map 1:1 to non-READINESS rules above.

| Gap | Detail |
|-----|--------|
| `estimated_minutes` | **null** on all — warning `PLANNING_MINUTES_SOURCE_REQUIRED` |
| `machine_requirement.workcenter` | **null** on all — parent aggregate ops lack workcenter; module duplicates have WC but different operation_code |
| Dependencies | Linear chain (each task depends on immediate predecessor) — **unclear** if this matches real shop parallelism |

### 5.3 Aggregate operations (17) — orphan ops without planned task

| operation_code | workcenter | priced | source_template | Class | In planned task? | Risk |
|----------------|------------|--------|-----------------|-------|------------------|------|
| svg_geometry_analysis | PREPRESS | false | TPL-VOLUMETRIC-LETTERS_v2 | technical_operation / analytics | **no** | Med — prepress analysis not operationalized |
| vector_prep | — | true | parent | technical_operation | yes → vector_prep | OK |
| face_cnc_cut | — | true | parent | technical_operation | yes | OK |
| back_cut | — | true | parent | technical_operation | yes | OK |
| side_forming | — | true | parent | technical_operation | yes | OK |
| return_face_bonding | — | true | parent | technical_operation | yes | OK |
| led_install_letters | — | true | parent | technical_operation | yes | OK |
| electrical_letters | — | true | parent | technical_operation | yes | OK |
| painting | — | true | parent | technical_operation | yes | OK |
| vinyl_application | — | true | parent | technical_operation | yes | OK |
| packaging_letters | — | true | parent | technical_operation | yes | OK |
| mounting_template_cnc_cut | — | true | parent | technical_operation | yes | OK |
| qc_letters | — | true | parent | technical_operation | yes | OK |
| premount_bar_preparation | WC_METAL_FAB | false | TPL-METAL-PREMOUNT-STRUCTURE_v1 | module / technical_operation | **no** | Med — linked module op not in task_rules |
| RETURN_PROFILE_MACHINE_FORMING | WC_FORMING | true | TPL-VOLUM-ALUMINIU_v1 | module / duplicate lateral | **no** | **High** — doc `02` NEEDS_OWNER_DECISION |
| RETURN_PROFILE_FACE_BONDING | WC_ASSEMBLY | true | TPL-VOLUM-ALUMINIU_v1 | module / duplicate lateral | **no** | **High** |
| PAINTING | WC_PAINT | true | TPL-VOLUM-ALUMINIU_v1 | module / duplicate lateral | **no** | **High** |

**Interpretation:** Task graph is driven by **task_rules**, not full aggregate operations list. Orphan ops are expected for analytics/unpriced ops and **known duplicate lateral module rows** — not invented by Step 9, but semantic debt before materialization GO.

### 5.4 ProductDefinition alignment

- `product_definition_snapshot.operation_roles` mirrors aggregate operations (17 roles).
- Parent template ops: labels present, **workcenter mostly null**.
- Module ops: workcenters present on duplicates — **not wired** into planned tasks because task_rules reference parent `priced_operation` codes.

### 5.5 Dead / legacy / invented check

| Item | Verdict |
|------|---------|
| Task keys in plan | **Not invented** — from frozen snapshot task_rules |
| V3 catalog as driver | **Not used** on Step 9 V2 path (code + tests) |
| Dossier task_rules as runtime driver | **Partial** — frozen inside aggregate snapshot at convert, not live dossier read |
| CostEngine / QO / `/price` on Step 9 path | **Absent** (static import guard tests) |
| Commercial recalculation in plan | **None** |

---

## 6. Alignment question — answer

**Is `tasks_json` for plan 2 a correct bridge between Order Snapshot V2 and operational reality?**

**Partially yes.**

- **Yes:** Single source for planned tasks = frozen `product_aggregate_snapshot.task_contract.task_rules`; READINESS_GATE excluded; snapshot provenance intact; no pricing drift in Step 9 services.
- **No / gaps before materialization GO:** workcenter assignment missing; planning minutes missing; 5 operations in aggregate not represented as tasks (including known module duplicates); linear dependencies may oversimplify; orphan PREPRESS analytics op may need explicit non-operational classification in UI/docs.

**Verdict enum:** `PARTIAL_ALIGNMENT_GAPS_FOUND`

Not `BLOCKED_PRODUCTSYSTEM_DRIFT` — drift is documented and upstream in aggregate/snapshot, not introduced by persist.

Not `ALIGNED_FOR_MATERIALIZATION_AUDIT` — gaps above block confident materialization GO without owner review.

---

## 7. Step 10 status confirmation (repo-only)

| Slice | Git evidence | Worklog |
|-------|--------------|---------|
| 10.1 immutability guard | `90ba918` | untracked audit/plan worklogs |
| 10.1 batch PUT | `453932f` | untracked |
| 10.2+10.3 profitability GET | `45255a1` | untracked |
| 10.4 ExecutionDetail panel | `378b42b` | untracked |

**Step 10 overall:** **PARTIAL** — commits in repo; several worklogs not yet committed. Not re-validated by HTTP in this audit.

---

## 8. Tests

```powershell
cd backend
Remove-Item test_placeholder.db -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest tests/test_step9_materialization_audit.py tests/test_step9_order_snapshot_to_execution_plan.py -q
```

**Result:** **13 passed**

---

## 9. Forbidden path confirmation

| Path | Touched? |
|------|----------|
| POST materialize-tasks | **No** |
| operational_tasks write | **No** |
| sessions / ExecutionActuals | **No** |
| Employee Mobile | **No** |
| `/price` / CostEngine / QuoteOrchestrator | **No** |
| UI / navigation | **No** |
| migration / seed / reset DB | **No** |
| Step 12 cleanup | **No** |
| push | **No** |

---

## 10. Owner decisions needed

1. **Duplicate lateral module ops** (`RETURN_*`, `PAINTING` vs parent `side_forming` / `return_face_bonding` / `painting`) — which codes are canonical for execution?
2. **`premount_bar_preparation`** — should it become a task_rule or stay non-operational module cost only?
3. **`svg_geometry_analysis`** — explicit non-operational PREPRESS analytics vs future task?
4. **Planning minutes source** — where should `estimated_minutes` come from before materialization GO?
5. **Workcenter mapping** — populate from module ops, product_definition roles, or registry pass?

---

## 11. What remains

| Item | Status |
|------|--------|
| POST materialize on plan 2 | **NEEDS OWNER GO** |
| Step 9B UI read-only | optional, separate pass |
| Docs sync roadmap → `d712802` | optional — not done (no official truth change in this audit) |
| 7G / 7H / 7I runtime | **NOT STARTED** |
| Sessions / Employee Mobile | **final-final** |

---

## 12. Next recommended step

**Owner review of this audit** — decide on duplicate module ops + planning minutes + workcenter policy **before** any POST materialize GO or Step 9B UI.

Alternative without GO: **Step 9B read-only UI** showing planned_tasks + orphan ops + audit badge (still no materialize).

---

## 13. Direction score

**Cat sunt in directia stabilita: 93/100%**

(-7 for workcenter/planning minutes gaps, duplicate module lateral ops, orphan aggregate operations not classified in product contract UI)

**Roadmap alignment note:** Semantic bridge Step 9 is on-architecture; gaps are upstream ProductAggregate/snapshot completeness, not Step 9 persist bug.

---

## 14. Files changed

| File | Change |
|------|--------|
| `docs/worklog/realignment/2026-06-30_step9_semantic_alignment_audit.md` | **NEW** — this worklog |

**Commit:** none (audit-only; owner decides)
