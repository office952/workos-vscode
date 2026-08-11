# RETURN_CANT_12_CASE_MATRIX_AFTER

Same perimeter **12.5 ml**. Proven by `tests/test_intake_v6_return_cant_depth_finish_matrix.py`.

## STOCK

Unchanged by design: no `finisaje_cant_*`; forming 5 EUR/ml flat → **INTENTIONAL_ZERO_DELTA** for stock finish depth on sell path.

## ORACAL

Material qty = perimeter × depth/1000; rates unchanged (651 @ 5 EUR/m²).  
O30 < O60 < O80 < O100 material subtotals.  
Labor remains F7F **3 EUR/m²** on developed area (scales with depth; registry 1 EUR/ml not applied).

## RAL

Tiers 2 / 2.5 / 3 / 4 EUR/ml consumed; labor 1 EUR/ml constant across depths.  
R30 < R60 < R80 < R100 material. Minimum EUR still unpublished (F7H).

## Fidelity repairs

| Repair | Effect |
|---|---|
| quote_input restores `return_depth_mm` / `return_finish_type` | depth reaches CPP |
| enrich bridges `return_depth_mm` | dry-run cannot drop depth |
| CPP per-group Oracal wrap area | mixed 30+100 → 0.90 m² |
| CPP per-group RAL tiers | mixed 30+100 → material 40 EUR, labor 12.5 |
