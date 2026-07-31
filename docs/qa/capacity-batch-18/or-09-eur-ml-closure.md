# Capacity Batch 18 — Track C: OR-09 EUR/ml Closure

**Mode:** Display clarity only · **no Pricing / CostEngine** · **no invent unit** · **no materialize**  
**Date:** 2026-07-31  
**Fixture:** `FIX-DEC009-MAT-01` · order `973010` · plan `12` · ops **12**  
**Route:** `/execution/ops-graph`  
**Product:** `C:\w\psiso` (`office952/workos-vscode`)  
**Branch:** `fix/capacity-batch-18-or-09-eur-ml`  
**Prior:** Batch 16 OR-09 / V-15 **WARNING** · Batch 17 residual (out of Track C scope)

---

## Kickoff confirmation

| File | Ownership impact |
|------|------------------|
| `docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md` | UI may format/guide; must not invent business fields, units, or Pricing |
| `docs/workflow-adv/README.md` + contracts | Product System vs Pricing vs Capacity / task-graph boundaries |
| Batch 16/17 gap + ui-clarity | OR-09 classified as template-provenance commercial phrasing |
| `execution_ops_graph_read_clarity.py` (Batch 17 Track B) | Extend display-only honesty; no persist rewrite |

**Allowlist:**

- `backend/services/execution_ops_graph_read_clarity.py`
- `backend/tests/test_execution_ops_graph_read_clarity.py`
- `frontend/src/api/execution.ts`
- `frontend/src/pages/MaterializedOpsGraph.tsx`
- `frontend/src/pages/MaterializedOpsGraph.test.tsx`
- `docs/qa/capacity-batch-18/or-09-eur-ml-closure.md`

**Non-goals:** CostEngine · Pricing registry edits · invent `task.unit` · upstream Product System / seed rename · materialize POST · sessions/actuals · hide process name without soften path · densify sequence

```text
KICKOFF READ CONFIRMED — OR-09 EUR/ml DISPLAY CLARITY AUTHORIZED
```

---

## Locate

| Surface | Where EUR/ml appears |
|---------|----------------------|
| Ops-graph Task column | `display_name` / `read_clarity.identity.label` for seq **4** and **5** |
| Fixture evidence | Batch 16/17 DOM + plan snapshot |
| Template provenance | `seed_build4_templates.py` op labels `(EUR/ml serviciu)` |
| Pricing / registry | Separate (workcenter rates, material EUR/ml) — **not** rendered on ops-graph |

Observed labels (raw):

1. `Modelare cant profil — utilaj (EUR/ml serviciu)`
2. `Lipire cant pe față (EUR/ml serviciu)`

---

## Classification (OR-09 / V-15)

| Candidate class | Verdict | Why |
|-----------------|---------|-----|
| Pricing display | **No** | Ops-graph does not show rates, totals, or CostEngine output |
| Capacity metadata | **No** | Minutes / WC / machine_type are capacity fields; EUR/ml is not among them |
| Catalog / task `unit` | **No** | Fixture `unit` remains null ×12 (`unknown`); EUR/ml is free-text inside `display_name` |
| Misleading artifact | **Yes** | Commercial unit phrasing leaked into Product System template process labels |

**Artifact kind:** `misleading_commercial_unit_phrasing`  
**Role:** `template_provenance_not_client_price_not_capacity_unit`  
**Owner lock (upstream rename):** `PRODUCT_SYSTEM_TEMPLATE_LABEL` — remains Owner decision; not silently rewritten in seed/PD this batch.

---

## What changed

| Layer | Change |
|-------|--------|
| Read model | `classify_ops_graph_label` · `identity.ops_display_label` · `identity.label_clarity` · plan `label_policy` |
| Persist | **Unchanged** — raw `display_name` on task rows not rewritten |
| UI | Prefer `ops_display_label`; tooltip / `data-label-provenance` keeps raw; page OR-09 note when count > 0 |
| Soften rule | Strip parentheticals matching `EUR/ml` only — process wording kept; no invent rate/unit |

Softened display:

| Seq | Ops display |
|-----|-------------|
| 4 | `Modelare cant profil — utilaj` |
| 5 | `Lipire cant pe față` |

Hide? **No** — process name remains. Only the commercial parenthetical is softened, because source truth supports that it is pricing-adjacent wording, not Capacity/task-unit truth.

---

## Tests

| Check | Result |
|-------|--------|
| `backend/.venv/Scripts/python.exe -m pytest tests/test_execution_ops_graph_read_clarity.py -q` | **11 passed** |
| `npx vitest run src/pages/MaterializedOpsGraph.test.tsx` | **4 passed** |
| Fixture commercial count | `label_policy.commercial_unit_phrasing_task_count == 2` |
| `task.unit` invent | Asserted still `unknown` / null |

---

## Alignment

| Boundary | Honored how |
|----------|-------------|
| Product System | Owns template labels; raw `identity.label` retained; upstream rename Owner-gated |
| Pricing separation | No rates shown; EUR/ml not treated as client price on Capacity surface |
| Capacity boundary | Ops-graph remains planning/task-graph RO; no cost fields added |
| Task graph read model | Additive `read_clarity` only; counts guard 12→12; no dep/sequence rewrite |

---

## SMART CODE COMPLIANCE

| Gate | Evidence |
|------|----------|
| No Pricing / CostEngine | Soften string only; no registry / calculator touched |
| No invent unit | `unit` classification unchanged (`unknown` when null) |
| No frontend business truth | Display + tooltip from GET honesty fields |
| No persist mutation | Raw `display_name` equal before/after enrich |
| No materialize / sessions | Out of allowlist |
| FAIL ⇒ no FREEZE claim | Closure is display WARNING close, not FREEZE ON |

---

## Return summary

| Item | Value |
|------|-------|
| **Closed** | **Y** (ops-graph display) — upstream template rename remains Owner optional |
| **What changed** | Read-clarity label soften + ops-graph UI/tooltip + OR-09 note |
| **PR / SHA** | See git / PR after push (stamp below when landed) |
| **Handoff copy** | `workos-atoms-ui-chrome-handoff/docs/qa/capacity-batch-18/or-09-eur-ml-closure.md` |
