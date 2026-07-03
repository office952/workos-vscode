# FIX_INTAKE_V4_OWNER_ORACAL_PRICE_SOURCE_GUARD_FOR_EDGE_CANT

## Purpose

Protect Intake V4 owner Oracal `price_source` values from Pricing Registry overrides when the source is composed with module prefixes (e.g. edge/cant wrap rows).

## Root cause

`shared_edge_cant_rules` sets `price_source = shared_edge_cant_rules|intake_v4_owner_oracal_651` on `edge_cant_oracal_651` rows. `intake_v4_material_breakdown_service._apply_registry_prices` skipped registry override only when `price_source.startswith("intake_v4_owner_oracal")`. Composite sources fell through; dev `pricing_registry` `MAT-ORACAL-651` @ 5 EUR/m² replaced owner catalog 9 EUR/m².

Face Oracal rows were already protected because their `price_source` is direct (`intake_v4_owner_oracal_651`).

## Before / after

| Case | Before | After |
|------|--------|-------|
| `intake_v4_owner_oracal_651` | 9 EUR/m² (protected) | 9 EUR/m² (protected) |
| `shared_edge_cant_rules\|intake_v4_owner_oracal_651` | 5 EUR/m² (registry override) | 9 EUR/m² (protected) |
| Non-owner `missing` + registry code | registry price | registry price (unchanged) |

No price value changes. No Pricing Registry rewrite.

## Implementation

`is_intake_v4_owner_oracal_price_source()` in `intake_v4_oracal_face_pricing_service.py` now checks each `|`-separated segment for `intake_v4_owner_oracal` prefix. Used by `_apply_registry_prices`.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_oracal_641_651_pricing.py tests/test_shared_edge_cant_rules.py -vv
```

Coverage:

- Direct owner source protected from registry override
- Composite owner source protected from registry override
- Non-owner sources still use registry override
- `edge_cant_oracal_651` stays 9 EUR/m² when registry has MAT-ORACAL-651 @ 5
- 641 / 8500 owner sources remain protected
- Missing-registry material breakdown tests still pass

## PBL smoke (IV4-4B172FD4)

Workspace `0f300dcf-0b77-4fc1-affd-6e2a20329804` with letter groups `oracal_wrapped`:

- `edge_cant_oracal_651`: area ≈ 1.1442 m², unit m², 9 EUR/m², cost ≈ 10.30 EUR before VAT (`estimated_cost` 10.2978)
- `price_source`: `shared_edge_cant_rules|intake_v4_owner_oracal_651`
- Restored: `return_finish=white_aluminum`, `backing_mode=none`, `emblem_lighting_mode=needs_decision`

No quote/order/tasks created.

## Boundary

No ExecutionPlan, tasks_json, stock consumption, CostEngine, Color Registry rewrite, employee assignment, or push in this build.
