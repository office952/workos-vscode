# Authorities

| Token | Exact |
|-------|--------|
| MATERIAL_IDENTITY_AUTHORITY | `inventory_materials.id` (+ projected `code`) |
| MATERIAL_ACTUAL_QUANTITY_AUTHORITY | `stock_movements` net of returns; legacy full reverse excludes consumption |
| MATERIAL_ACTUAL_FREEZE_POINT | stock movement write time |
| MATERIAL_ACTUAL_COST_AUTHORITY | `extended_cost_snapshot` / `inventory_unit_cost_at_movement` |
| HISTORICAL_MATERIAL_COST_STABILITY | PROVEN (catalog change after issue) |
| HISTORICAL_MATERIAL_QUANTITY_STABILITY | PROVEN (DB rows; not ProductDefinition rebuild) |
| CURRENCY_AUTHORITY | `currency_snapshot` per movement; mixed currencies fail-closed |
| DUPLICATE_WRITABLE_AUTHORITY | Single table `stock_movements`; two writers share freeze contract |

## Letters V1 set (by identity, not free text)

Face/plexiglas, Oracal series/color codes, aluminum return, adhesives/electrical — when present as inventory materials with unit cost — use the same issue path. No ACM/Logo expansion.
