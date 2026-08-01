# WorkOS Ops-Graph Frozen Technical Materials — Worklog

**Date:** 2026-08-01  
**Repo:** `C:\w\psiso`  
**Status:** COMPLETE (product commit local; not pushed)  
**Mini decision:** Order/plan-level read-only surface for frozen technical materials; null qty → Nespecificată; no inventory/pricing/task mapping.

---

## Repo state before

| Check | Result |
|-------|--------|
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD | `7b23b209` |
| Ahead/behind | 1/0 |
| Audit commit | docs-only pack only |
| Stash | `stash@{0}` present |

## Push proof for `7b23b209`

```text
89e021c7..7b23b209  HEAD -> feat/capacity-batch-20d-scoped-b-92401
Remote SHA = 7b23b2097fd6ca34d8fb02dd810f00a7770ab207
ahead/behind = 0/0
```

## Architecture readback

- 22 entries = frozen technical material truth from Order PA snapshot  
- Not inventory / actual consumption / operation-owned  
- 18 ops still have `material_inputs: []`  
- `material_readiness_inputs` not invented/persisted  
- No material→task mapping evidence  
- Duplicates / lateral variants not auto-collapsed  
- quantity null kept; units kept  
- Pricing/EIC ignored  
- Topo + SEQ out of change scope  
- DEC-003/004/005/007 open; DEC-009 blocked  
- Materialize / sessions / actuals forbidden  

## UI placement analysis

| | |
|--|--|
| Selected | **Variant B** — compact summary + on-demand expand, between metrics and task table |
| Alternatives | A = always-open section (heavier); C = per-op materials (**rejected** — no mapping) |
| Why | Keeps task graph primary; 22 rows available without forcing viewport noise |
| Operator benefit | Sees frozen BOM codes/units honestly without claiming stock |
| Visual risk | Expanded list can still dominate if left open — default collapsed |
| Ownership match | Order/plan-level frozen truth, not task ownership |

## Implementation

- `backend/services/ops_graph_frozen_technical_materials.py`  
- `GET /execution/plan/{id}` attaches `frozen_technical_materials` from `orders.snapshot_v2_json`  
- `OpsGraphFrozenTechnicalMaterials.tsx` + page wire  
- Tests backend + frontend; allowlist CI  

## Forbidden paths confirmation

No authorize/materialize/execute · no sessions/actuals writes · no inventory · no pricing · no material_inputs populate · no readiness persist · no SEQ/topo change · stash untouched · product commit not pushed.

## Dead pieces

| Piece | Class |
|-------|-------|
| Preview `material_readiness_inputs` still not persisted | LEGACY_STILL_CALLED / ACTIVE_MISLEADING if assumed complete |
| Task `material_inputs` always [] | ACTIVE_CORRECT as current truth; not filled by this GO |
| New projection | ACTIVE_CORRECT |

## Roadmap awareness

Read-only display only. Not materialization/inventory/procurement/readiness. Does not solve quantity sourcing, duplicate ownership, or material→operation mapping. DEC-009 remains blocked. Next healthy step = upstream Product Truth for quantities/active variants — not consumption.

## Next recommended Owner GO

```text
OWNER GO — Review Frozen Materials Surface Screenshots + Decide Upstream Quantity / Variant Truth
```

or push product commit after Owner visual accept.

## Direction

**97/100%**
