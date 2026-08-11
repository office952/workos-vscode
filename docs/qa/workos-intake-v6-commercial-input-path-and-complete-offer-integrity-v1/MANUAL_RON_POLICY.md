# MANUAL_RON_POLICY

```
MANUAL_RON_POLICY = A — TRUE RON ADJUSTMENT
Owner decision: 2026-08-11
```

## Rules

1. Operator enters `manual_adjustment_ron` (RON).
2. Conversion runs **only on backend**.
3. When `manual_adjustment_ron == 0`: no FX required.
4. When `manual_adjustment_ron != 0` and commercial presentation currency is EUR:
   - `require_configured_eur_to_ron_rate` / fail-closed if missing
   - `manual_adjustment_eur = round(manual_ron / rate, 2)` via `_round_money`
5. When commercial currency is already RON (diagnostic cost-plus): use RON as-is; no FX conversion.
6. Persist in `commercial_adjustment_trace`:
   - original RON
   - converted EUR (when applied)
   - `eur_to_ron_rate`, `rate_source`, `fx_freeze_point`
7. Frontend never performs authoritative conversion or official total calculation.
