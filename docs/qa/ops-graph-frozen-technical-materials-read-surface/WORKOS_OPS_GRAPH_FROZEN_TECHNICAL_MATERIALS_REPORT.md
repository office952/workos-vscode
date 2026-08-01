# WorkOS Ops-Graph Frozen Technical Materials Read Surface — Report

**Date:** 2026-08-01  
**Repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

---

## 1. Mini decision

Read-only order/plan-level section **Materiale tehnice conform comenzii** projects frozen Order snapshot materials (22 on 92401). Null qty → **Nespecificată**. No inventory/pricing/task mapping. No envelope mutation.

## 2. Stamp

**PASS WITH WARNINGS**

## 3. Branch / SHA before and after

| | |
|--|--|
| Before (audit tip) | `7b23b209` |
| After product commit | tip of this commit (`Show frozen technical materials in ops graph`) |

## 4–6. Push proof for audit commit

| | |
|--|--|
| Push | `89e021c7..7b23b209` |
| Remote SHA | `7b23b2097fd6ca34d8fb02dd810f00a7770ab207` |
| After audit push | **0/0** |

## 7. Ahead/behind after product commit

Expected **1/0** (not pushed).

## 8. Repo dirty state

Known untracked capacity/`_tmp` packs left untouched.

## 9. Stash confirmation

`stash@{0}: wip-employee-unrelated` — untouched.

## 10. Architecture readback

Confirmed in worklog (frozen ≠ inventory; null ≠ 0; no task mapping; DEC-009 blocked).

## 11–12. UI placement

**Variant B** selected (summary + expand). C rejected. Details in worklog.

## 13. Source-to-UI contract

See `SOURCE_TO_UI_CONTRACT.md`.

## 14. Files changed

| Path | Role |
|------|------|
| `backend/services/ops_graph_frozen_technical_materials.py` | Projection |
| `backend/routers/execution.py` | Attach on GET plan |
| `backend/tests/test_ops_graph_frozen_technical_materials.py` | Backend tests |
| `frontend/src/api/execution.ts` | Types |
| `frontend/src/components/workos/OpsGraphFrozenTechnicalMaterials.tsx` | UI |
| `frontend/src/components/workos/OpsGraphFrozenTechnicalMaterials.test.tsx` | UI tests |
| `frontend/src/pages/MaterializedOpsGraph.tsx` | Wire |
| `frontend/src/pages/MaterializedOpsGraph.test.tsx` | Page assertion |
| `frontend/scripts/ci-unit-tests.txt` | Allowlist |
| `docs/qa/ops-graph-frozen-technical-materials-read-surface/*` | QA pack |

## 15. Implementation summary

Allowlisted projection from `snapshot_v2_json.product_aggregate_snapshot.materials` → `frozen_technical_materials` on plan GET → collapsible RO section. Does not write DB / mutate tasks / fill material_inputs.

## 16–20. Proofs

| Proof | Result |
|-------|--------|
| 22 entries | API + UI |
| Null qty / no false zero | 22× Nespecificată; 0× zero |
| Duplicates preserved | ORACAL / VOPSEA / ACM appear multiple times |
| No price leakage | No price columns; commercial snapshots not projected |
| No inventory/consumption claims | Semantic note + absent verbs |
| Ops count | 18 |
| Topo order | note + dependency strip unchanged |
| SEQ | 1–10,13,14,24–29 |
| Sessions/actuals/authorize | 0 / 0 / false |
| DB side effects | ops 18; material_inputs empty; readiness absent; reality 0 |

## 26–27. Tests

| Layer | Result |
|-------|--------|
| Targeted backend | 7 projection tests + read_clarity regression = 18 passed |
| Frontend targeted | OpsGraphFrozenTechnicalMaterials + MaterializedOpsGraph + displayOrder |
| Frontend `test:ci` | **207 passed** (23 files) |
| Broader pytest suite | not run full |
| Runtime | pass |

## 28. Screenshot paths

`docs/qa/ops-graph-frozen-technical-materials-read-surface/screenshots/`  
before-full, before-location, after-full, after-summary, after-expanded-top/bottom, after-seq.

## 29. Visual verification steps

See `MATERIALS_RUNTIME_PROOF.md`.

## 30. Honest full-page UI verdict

Placement is correct: materials sit under metrics, above the task graph, collapsed by default so the graph remains primary. Expanded 22-row list is scannable (code/unit/qty) but can dominate the fold — acceptable with toggle. Semantic note is clear; risk of confusing with stock is low if note stays visible. Delta is **real operator value**, not cosmetic: previously materials were invisible despite existing frozen truth. Remaining visual defect: expanded list still competes with tasks; optional future density tweak (sticky note / denser rows) without changing semantics.

## 31. Boundaries verdict

**PASS**

## 32. Dead pieces

See worklog.

## 33. Roadmap awareness

Confirmed read-only; not materialization/inventory; upstream quantity/variant truth still open; DEC-009 blocked; Mobile/Pricing separate.

## 34. Blockers

None.

## 35. Warnings

1. Backend runtime needed restart (stale uvicorn on 8000) during verification  
2. Inventory reservation tables still NOT VERIFIED  
3. Lateral size variants still all shown (Owner rule pending)  
4. `project_sources/` still missing in repo  

## 36. Product commit SHA

Tip of this commit — verify with `git rev-parse --short HEAD`.

## 37. Next recommended Owner GO

```text
OWNER GO — Push Frozen Technical Materials Commit (after visual accept)
```

Optional follow-up (separate): upstream quantity / active-variant Product Truth — not consumption.

## 38. Stamp

**PASS WITH WARNINGS**

## 39. Cât suntem în direcția stabilită: **97/100%**
