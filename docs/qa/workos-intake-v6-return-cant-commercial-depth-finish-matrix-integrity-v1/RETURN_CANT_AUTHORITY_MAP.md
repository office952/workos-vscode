# RETURN_CANT_AUTHORITY_MAP

**Baseline:** `2d495b60`

## Live Ofertă authority (CPP F7F / F7H)

| Finish | Quantity | Material | Labor |
|---|---|---|---|
| Stock / prefinished | — (no `finisaje_cant_*`) | zero finish surcharge | forming `modelare_cant_aluminiu` = **5 EUR/ml** flat (depth not tiered on sell) |
| Oracal wrap | `perimeter_m × depth_m` → m² | 641 = 6.5 / 651 = 5.0 EUR/m² | **3 EUR/m²** on same developed area (F7F) |
| RAL paint | `perimeter_m` (ml) | 30→2 / 60→2.5 / 80→3 / 100→4 EUR/ml | **1 EUR/ml** via `RETURN_CANT_RAL_PAINT_LABOR` |

## Parallel / non-sell authorities (not duplicated)

| Authority | Role |
|---|---|
| Pricing Registry Oracal labor 1 EUR/ml | Seed/registry; **not** live CPP cant labor (F7F m² wins) |
| Profile MAT-PROFIL-LATERAL-*MM 2/3/4/5 EUR/ml | Purchase / CostEngine — not CPP finish lines |
| RAL min 100 lei/color | Legacy RON; EUR floor unpublished (`CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR=None`) |

## Token path

```
UI return_finish_type / return_depth_mm
→ finish_setup (+ letter_group_finishes)
→ quote_input (restored depth/finish + enrich bridge)
→ CPP finish_setup.return_* (+ per-group aggregation when groups complete)
→ commercial lines → priced dry-run → live rail
```
