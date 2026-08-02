# Material-flow coverage matrix

| Flow | Actual? | Owner | Evidence |
|------|---------|-------|----------|
| Manual issue/consumption | Yes | `MaterialActualsService.record_issue` | Frozen valuation |
| Scrap | Yes | `record_scrap` | Distinct movement type |
| Return | Yes | `record_return` + `reverses_movement_id` | Nets against original freeze |
| Reality deduction | Yes (stock) | `InventoryDeductionService` | Now closed-job guarded |
| Legacy reversal | Stock-only | `InventoryStockAdjustmentService` | Not F4-valued; guarded if order linked |
| Reservation | Rejected | `_reject_non_actual_source` | `reservation_not_actual` |
| Planned BOM | Rejected | same | `planned_bom_not_actual` |
