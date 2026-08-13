# BEVEL_RATE_AUTHORITY

```text
OWNER GO = 1 + 3 (2026-08-13)
STATUS = CONFIRMED
RATE_CODE = CNC_ROUTER
RATE_VALUE = 1.5 EUR/ml/pass
PASSES = VOLUMETRIC_BACKING_BEVEL_RULE.passes = 2
```

## Owner decision

Reuse existing `CNC_ROUTER`. Do not invent a new registry tariff.

```text
subtotal_eur =
  backing_cnc_cutting_perimeter_ml (bevel-enabled groups only)
  × 2 passes
  × 1.5 EUR/ml/pass
```

Example: `7.4175 ml × 2 × 1.5 = 22.2525 EUR` net.

CPP displays contour ml and applies the pass factor on the unit price (`1.5 × 2 = 3.0 EUR/ml`).

## Provenance

- Seed: `backend/seeds/seed_volumetric_workcenter_rates.py`
- Rule: `sanfren_spate` / `VOL_V2_BACK_BEVEL_CNC_ML`
- Source: `commercial_rules_volumetric_v2:owner_confirmed:back_bevel_cnc_router_2026_08_13`
- Publication: workcenter-reuse provisional — **not** F7I.1 `OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES`
