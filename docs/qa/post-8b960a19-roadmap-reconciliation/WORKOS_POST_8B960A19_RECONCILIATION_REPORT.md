# WORKOS — Post-8b960a19 Roadmap Reconciliation & Upstream Materials Truth Decision Audit

**Stamp:** `PASS WITH WARNINGS`  
**Date:** 2026-08-01  
**Mode:** READ-ONLY audit + docs-only pack  
**Canonical repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

---

## 1. Mini decision

Autorized large read-only reconciliation after Capacity Batch series and tip `8b960a19`. No product implementation. Produce current-state matrices, DEC reconciliation, 22-material source trace, and one next Owner GO.

## 2–7. Repo gate

| Field | Value |
|-------|-------|
| Stamp | **PASS WITH WARNINGS** |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Local HEAD | `8b960a1955e72c64e36847d3b14a4df9c6142116` |
| Remote HEAD | `8b960a1955e72c64e36847d3b14a4df9c6142116` |
| Ahead/behind before | **0 / 0** |
| Dirty | Untracked prior QA packs + `_tmp` elsewhere; **no product dirty**; this pack created under `docs/qa/post-8b960a19-roadmap-reconciliation/` |
| Stash | `stash@{0}: wip-employee-unrelated` **intact** (not applied/popped) |
| Merge/rebase/amend in progress | **None** |

Tip message: `Show frozen technical materials in ops graph`.

## 8. Sources read

**Architecture (handoff mirrors — `project_sources/` absent in repo):**

- `docs/architecture/realignment/03_PRODUCT_DEFINITION_COMPILER.md`
- `docs/architecture/realignment/04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md` *(index/context)*
- `docs/architecture/realignment/08_PRICING_REGISTRY_SEPARATION.md`
- `docs/architecture/realignment/09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md`
- `docs/architecture/app-flows/05_PRODUCT_AGGREGATE_FLOW.md`
- `docs/architecture/app-flows/08_EXECUTION_PLAN_FLOW.md`
- `docs/architecture/app-flows/09_WORKCENTERS_MACHINES_EMPLOYEES_FLOW.md`
- Plus related realignment/app-flow index files under handoff tree

**In-repo:**

- `AGENTS.md` (if present) / Capacity Batch 15–20D QA packs
- `docs/qa/ops-graph-materials-honesty-audit/*`
- `docs/qa/ops-graph-frozen-technical-materials-read-surface/*`
- `docs/qa/ops-graph-topological-order-readability/*`
- `docs/qa/capacity-batch-20a1/owner-f6-fixture-decisions.md`
- `docs/worklog/realignment/2026-06-30_step9_semantic_gap_owner_review.md` (+ Step9B/roadmap drift notes)
- Code: `backend/services/dec009_materialize_gate.py`, frozen materials projection, ops-graph UI

**Not copied into repo:** Desktop `project_sources/` attachments (missing locally; handoff architecture used).

## 9. Commit range audited (Capacity → tip)

Representative accepted chain inspected (not exhaustive dump):

`… capacity batches …` → `5c83d33a` DEC-009 gate → `9be947f4` ops-graph → Batch 17/18 clarity → `1454343b` scoped-B MAT-02 stamp → `89e021c7` topo order → `7b23b209` materials honesty audit → **`8b960a19` frozen materials RO**.

Old Step9 fixture baseline (`88002` / plan `2` / 12 tasks) treated as **historical**, not current.

## 10. Current architecture readback

```text
Intake / Product Truth
  → ProductDefinition (activation, material_roles, geometry)
  → ProductAggregate (materials[], operations[], task_contract)
  → Quote Snapshot V2 → Order Snapshot V2 (frozen)
  → ExecutionPlan draft → operational_tasks envelope (materialized for 92401)
  → Ops-graph RO (+ frozen_technical_materials attach from snapshot)
```

Boundaries held: Pricing registry separate; Inventory not product BOM; Analyzer/SVG parse not in this track; frontend must not invent business qty; FREEZE change only via new DEV version.

## 11. Roadmap drift

| Old claim (≈2026-06-30) | Current truth |
|-------------------------|---------------|
| 12 planned tasks / 17 ops / plan 2 / 88002 | **92401 / plan 13 / 18 ops** |
| Step 9B UI NOT_STARTED (app-flow) | **Ops-graph RO + materials RO implemented** |
| operational_tasks empty until materialize | **18 ops already in envelope** |
| DEC-003/004 block all materialize | Painting closed; RETURN siblings still residual; MAT-02 already wrote once |
| Materials invisible | **22 frozen technical materials visible** |
| Roadmap as live status | Must be reconciled; **runtime wins** |

## 12–13. Runtime 92401

| Metric | Value | Verified |
|--------|-------|----------|
| order | 92401 | YES |
| plan | 13 | YES |
| operational tasks | 18 | YES |
| frozen technical materials | 22 | YES |
| quantity null | 22 | YES |
| false zero | 0 | YES |
| material_inputs nonempty | 0 / 18 | YES |
| material_readiness_inputs persisted | **not present** | YES |
| sessions | 0 | YES |
| actuals/reality for 92401 | 0 | YES |
| authorize | false | YES |
| DEC-009 live | A / further POST blocked | YES |
| audit status | `already_materialized_in_envelope` | YES |
| MAT-02 | Historical scoped fixture binding; further materialize blocked | YES |
| topo note + original SEQ gaps | Present | YES |
| ORACAL/VOPSEA/ACM duplicate codes | Present with distinct provenance | YES |
| prices on materials table | Absent | YES |
| stock/reservation/consumption claims | Absent (honesty note present) | YES |

URL: `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`

## 14. DEC-001…009 status

See `OWNER_DECISION_STATUS_MATRIX.md`.

**Closed enough for stage:** 001 (fixture), 004, 008, 006-as-accepted-null, 009-further-blocked.  
**Open:** 003 production siblings, 005 envelope WC, 006 prod minutes, 007 prod DAG, 009 new execute, materials qty/ownership (cross-cutting).

## 15–19. Materials verdicts

| Topic | Verdict |
|-------|---------|
| Source trace | Complete for 22; PD has +2 inactive premount roles |
| Component ownership | Mostly COMPONENT_OWNED; composition emits linked_module rows; two UNKNOWN without formula |
| Quantity source | Prefer Model A (component formula→freeze); variants need Owner active filter; Model E rejected; Model D for formula-less sets |
| Duplicates | Provenance/variant parallel emissions — **not** accidental identical rows; do not auto-merge |
| Material→operation | **Insufficient contract** — empty inputs, name similarity only |

## 20–22. Boundaries

| Boundary | Verdict |
|----------|---------|
| Inventory | Must not source technical need; availability later |
| Procurement | Not ready — no owned qty |
| Pricing | Separate; not technical truth |

## 23–25. Next build

See `NEXT_BUILD_OPTIONS_AND_RECOMMENDATION.md`.

**Recommended:**

```text
OWNER GO — Upstream Material Quantity & Ownership Contract
```

**Why not others:** Planning hints / procurement / inventory / material→op / rematerialize either lack truth or invent semantics.

## 26–28. Files / product / runtime checks

**Created (this pack):**

```text
docs/qa/post-8b960a19-roadmap-reconciliation/
  WORKOS_POST_8B960A19_RECONCILIATION_REPORT.md
  WORKOS_POST_8B960A19_RECONCILIATION_WORKLOG.md
  CURRENT_STATE_RECONCILIATION_MATRIX.md
  OWNER_DECISION_STATUS_MATRIX.md
  FROZEN_MATERIAL_SOURCE_TRACE_MATRIX.md
  NEXT_BUILD_OPTIONS_AND_RECOMMENDATION.md
  screenshots/ops-graph-92401-current-full-page.png
  screenshots/ops-graph-92401-materials-expanded.png
```

**Product files changed:** **none**

**Runtime checks:** GET plan + materialization-audit + SQLite read-only + browser RO UI. **No POST mutating.**

## 29–30. Tests

| Ran | Not run |
|-----|---------|
| Live GET/API/DB/UI verification for 92401 | Full pytest / test:ci suite |
| CDP count Nespecificată=22 | Product unit suites for this docs pack |

## 31. Screenshots

- `screenshots/ops-graph-92401-current-full-page.png`
- `screenshots/ops-graph-92401-materials-expanded.png`

Honesty copy confirmed: *Materiale tehnice conform comenzii* / *Nu reprezintă stoc, rezervare sau consum.*

## 32. No-side-effect proof

- Authorize remains false  
- No envelope rewrite  
- No snapshot mutation  
- No stash touch  
- No push (until Owner evaluates)  
- Docs-only commit path only

## 33. Dead pieces (classify, do not delete)

| Piece | Class |
|-------|-------|
| Frozen snapshot materials path | ACTIVE_CORRECT |
| Ops-graph frozen materials RO | ACTIVE_CORRECT |
| Empty material_inputs treated as unknown | ACTIVE_CORRECT |
| Inventory as BOM qty | ACTIVE_MISLEADING if used |
| Pricing lookup as technical qty | ACTIVE_MISLEADING if used |
| Null→zero normalizer on this surface | Not observed (good) |
| Live inventory lookup on ops materials | Not used (good) |
| V3 op/material catalogs (legacy naming) | UNKNOWN_NEEDS_EVIDENCE / legacy parallel elsewhere |
| Linear-only dependency builder claims as current sole model | LEGACY_STILL_CALLED conceptually; deps exist but chain-like |
| WC invent fallbacks | Rejected by policy (null honesty) |
| Docs declaring 12 tasks/17 ops as *current* | ACTIVE_MISLEADING (drift) |
| App-flow “Step 9B NOT_STARTED” | ACTIVE_MISLEADING (drift) |
| material_readiness_inputs persist path | DEAD_CANDIDATE / unused for 92401 |
| Abandoned UI contracts pre-ops-graph | UNKNOWN_NEEDS_EVIDENCE |

## 34–35. Blockers / warnings

**Blockers for planning/procurement/materialize-next:** quantity ownership unresolved; active finish/depth variants co-emitted; material→op absent; DEC-009 authorize false.

**Warnings:** architecture app-flow lag; RETURN sibling ops still in envelope; PA WC not on envelope; untracked prior QA packs remain in working tree (untouched).

## 36–38. Commit / push

| Field | Expected after docs commit |
|-------|----------------------------|
| Docs-only commit message | `Reconcile post-capacity roadmap and material truth` |
| Docs-only commit SHA | local tip after pack (report final section / `git rev-parse --short HEAD`) |
| Ahead/behind after | **1 / 0** |
| Push | **not pushed** |

## 39. Next exact Owner GO

```text
OWNER GO — Upstream Material Quantity & Ownership Contract
```

## 40. Direction score

**97/100%** — tip materials honesty landed; next coherent step is upstream ownership/qty, not inventory/procurement/materialize.

---

## Final decision requirement checklist

1. Current state demonstrated — **YES**  
2. Decisions really closed — **YES** (see matrix)  
3. Decisions really open — **YES**  
4. Docs behind — **YES** (Step9 / app-flow 12/17 / Step9B NOT_STARTED)  
5. Material truth owners — **YES**  
6. Quantity source recommendation — **YES** (A/B/C/D by family; E rejected)  
7. Duplicate classification — **YES**  
8. Material→op readiness — **NO contract**  
9. Why not inventory — availability ≠ need  
10–12. Next build + frontier + outs — **YES**  
13. Single Owner GO — **YES**
