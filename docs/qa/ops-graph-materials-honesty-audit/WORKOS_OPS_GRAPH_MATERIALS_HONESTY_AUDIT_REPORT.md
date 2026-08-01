# WorkOS Ops-Graph Materials Honesty Audit — Report

**Date:** 2026-08-01  
**Repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

No UI change was authorized.  
Current screenshots represent the audited accepted state, not an after-state.

---

## 1. Mini decision

Ops-graph does **not** currently display materials. Upstream frozen Order snapshot holds **22** technical materials (qty all null). Envelope task `material_inputs` are empty; `material_readiness_inputs` is not persisted. No false consumption/stock/price claims on the page. Product fix needs a separate Owner GO.

## 2. Stamp

**PASS WITH WARNINGS**

## 3. Branch / SHA before and after

| | SHA |
|--|-----|
| Before audit | `89e021c7` |
| After docs-only commit | tip of this docs-only commit (`Document ops graph materials honesty audit`) |

## 4. Remote ahead/behind before and after

| | ahead/behind |
|--|--------------|
| Before | **0/0** |
| After docs commit (expected) | **1/0** — not pushed |

## 5. Repo dirty state

Known untracked only: capacity-19..20b packs, integrity `_tmp`, operator-review `_tmp/_before`, topo `_tmp`/`_sha_tip`. Not staged. Not deleted.

## 6. Stash confirmation

`stash@{0}: wip-employee-unrelated` — present, not applied, not dropped. HR WIP not inspected.

## 7. Architecture readback

See worklog — all 15 ownership/boundary points confirmed. Historical doc fixtures (88002 / plan 2 / 12 tasks) did not override 92401 runtime.

## 8. Source files read

`project_sources/` **missing**. Used handoff mirrors: ProductDefinition compiler, ProductAggregate flow, ExecutionPlan task graph + flow, Pricing Registry separation, HR boundary, Machines boundary, Governance, Implementation route (see worklog paths).

## 9. Source-to-UI trace

```text
Order snapshot product_aggregate_snapshot.materials (22, qty null)
  → NOT persisted into plan envelope material_readiness_inputs
  → planned_tasks[].material_inputs never populated in preview
  → materialize parser copies material_inputs or []
  → GET /api/v1/execution/plan/92401 → tasks[] (18) with material_inputs=[]
  → MaterializedOpsGraph maps tasks to table columns
  → NO materials column / section rendered
Parallel: GET reality/materials → [] ; reality row 404
Pricing/EIC/CPP present on snapshot but listed in ignored_pricing_sources for tasks
```

## 10. Materials matrix summary

- UI materials claims: **none** (Materiale/Necesare/Consum/Rezerv/Stoc/Preț = 0)  
- Envelope task materials: **18 × empty**  
- Frozen technical materials: **22** upstream  
- Actual consumption: **none**  
- Full matrix: `MATERIALS_SOURCE_AND_SEMANTICS_MATRIX.md`

## 11. Findings by severity and classification

| ID | Severity | Classification |
|----|----------|----------------|
| MH-01 | HIGH | SOURCE_GAP / READ_MODEL_FIX |
| MH-02 | MEDIUM | SOURCE_GAP |
| MH-03 | HIGH/MEDIUM | UNKNOWN_QUANTITY / FALSE_ZERO risk if coerced |
| MH-04 | MEDIUM | DUPLICATION_RISK |
| MH-05 | MEDIUM | OWNER_DECISION_REQUIRED |
| MH-06 | LOW | FALSE_ZERO latent |
| MH-07 | LOW | AMBIGUOUS_LABEL / LABEL_ONLY_FIX |
| MH-08 | — | CORRECT (no false ops claims today) |

Details: `MATERIALS_FINDINGS_AND_OPTIONS.md`

## 12. Runtime truth for 92401

| Field | Value |
|-------|-------|
| order_id | 92401 |
| plan_id | 13 |
| order_code | ORD-IV6-V2-1784236805-1 |
| snapshot | QSN2-2026-0001 |
| template | TPL-VOLUMETRIC-LETTERS_v2 |
| fixture badge | `—` (MAT-01 hardcode only for 973010; MAT-02 represented by this order/plan, not hardcoded label) |
| authorize | false |

## 13. Operational task count proof

GET plan + UI metrics + envelope: **18**.

## 14. Topological order preservation proof

UI note: “Display order: dependency order · SEQ: original…”. Dependency strip present. No sorter code changed in this audit.

## 15. Original SEQ preservation proof

Displayed SEQ: `1,2,3,4,5,6,7,8,9,10,13,14,24,25,26,27,28,29` — gaps visible; not remapped 1..N.

## 16. Sessions / actuals / authorize proof

| Indicator | Value |
|-----------|-------|
| Sessions UI | 0 (audit.guards.creates_sessions=false) |
| Session tables | none found |
| Actuals UI | 0 (reality null) |
| Reality 92401 rows | 0 |
| Reality materials | [] |
| BATCH_EXECUTE_MATERIALIZE_AUTHORIZED | False |

## 17. DB no-side-effect proof

Plan 13 / ops 18 / reality 0 unchanged before→after audit. No POST lifecycle. Inventory reservation/allocation/consumption scoped to 92401: **NOT VERIFIED**.

## 18. Tests and validation

1. Static inspection — pass  
2. Targeted tests — 9/9 pass (`opsGraphDisplayOrder`, `MaterializedOpsGraph`)  
3. Broader validation — not run  
4. Runtime verification — pass  
5. DB no-side-effect — pass for available indicators  
6. Not run: full `test:ci` / pytest suite (audit-only scope)

## 19. Files created

```text
docs/qa/ops-graph-materials-honesty-audit/
  WORKOS_OPS_GRAPH_MATERIALS_HONESTY_AUDIT_REPORT.md
  WORKOS_OPS_GRAPH_MATERIALS_HONESTY_AUDIT_WORKLOG.md
  MATERIALS_SOURCE_AND_SEMANTICS_MATRIX.md
  MATERIALS_FINDINGS_AND_OPTIONS.md
  screenshots/*
```

## 20. Screenshot paths

- `screenshots/current-92401-full-page.png`  
- `screenshots/current-92401-materials-detail.png`  
- `screenshots/current-92401-seq-and-order-proof.png`  
- `screenshots/MATERIALS_ABSENCE_PROOF.txt`

## 21. Honest full-page UI verdict

Calm operator table; topo+SEQ clarity is good. Materials honesty problem is mostly **silence**: no false “consumed/reserved” claims, but also **no** frozen technical materials visibility despite 22 upstream rows. Process names mention Forex/RAL/LED/folie as craft context, not BOM. “Materialize” language is the main vocabulary collision. A materials section would add real operator value only if qty null stays Nespecificat and duplicates/variants are not over-claimed — otherwise cosmetic risk.

## 22. Boundaries verdict

**PASS** — read-only audit; no product mutation; Pricing not used for structure; no HR/Mobile/SVG; authorize false.

## 23. Dead pieces check

See worklog. Notable: readiness inputs computed in preview but dropped on persist; task `material_inputs` always empty.

## 24. Roadmap awareness checkpoint

Confirmed: audit ≠ materialization; DEC-009 blocked; DEC-003/004/005/007 not auto-resolved; upstream gaps to Product owners; inventory actuals future; sessions/actuals frozen; Mobile final-final; Pricing separate; Step 12 not started; topo+SEQ untouched.

## 25. Blockers

None.

## 26. Warnings

1. `project_sources/` missing in repo  
2. Inventory reservation tables NOT VERIFIED  
3. materials-detail screenshot overlaps full-page viewport (DOM proof compensates)  
4. Untracked local packs remain  

## 27. Decision

**IMPLEMENTATION_RECOMMENDED**

## 28. Next recommended Owner GO

```text
OWNER GO — Ops-Graph Frozen Technical Materials Read Surface
```

(Materials Honesty Charter as abstract doc: **not** created; findings pack is the concrete decision record.)

## 29. Commit SHA

Tip of this docs-only commit — verify with `git rev-parse --short HEAD` (message: Document ops graph materials honesty audit).

## 30. Exact ahead/behind after commit

**1/0** (local docs commit; not pushed)

## 31. Cât suntem în direcția stabilită: **96/100%**
