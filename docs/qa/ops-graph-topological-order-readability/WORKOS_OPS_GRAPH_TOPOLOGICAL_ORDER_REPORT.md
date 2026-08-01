# WorkOS Ops-Graph Topological Order Readability — Report

**Date:** 2026-08-01  
**Repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

---

## 1. Mini decision

| Field | Verdict |
|-------|---------|
| Change | Default ops-graph display = dependency/topo order; SEQ preserved |
| Docs push first | **YES** — `e8ea40a0..56adafb4` pushed (exit 0) |
| 92401 proof | 18 ops · plan 13 · SEQ gaps visible · 0 dep violations |
| Side effects | **None** |
| Stamp | **PASS WITH WARNINGS** |
| Direction | **96/100%** |

---

## 2. Branch / SHA before and after

| | SHA |
|--|-----|
| Before implementation | `56adafb4` (docs tip, synced) |
| After commit | tip of this commit (message: Improve ops graph dependency ordering readability) |

Exact tip SHA is recorded in the Owner final report chat (avoid self-referential SHA amend loop).

---

## 3. Docs commits pushed first?

**YES** — `git push origin HEAD` → `e8ea40a0..56adafb4`. Dirty was only untracked tmp/capacity (not suspicious).

---

## 4. Files changed

| File | Role |
|------|------|
| `frontend/src/lib/opsGraphDisplayOrder.ts` | Kahn topo sort helper |
| `frontend/src/lib/opsGraphDisplayOrder.test.ts` | Unit tests (5) |
| `frontend/src/pages/MaterializedOpsGraph.tsx` | Wire sort + note + SEQ header |
| `frontend/src/pages/MaterializedOpsGraph.test.tsx` | Assert display-order note |
| `frontend/scripts/ci-unit-tests.txt` | Allowlist new test |
| `docs/qa/ops-graph-topological-order-readability/*` | Proof + report |

---

## 5. Ordering logic summary

See `ordering-logic.md`. Display order ≠ remapped SEQ.

Kahn topo over `depends_on_task_ids`; ready-set tie-break by original source `sequence_index` then `task_id`. Cycle leftovers append by source SEQ. Task objects are not mutated.

---

## 6. SEQ preservation proof

Live 92401: multiset of `sequence_index` values unchanged after sort (`SEQ_preserved True`). UI rows still show SEQ **1,2,3,…,10,13,14,24…29** (gaps not densified).

---

## 7. 92401 runtime proof

| Check | Result |
|-------|--------|
| URL | `http://127.0.0.1:3000/execution/ops-graph?orderId=92401` |
| Ops | **18** |
| Plan | **13** · fixture label `—` (no MAT-02 hardcode) |
| Note visible | Display order / SEQ original |
| Dep violations in display order | **0** |
| Authorize | **false** |

---

## 8. DB no-side-effect proof

| Surface | Value |
|---------|-------|
| Ops count | 18 unchanged |
| Sessions tables | 0 |
| `execution_reality` 92401 | 0 |
| Authorize | false |

---

## 9. Screenshots path

`docs/qa/ops-graph-topological-order-readability/screenshots/after-92401-ops-graph.png`  
Before: `screenshots/BEFORE_NOTE.txt` (SEQ-only sort; for this fixture main chain coincides with dep order).

---

## 10. Honest UI verdict

Calm RO table. Label is restrained. For **92401**, visual row order largely matches prior SEQ sort because dependencies already follow SEQ on the main chain — the win is **correctness under disagreement** (proven in unit tests) plus explicit operator note that SEQ is source reference, not densified rank. SEQ gaps (11–12) remain honest.

---

## 11. Boundaries verdict

**PASS** — display-only frontend; no authorize/materialize/execute; no Pricing/HR/Mobile/SVG; no 92401 hardcode.

---

## 12. Blockers

**None.**

---

## 13. Warnings

1. `project_sources/*` missing — used Owner future-ordering warning  
2. 92401 visual delta vs SEQ-sort is modest (deps already aligned)  
3. Agent browser briefly showed session check; Owner URL works when authenticated  
4. Capacity partial QA packs still untracked locally  

---

## 14. Next recommended Owner GO

```text
OWNER GO — Push Ops-Graph Topo Order Commit + Optional Materials Honesty Charter
```

Or product: envelope materials honesty (no invent).

---

## 15. Stamp

**PASS WITH WARNINGS**

## 16. Cât suntem în direcția stabilită: **96/100%**
