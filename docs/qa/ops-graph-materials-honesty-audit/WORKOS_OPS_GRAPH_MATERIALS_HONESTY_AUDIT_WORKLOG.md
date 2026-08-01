# WorkOS Ops-Graph Materials Honesty Audit — Worklog

**Date:** 2026-08-01  
**Repo:** `C:\w\psiso`  
**Status:** COMPLETE (docs-only)  
**Scope:** AUDIT READ-ONLY + DOCUMENTATION EVIDENCE ONLY  
**Mini decision:** Establish materials source/semantics for ops-graph 92401 without product mutation.

---

## Architecture readback (confirmed before UI audit)

1. ProductDefinition compiles concrete technical product from Intake + Template.  
2. ProductDefinition activates dependencies/modules; does not decide price.  
3. Product Template composes possibilities; component-owned truth stays on component / Component Template / Product Truth path.  
4. ProductAggregate is technical read model (components, materials, operations, provenance, task contract).  
5. Order snapshot freezes accepted technical truth.  
6. ExecutionPlan consumes frozen order truth; must not re-read live Intake as truth.  
7. Ops-graph must not reprice; must not use Pricing Registry as product structure source.  
8. Pricing Registry owns rates/acquisition/commercial rules — not technical structure.  
9. Technical/planned material ≠ stock / reserved / allocated / prepared / issued / consumed / commercial client cost.  
10. Actual consumption only via inventory/execution actuals authorized.  
11. sessions=0 and actuals=0 ⇒ UI must not claim real operational consumption for 92401.  
12. HR/Pontaj / employee rates out of this analysis.  
13. Machines/capacity ≠ commercial tariff.  
14. Accepted topo display order + original SEQ out of modification scope.  
15. Employee Mobile final-final — out of scope.

---

## Repo state before

| Check | Result |
|-------|--------|
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD | `89e021c7` |
| Remote ahead/behind | **0/0** |
| Stash | `stash@{0}: wip-employee-unrelated` present, untouched |
| Dirty | known untracked capacity packs + `_tmp` / `_before` only |
| Accepted commit files | topo-order frontend + QA pack only — no foreign files |

## Source files read

| Source | Location used |
|--------|----------------|
| `project_sources/*` (named pack) | **Missing in repo** — WARNING |
| ProductDefinition compiler | handoff `psiso-worktree/.../03_PRODUCT_DEFINITION_COMPILER.md` |
| ProductAggregate flow | `.../app-flows/05_PRODUCT_AGGREGATE_FLOW.md` |
| Execution task graph | `.../10_EXECUTION_PLAN_TASK_GRAPH.md` |
| Execution plan flow | `.../app-flows/08_EXECUTION_PLAN_FLOW.md` |
| Pricing Registry separation | `.../08_PRICING_REGISTRY_SEPARATION.md` |
| HR boundary | `.../12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md` |
| Machines boundary | `.../14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md` |
| Governance | `.../18_GOVERNANCE_SETTINGS_POLICY.md` |
| Implementation route | `.../21_WORKOS_IMPLEMENTATION_ROUTE.md` |

Historical fixture numbers in those docs (88002 / plan 2 / 12 tasks) were **not** used to override accepted 92401 runtime.

## Code paths inspected

- Route: `App.tsx` → `/execution/ops-graph` → `MaterializedOpsGraph.tsx`
- API client: `frontend/src/api/execution.ts` (`getExecutionPlan`, materialization audit, reality)
- Backend GET plan: `routers/execution.py` + `execution_plan_task_parser.py`
- Preview materials readiness: `execution_plan_v2_preview_service._build_material_readiness`
- Persist envelope: `execution_plan_v2_persist_service.build_tasks_json_envelope` (**omits** `material_readiness_inputs`)
- Schemas: `schemas/execution_plan_v2.py` (`material_inputs`, `material_readiness_inputs`)
- Read clarity: `execution_ops_graph_read_clarity.py` (quantity classification; no materials column)
- Reality materials: `execution_reality_service` / GET materials
- DEC-009 gate: `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False`

## Runtime evidence

- GET plan 92401: plan id **13**, tasks **18**, SEQ multiset with gaps, all `material_inputs=[]`
- Audit: `already_materialized_in_envelope`, ops envelope 18, guards no sessions/writes/price
- Reality: 404; reality materials `total_count=0`
- UI: Materiale=0; columns without Materials; topo note present; SEQ 1..10,13,14,24..29
- Snapshot PA materials: **22**, qty all null, status present

## DB no-side-effect proof

| Indicator | Before | After |
|-----------|--------|-------|
| execution_plan id=13 | 1 | 1 |
| operational_tasks | 18 | 18 |
| execution_reality order 92401 | 0 | 0 |
| session tables | none | none |
| authorize | false | false |
| Inventory reservation/allocation/consumption tables for 92401 | **NOT VERIFIED** (no safe 92401-scoped reservation tables identified; `inventory_materials` global count=68 left unread for mutation) | same |

## Screenshots

- `screenshots/current-92401-full-page.png`
- `screenshots/current-92401-materials-detail.png`
- `screenshots/current-92401-seq-and-order-proof.png`
- `screenshots/MATERIALS_ABSENCE_PROOF.txt`

## Files created (docs pack)

- REPORT / WORKLOG / MATRIX / FINDINGS  
- screenshots/*  

## Tests

| Layer | Result |
|-------|--------|
| Static inspection | DONE |
| Targeted vitest `opsGraphDisplayOrder` + `MaterializedOpsGraph` | **9 passed** |
| Broader suite | **NOT RUN** (audit-only; avoid heavy unrelated) |
| Runtime verification | DONE |
| DB no-side-effect | DONE (available indicators) |

## Forbidden paths confirmation

No authorize · materialize · execute · POST lifecycle · sessions/actuals writes · inventory mutation · migrations · pricing `/price` · HR · Mobile · SVG/DWG · SEQ/topo changes · product commits · push · stash apply/drop · untracked cleanup.

## Blockers

None for audit completion.

## Warnings

1. `project_sources/` missing in repo — used handoff architecture mirrors  
2. Agent browser session gate flaky on fresh tab; authenticated tab used for screenshots  
3. materials-detail screenshot shares viewport with full-page (absence is also in DOM proof txt)  
4. Inventory reservation tables not fully enumerated → NOT VERIFIED  

## Owner decisions required

1. Should ops-graph show frozen technical materials at all?  
2. How to treat profile size variants (all vs active)?  
3. Empty `material_inputs` wording when/if exposed  

## Dead pieces check

| Piece | Class |
|-------|-------|
| `PlannedTaskMaterialInput` / task `material_inputs` always empty | LEGACY_STILL_CALLED *(schema+parser)* / ACTIVE_MISLEADING if treated as complete |
| Preview `material_readiness_inputs` not persisted in envelope | ACTIVE_MISLEADING *(summary count only)* |
| Ops-graph materials UI | DEAD_CANDIDATE *(never built)* |
| Reality materials POST path | ACTIVE_CORRECT but unused for 92401 |
| EUR/ml softened labels | ACTIVE_CORRECT with residual provenance |
| `quantity: 1.0` on ops tasks | ACTIVE_CORRECT as plan count; UNKNOWN_NEEDS_EVIDENCE if reused as BOM |

## Roadmap awareness checkpoint

Audit of truth/label/read-model only — not materialization. DEC-009 blocked. Does not close DEC-003/004/005/007. Upstream qty gaps → ProductAggregate/Product Truth owners. Inventory actuals future. Sessions/actuals frozen. Employee Mobile final-final. Pricing track separate. Step 12 cleanup not started. Topo+SEQ remain accepted.

## Next recommended Owner GO

```text
OWNER GO — Ops-Graph Frozen Technical Materials Read Surface
```

## Direction score

**96/100%** (honesty gap documented; runtime fixture intact)
