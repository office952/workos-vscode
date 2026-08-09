# Profitability Monetary Composition V1

**Status:** PARTIAL — composition + N/A closed; **currency gate blocks Letters EUR vs RON costs**  
**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_PROFITABILITY_MONETARY_COMPOSITION_V1`  
**Owner decisions:**  
`MACHINE_COST_V1 = DECLARE_NA_FOR_V1`  
`OTHER_DIRECT_COST_V1 = DECLARE_NA_FOR_V1`

## Formula (same currency only)

```text
known_v1_contribution =
  accepted_commercial_total
  − actual_labor_cost
  − actual_material_cost
```

Machine / other_direct: `N_A_FOR_V1` (value null, never 0).

## Authorities

| Input | Source |
|-------|--------|
| Revenue | `order_snapshot_v2.accepted_commercial_total` + currency |
| Labor | `ActualLaborCostLine` frozen |
| Material | `stock_movements.extended_cost_snapshot` |
| Machine | Owner N/A |
| Other | Owner N/A |

## Currency

```text
FX_REQUIRED = YES for typical Letters (EUR revenue vs RON labor/material)
Silent EUR−RON subtraction = FORBIDDEN
Reason code = currency_mismatch_no_fx
```

When currencies match (e.g. RON−RON): `scope_status = COMPLETE_FOR_V1_SCOPE`.  
When mismatch: `scope_status = BLOCKED_CURRENCY`; known labor+material cost may still be available in cost currency.

## Read model

`GET /api/v1/profitability-actual/order/{id}` → `monetary_v1` + updated `profitability_result`.

## UI

`/execution/:orderId` — CostsCompletenessPanel + FinalResultPanel (admin/manager).

## Not claimed

Not accounting profit / EBIT / all real-world costs.
