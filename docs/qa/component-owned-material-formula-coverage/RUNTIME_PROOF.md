# RUNTIME_PROOF — Component-Owned Material Formula Coverage

**Date:** 2026-08-02  
**Base tip:** `c382f061` (pushed 0/0 before this product commit)

## Historical fixture 92401 (immutable)

Live GET `http://127.0.0.1:8000/api/v1/execution/plan/92401` (Bearer `__DEV_BYPASS_TOKEN__`):

| Check | Result |
|-------|--------|
| order / plan | 92401 / 13 |
| ops | 18 |
| frozen materials | 22 |
| qty null | 22 |
| false zero | 0 |
| quantity_status | all `legacy_unspecified` |
| material_inputs nonempty ops | 0 |
| authorize | `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False` |
| projection | `ops_graph_frozen_technical_materials/v2` |

Ops-graph UI: `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`

## New live Order fixture

**NOT VERIFIED** — no new Order Snapshot / freeze created in this GO (shared DB safety; no materialize).

New-contract behavior proven by unit tests:

- `return_wrap_area` Model A derived (0.84 m² for 10m × 60mm + waste/band)
- missing depth/perimeter → null `source_missing` (no default 60)
- inactive finish → not emitted
- Oracal vs RAL mutual exclusion
- `return_paint_consumption` remains `source_missing` + null

## No-side-effect

- No POST materialize
- No 92401 snapshot rewrite
- Authorize constant unchanged
