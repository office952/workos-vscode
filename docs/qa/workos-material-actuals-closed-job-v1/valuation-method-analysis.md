# Valuation method

Reuse existing Inventory freeze:

```text
valuation_method = inventory_unit_cost_at_movement
provenance = inventory_material_price_history | inventory_materials.unit_cost
```

No FIFO/LIFO/weighted average invented. Missing unit cost ⇒ `material_valuation_unavailable` (not zero). Catalog changes after freeze do not rewrite snapshots. Returns reuse the original frozen unit cost via `reverses_movement_id`.
