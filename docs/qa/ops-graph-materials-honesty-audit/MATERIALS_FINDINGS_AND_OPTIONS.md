# Materials Findings and Options — Ops-Graph Honesty Audit

**Date:** 2026-08-01  
**Decision state:** **IMPLEMENTATION_RECOMMENDED** (docs-only now; product changes need separate Owner GO)

---

## Finding MH-01 — Frozen technical materials not projected to ops-graph

| Field | Value |
|-------|-------|
| Severity | **HIGH** |
| Current behavior | Order snapshot has 22 `product_aggregate_snapshot.materials`; plan envelope has empty `material_inputs[]` on all 18 ops; persist omits `material_readiness_inputs`; UI has no materials section |
| Evidence | SQLite plan 13 envelope keys; GET plan tasks; DOM headers; `_tmp_snapshot_materials.json` |
| Source path | `orders.snapshot_v2_json.product_aggregate_snapshot.materials` → *(gap)* → `execution_plan.tasks_json` → GET `/execution/plan` → `MaterializedOpsGraph` |
| Operator risk | Operator cannot see technical material requirements on the ops surface; may assume none exist |
| Boundary affected | ProductAggregate / Order snapshot → ExecutionPlan read model → Ops-graph RO |
| Option A | Display-only plan-level section: “Cerințe tehnice înghețate (Order snapshot)” — code, label, unit, qty=Nespecificat when null; no stock/reservation/consumption claims |
| Option B | Persist `material_readiness_inputs` in envelope from preview (`build_tasks_json_envelope`) then render same honest labels |
| Option C | Keep ops-graph task-only; materials remain on Product System / Inventory surfaces with explicit cross-link |
| Recommended | **A** first (smallest operator value); B if Owner wants envelope self-contained |
| Why | Frozen truth already exists; ops-graph currently silent; A avoids new materialize writes |
| Files likely affected | `MaterializedOpsGraph.tsx`, `frontend/src/api/execution.ts`, possibly GET plan assembler or a dedicated frozen-materials read endpoint |
| Tests required | UI unit: renders Nespecificat not 0; no inventory verbs; fixture-agnostic |
| UI proof required | YES — before/after screenshots on 92401 |
| Migration required | NO |
| DB write required | NO *(for A)* |
| Owner GO required | **YES** |

---

## Finding MH-02 — Empty `material_inputs` must not become “zero materials”

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Current behavior | Parser sets `material_inputs: planned.get("material_inputs") or []`; preview never fills task-level inputs |
| Evidence | `execution_plan_task_parser.py`; preview grep no `material_inputs` assignment; 18× `[]` |
| Source path | PlannedTaskPreview.material_inputs → operational_tasks |
| Operator risk | Future UI binding `length===0` → “0 materials” would falsify |
| Boundary affected | ExecutionPlan task projection |
| Option A | Treat empty as UNKNOWN / “neproiectat pe task” |
| Option B | Populate task-level inputs from aggregate mapping (larger Product/Execution Owner work) |
| Recommended | **A** until B has Owner GO |
| Why | Missing projection ≠ proven absence |
| Files likely affected | read clarity + UI empty-state copy |
| Tests required | empty ≠ “0 needed” |
| UI proof required | YES if exposed |
| Migration required | NO |
| DB write required | NO for A |
| Owner GO required | **YES** |

---

## Finding MH-03 — Snapshot material quantities are null; status `present` ≠ stock

| Field | Value |
|-------|-------|
| Severity | **HIGH** *(if displayed without honesty)* / **MEDIUM** *(latent while hidden)* |
| Current behavior | 22/22 quantities null; status=`present`; units present |
| Evidence | snapshot materials dump |
| Source path | ProductAggregate materials freeze |
| Operator risk | Showing `0` or “disponibil” would be false |
| Boundary affected | ProductAggregate / Inventory |
| Option A | Display qty as **Nespecificat / Cantitate neînregistrată** |
| Option B | Upstream Product Truth fills quantities (separate track) |
| Recommended | **A** for any ops-graph surface; B remains Product Owner |
| Why | Sessions/actuals=0; no inventory actuals |
| Migration required | NO |
| DB write required | NO |
| Owner GO required | **YES** (for display rules) |

---

## Finding MH-04 — Duplicate material codes across provenance

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Current behavior | Codes repeated: MAT-ORACAL-651, MAT-VOPSEA-RAL, MAT-ACM-BOND-PANEL (and lateral size variants) |
| Evidence | snapshot materials list |
| Source path | parent vs linked_module rollup |
| Operator risk | Naive distinct-count or sum by code double-counts |
| Boundary affected | ProductAggregate dedupe / display aggregation |
| Option A | Show one row per (code, component_ref, provenance) |
| Option B | Owner-defined active-variant filter before display |
| Recommended | **A** |
| Why | Audit rule F — do not auto-merge |
| Owner GO required | **YES** |

---

## Finding MH-05 — Lateral profile size variants may be alternatives

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** — OWNER_DECISION_REQUIRED |
| Current behavior | MAT-PROFIL-LATERAL-LITERE plus 30/60/80/100MM variants all present |
| Evidence | snapshot codes |
| Operator risk | Showing all as required overstates BOM |
| Option A | Show all as “candidate technical roles — active variant unknown on ops-graph” |
| Option B | Resolve active variant from ProductDefinition/Product Truth before display |
| Recommended | **A** short-term; **B** correct long-term |
| Owner GO required | **YES** |

---

## Finding MH-06 — Task `quantity: 1.0` hardcoded (latent false zero/qty)

| Field | Value |
|-------|-------|
| Severity | **LOW** *(latent; not rendered today)* |
| Current behavior | Materialize parser sets `"quantity": 1.0` for every op |
| Evidence | `execution_plan_task_parser.py` |
| Operator risk | If UI ever shows “Cantitate” without role, looks like material qty |
| Recommended | Keep off materials UI; if shown, label “Plan task count” |
| Owner GO required | YES only if exposing field |

---

## Finding MH-07 — “Materialize” wording vs physical materials

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Current behavior | Banners/status use materialize/materialized heavily; Materiale=0 |
| Evidence | DOM scan |
| Recommended | Optional restrained glossary line |
| Classification | LABEL_ONLY_FIX |
| Owner GO required | YES for copy change |

---

## Finding MH-08 — No false consumption / reservation / price-as-ops (current UI)

| Field | Value |
|-------|-------|
| Severity | n/a — **CORRECT** |
| Current behavior | No Consum/Rezerv/Stoc/Preț/Cost materials claims; reality materials []; pricing ignored for tasks |
| Evidence | DOM + API + envelope `ignored_pricing_sources` |
| Recommended | Preserve in any future materials surface |

---

## Coherent recommended build (single Owner GO)

```text
OWNER GO — Ops-Graph Frozen Technical Materials Read Surface
```

**In scope**
- Read-only section on ops-graph (or plan GET projection) for frozen Order snapshot materials
- Labels: Cerințe tehnice înghețate / Cantitate neînregistrată when null
- Preserve topo order + original SEQ; no authorize/materialize/execute
- No inventory wiring; no Pricing Registry; no task.quantity as BOM

**Out of scope**
- DEC-009 reopen; sessions/actuals; Employee Mobile; HR; SVG/DWG; Step 12 cleanup
- Abstract charter without this evidence (not needed — findings above are the charter)

**Acceptance**
- 92401 still 18 ops, sessions 0, actuals 0, authorize false
- Materials section does not show 0 for null qty
- No reserved/consumed/in-stock wording
- Duplicates not silently merged
