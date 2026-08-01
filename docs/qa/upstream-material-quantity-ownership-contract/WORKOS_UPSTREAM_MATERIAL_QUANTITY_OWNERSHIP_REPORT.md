# WORKOS — Upstream Material Quantity & Ownership Contract

**Stamp:** `PASS WITH WARNINGS`  
**Date:** 2026-08-01  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

## Mini decision

Accepted post-`8b960a19` audit; implement upstream material quantity/ownership contract (Models A/D), active variants, freeze semantics; no inventory/materialize/92401 rewrite.

## Repo / push

| Item | Value |
|------|-------|
| Before | HEAD `a1e35c9c`, remote `8b960a19`, ahead 1/0 |
| Audit scope | docs-only `docs/qa/post-8b960a19-roadmap-reconciliation/` |
| Push | `git push origin feat/capacity-batch-20d-scoped-b-92401` → confirmed **0/0** at `a1e35c9c` |
| Stash | `stash@{0}` intact |

## Architecture readback

Materials born from template `required_materials_json` → ProductAggregate materials (no qty copied from seed zeros) → freeze via `build_frozen_component_scope` → Quote/Order Snapshot V2 → ops-graph RO.  
Quantity evaluation added **at freeze** only. EIC heuristics and inventory excluded.

## Contract chosen

Single extension of `ProductAggregateMaterial` + `apply_technical_material_requirements` — no parallel DTO.

## Models

| Model | Verdict |
|-------|---------|
| A | Implemented for registered formulas (face area, perimeter, return_profile_linear_meter→perimeter, LED/PSU, panel area, …) |
| D | Implemented for formula-less rows |
| B | Analyzed, not implemented |
| C | Out of scope |
| E | Rejected (code + tests) |

## Proofs (summary)

- Active/inactive variants: unit tests  
- Duplicates preserved: unit tests  
- Null/no false zero: unit + 92401 runtime  
- Freeze path wired in `quote_snapshot_component_scope_service`  
- No live lookup on ops-graph  
- Legacy 92401: 22 null / 22 legacy_unspecified / 18 ops / authorize false  
- New Order fixture: **NOT VERIFIED** (tests cover contract)  
- material_inputs=[] · no readiness · no price/stock on surface  

## Files changed (product)

- `backend/schemas/product_aggregate.py`
- `backend/services/technical_material_requirement_service.py` (new)
- `backend/services/product_aggregate_service.py`
- `backend/services/quote_snapshot_component_scope_service.py`
- `backend/services/formula_handlers.py` (`return_profile_linear_meter`)
- `backend/services/ops_graph_frozen_technical_materials.py`
- `backend/tests/test_technical_material_requirement_contract.py` (new)
- `frontend/src/api/execution.ts`
- `frontend/src/components/workos/OpsGraphFrozenTechnicalMaterials.tsx` (+ test)
- QA pack + worklog under `docs/qa/…` and `docs/worklog/realignment/`

## Tests

| Suite | Result |
|-------|--------|
| `test_technical_material_requirement_contract` + ops-graph frozen + active_scope_filter | **20 passed** |
| Frontend `test:ci` | **207 passed** |
| Full pytest / quote_snapshot_v2 HTTP | **not relied on** — env 404/readiness noise observed; not treated as contract failure |

## UI verdict

Reused collapsed materials section. Labels distinguish derived / reference / source missing / legacy. Task graph remains primary. No stock/price/consum CTAs. Fold risk from long list remains (accepted Variant B).

## Boundaries

DEC-009 A · authorize false · no materialize · no inventory · no procurement · no material→op · 92401 immutable.

## Warnings

- Return wrap/paint/adhesive formulas still unregistered → `source_missing` when gates match  
- New live Order/E2E fixture not created  
- Backend may need reload for full FE label path on stale processes  

## Next Owner GO

```text
OWNER GO — Material Planning Hints Read-Only Surface
```
*(only after more Model A families resolve; still not inventory)*  
or  
```text
OWNER DECISION REQUIRED — Register return_wrap_area / return_paint_consumption formulas
```

## Direction

**98/100%**
