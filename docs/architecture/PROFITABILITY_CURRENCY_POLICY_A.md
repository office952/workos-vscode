# Profitability Currency Policy A

**Owner:** `PROFITABILITY_CURRENCY_POLICY = A`  
**Status:** WIRED / DONE_FOR_V1

## Rule

```text
Reporting currency = EUR (Letters commercial)
Native costs remain RON on labor/material authorities
known_cost_eur = (labor_ron + material_ron) / profitability_fx_v1.eur_to_ron_rate
known_contribution_eur = accepted_commercial_total_eur − known_cost_eur
```

## Freeze

| Fact | Value |
|------|--------|
| Source at convert | `company_commercial_settings.eur_to_ron_rate` |
| Storage | `OrderSnapshotV2.profitability_fx_v1` |
| Freeze point | `order_convert` |
| At P&L view | **stamp only** — never live Settings |

## Not claimed

Not full FX accounting; not per-event FX; machine/other still N/A_FOR_V1.
