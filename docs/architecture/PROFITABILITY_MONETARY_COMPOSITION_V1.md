# Profitability Monetary Composition V1

**Status:** DONE_FOR_V1  
**Date:** 2026-08-09  
**Owner GOs:** monetary composition + `PROFITABILITY_CURRENCY_POLICY = A` wiring  
**Owner decisions:**  
`MACHINE_COST_V1 = DECLARE_NA_FOR_V1`  
`OTHER_DIRECT_COST_V1 = DECLARE_NA_FOR_V1`  
`PROFITABILITY_CURRENCY_POLICY = A`

## Formula

```text
Same currency:
  known_v1_contribution = revenue − labor − material

Policy A (EUR revenue + RON costs):
  known_cost_eur = (labor_ron + material_ron) / profitability_fx_v1.eur_to_ron_rate
  known_v1_contribution_eur = revenue_eur − known_cost_eur
```

Machine / other_direct: `N_A_FOR_V1` (value null, never 0).

## Authorities

| Input | Source |
|-------|--------|
| Revenue | `order_snapshot_v2.accepted_commercial_total` + currency |
| Labor | `ActualLaborCostLine` frozen |
| Material | `stock_movements.extended_cost_snapshot` |
| FX stamp | `order_snapshot_v2.profitability_fx_v1` (frozen at convert) |
| Machine | Owner N/A |
| Other | Owner N/A |

## Currency

```text
Silent EUR−RON without stamp = FORBIDDEN
Missing stamp on EUR/RON job → profitability_fx_stamp_missing
Live Settings at P&L view = FORBIDDEN
```

Same currency → `COMPLETE_FOR_V1_SCOPE`.  
Policy A with stamp → `COMPLETE_FOR_V1_SCOPE` in EUR.  
See `PROFITABILITY_CURRENCY_POLICY_A.md`.

## Read model

`GET /api/v1/profitability-actual/order/{id}` → `monetary_v1` + updated `profitability_result`.

## UI

`/execution/:orderId` — CostsCompletenessPanel + FinalResultPanel (admin/manager).

## Not claimed

Not accounting profit / EBIT / all real-world costs.
