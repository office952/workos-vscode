# Movement write entry-point matrix

| Entry | Router permission | Closed-job guard |
|-------|-------------------|------------------|
| `/api/v1/material-actuals/...` issue/return/scrap | `inventory.material_actual.write` | Yes |
| `/api/v1/inventory/...` deduct | `inventory.deduct_stock` | Yes |
| inventory reverse_movement | `inventory.adjust_stock` | Yes (if order_id) |
