# Material truth source inventory

| Source | Class | V1 Profitability role |
|--------|-------|------------------------|
| Intake / nesting geometry qty | ESTIMATED_CONSUMPTION | Not actual |
| ProductAggregate / planned BOM | PLANNED_MATERIAL | Rejected at writer |
| Soft reservation | RESERVED_MATERIAL | Rejected at writer |
| `MaterialActualsService.record_issue` | ISSUED + ACTUAL_CONSUMPTION + ACTUAL_COST | Canonical |
| `InventoryDeductionService.deduct` | ISSUED + ACTUAL_CONSUMPTION + ACTUAL_COST | Same freeze table |
| `record_scrap` | ACTUAL_CONSUMPTION + ACTUAL_COST | Canonical |
| `record_return` | ACTUAL_COST credit | Canonical netting |
| Legacy `movement_type=reversal` | LEGACY stock recovery | Consumption excluded from basis |
| Live `inventory_materials.unit_cost` | LIVE_UNSAFE alone | Freeze source only at write |
| Material market / quote price | COMMERCIAL_PRICE | Forbidden as actual |
| `ExecutionReality.materials_json` | OBSERVATION | Not cost until deducted |
| `post_job_truth` catalog×qty | LEGACY at-read | Not Profitability Actual RM authority |
| `profitability_analysis` MVP | LEGACY at-read | Not canonical Actual RM |

```text
PLANNED_ACTUAL_SEPARATION = VERIFIED
ACTUAL_MATERIAL_TO_COMMERCIAL_BACKFLOW = 0
```
