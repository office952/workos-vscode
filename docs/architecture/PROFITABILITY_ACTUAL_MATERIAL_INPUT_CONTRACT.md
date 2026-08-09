# Profitability Actual Material Input Contract

**Status:** CLOSED (V1 sufficiency)  
**Contract id:** `profitability_actual_material_input/v1`  
**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_WORKOS_V1_MATERIAL_ACTUALS_SUFFICIENCY`

## Separation (non-negotiable)

```text
Planned BOM / nesting estimate / quote material
  ≠ ACTUAL MATERIAL INPUT

StockMovement ISSUE / SCRAP / RETURN (frozen valuation)
  → ACTUAL MATERIAL INPUT          ← this contract
       (+ optional job closure gate)
  → ACTUAL MATERIAL COST aggregate ← same freeze authority
       + labor + revenue
  → PROFITABILITY MONETARY         ← separate GO
```

```text
ACTUAL_MATERIAL_TO_COMMERCIAL_BACKFLOW = 0
LABOR_DOUBLE_COUNT = 0
MACHINE_RUN_DOUBLE_COUNT = 0
```

## Authorities

| Concern | Value |
|---------|--------|
| MATERIAL_IDENTITY_AUTHORITY | `inventory_materials.id` (+ `code` projection) |
| MATERIAL_ACTUAL_QUANTITY_AUTHORITY | `stock_movements.quantity` net of returns; legacy full `reversal` excludes original consumption |
| MATERIAL_ACTUAL_FREEZE_POINT | **stock movement write time** |
| MATERIAL_ACTUAL_COST_AUTHORITY | `stock_movements.extended_cost_snapshot` (`inventory_unit_cost_at_movement`) |
| Write authority | `MaterialActualsService` (canonical) + `InventoryDeductionService` (same freeze columns) |
| Read helper | `build_profitability_actual_material_input` |

## Historical stability

| Change after consume | Historical job |
|---------------------|----------------|
| Live `inventory_materials.unit_cost` | Unchanged (uses snapshot) |
| Price history append | Unchanged for prior movements |
| ProductDefinition / nesting edits | Unchanged (actuals are movements, not rebuild) |
| Planned BOM | Never admitted as actual (`planned_bom_not_actual`) |

## Fail-closed

Missing movements → `material_movement_missing` / incomplete input.  
Missing unit cost at write → movement incomplete; basis unavailable (`material_valuation_unavailable`).  
Unresolved return → unavailable.  
Multi-currency mix on one order → unavailable (no invent FX).

## V1 Letters materials

Identity is inventory `material_id`/`code`. Distinct Oracal codes remain separate lines. Return/cant and face materials are separate lines when issued as distinct materials. Lighting/electrical sufficient when issued as valued inventory materials (same path).

## Not required for V1

Warehouse locations, lots, MRP, PO, barcode, scrap analytics platform, FIFO engine.
