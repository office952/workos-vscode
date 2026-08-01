# Track D — Next Build Candidates (3 large coherent builds)

**Date:** 2026-08-01  
**Constraint:** After docs hygiene; still **no** authorize/materialize/execute unless separate Owner GO.

---

## Build 1 — Ops-Graph Topological Order Readability (RECOMMENDED)

| Field | Detail |
|-------|--------|
| **Objective** | Default operator view sorts by dependency/topological execution order; keep original `sequence_index`/SEQ visible; never remap SEQ to 1..N |
| **Value** | Directly addresses Owner visual warning on 92401; improves calm operator understanding without inventing truth |
| **Risk** | Medium — sort/display bugs could confuse operators; must not change envelope data |
| **Boundaries** | Frontend ops-graph / optional read_clarity display only · no Pricing · no HR · no materialize |
| **Expected files** | `frontend/src/pages/MaterializedOpsGraph.tsx` (+ helpers/tests) · maybe `execution_ops_graph_read_clarity` display hints if needed |
| **Tests/proof** | Vitest sort fixtures (incl. 973010 + generic) · screenshot `?orderId=92401` · CI lint/test:ci/build · prove SEQ column unchanged |
| **Before/after push** | Tip already pushed; do **docs QA commit first**, then this product GO on clean branch tip |

---

## Build 2 — Envelope Materials Honesty / Material Inputs Visibility

| Field | Detail |
|-------|--------|
| **Objective** | Surface real `material_inputs` / component material links when present; keep empty as honesty (no invent); align with cant-finish materials ownership (Pricing Registry vs PT) |
| **Value** | Closes empty-materials usability gap on 92401 without fake fills |
| **Risk** | Medium–high if it invents materials or pulls Pricing into Execution |
| **Boundaries** | ExecutionPlan read-model · Product Truth component path · Pricing Registry read-only display · no pontaj |
| **Expected files** | Backend plan enrichment (careful) · ops-graph columns · tests proving null stays null |
| **Tests/proof** | API fixture tests · UI RO · pricing/time boundary check |
| **Push timing** | After docs hygiene; product GO separate |

---

## Build 3 — Planning Minutes Source Closure (CAP-004 honesty → sourced minutes)

| Field | Detail |
|-------|--------|
| **Objective** | Close `PLANNING_MINUTES_SOURCE_REQUIRED` with real planning sources where Owner accepts; never invent 0; never feed Pricing from minutes |
| **Value** | Capacity/load usefulness; reduces accepted-risk nulls |
| **Risk** | High — easy to mix measured time/HR into commercial paths |
| **Boundaries** | Planning/capacity only · forbid Pricing/CostEngine consumption of pontaj · no Mobile execute |
| **Expected files** | Planning source services · materialize/read clarity · capacity tests |
| **Tests/proof** | Targeted pytest · boundary greps · no price fields on ops |
| **Push timing** | Only after explicit Owner charter; after docs hygiene |

---

## Ranking

1. **Build 1** (ordering UX) — best next product GO  
2. **Build 2** (materials honesty) — strong follow-on  
3. **Build 3** (planning minutes) — later, higher risk  

**Docs-first (non-build):** separate QA commit of integrity + exact-state + hygiene + multitask packs.
