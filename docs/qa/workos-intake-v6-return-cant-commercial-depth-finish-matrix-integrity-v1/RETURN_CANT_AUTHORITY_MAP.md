# RETURN_CANT_AUTHORITY_MAP

**Baseline remote:** `2d495b60` · **Local chain:** `fa3437a8` + Oracal labor closure commit

## Live Ofertă authority (CPP)

| Finish | Quantity | Material | Labor |
|---|---|---|---|
| Stock / prefinished | — (no `finisaje_cant_*`) | zero finish surcharge | forming `modelare_cant_aluminiu` = **5 EUR/ml** flat (depth not tiered on sell) |
| Oracal wrap | material: `perimeter_m × depth_m` → m²; labor: `perimeter_m` → ml | 641 = 6.5 / 651 = 5.0 EUR/m² | **1 EUR/ml** via `RETURN_CANT_VINYL_APPLICATION_LABOR` (depth-independent) |
| RAL paint | `perimeter_m` (ml) | 30→2 / 60→2.5 / 80→3 / 100→4 EUR/ml | **1 EUR/ml** via `RETURN_CANT_RAL_PAINT_LABOR` |

## Face / generic (not RETURN-CANT)

| Authority | Role |
|---|---|
| F7F `VINYL_APPLICATION_EUR_M2` = 3 EUR/m² | Face vinyl application only (`finisaje_aplicare_autocolant_fata`) |

## Parallel / non-sell authorities (not duplicated)

| Authority | Role |
|---|---|
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
