# Inventory source disposition (F4)

| Source | Disposition | Evidence |
|---|---|---|
| `StockMovement` `movement_type=consumption` via deduction / material-actuals issue | CANONICAL_REAL_MOVEMENT | `models/stock_movements.py`, `inventory_deduction_service.py`, `material_actuals_service.py` |
| F3 valuation snapshots on movement | VALUATION_SOURCE | `unit_cost_snapshot`, `extended_cost_snapshot`, `valuation_method=inventory_unit_cost_at_movement` |
| `inventory_materials.unit_cost` / price history at movement time | VALUATION_SOURCE | freeze-on-write only |
| Aggregate / quote BOM builders | PLANNED_ONLY | commercial/planning; rejected as actual source_type |
| Reservation language / soft reserve | RESERVATION_ONLY | rejected (`reservation_not_actual`) |
| Client / quote / Pricing Registry at profitability read | COMMERCIAL_FORBIDDEN | profitability read model remains read-only |
| `adjustment` movement type | LEGACY_AMBIGUOUS | not treated as job actual cost |
| Lots/batches FIFO/LIFO engine | MISSING | not invented; snapshot-at-movement is V1 |

Canonical decision: **real StockMovement ISSUE/consumption (or scrap) with frozen valuation = actual material cost**.
