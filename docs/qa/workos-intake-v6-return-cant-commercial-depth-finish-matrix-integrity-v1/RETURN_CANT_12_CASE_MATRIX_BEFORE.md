# RETURN_CANT_12_CASE_MATRIX_BEFORE

Perimeter fixture: **12.5 ml**. Capture: CPP + adapter audit @ `2d495b60` (pre-repair).

## STOCK (`white_aluminum`)

| ID | depth | cant finish lines | forming rate | forming qty | commercial depth delta |
|---|---|---|---|---|---|
| S30 | 30 | none | 5 EUR/ml | 12.5 | **INTENTIONAL_ZERO** (finish) / forming flat |
| S60 | 60 | none | 5 | 12.5 | same |
| S80 | 80 | none | 5 | 12.5 | same |
| S100 | 100 | none | 5 | 12.5 | same |

Profile purchase tiers exist in registry but are **not** CPP sell lines (known audit NO_EFFECT).

## ORACAL (`oracal_wrapped` / 651)

| ID | depth | material qty m² | mat rate | mat subtotal | labor qty | labor rate | labor subtotal |
|---|---|---|---|---|---|---|---|
| O30 | 30 | 0.375 | 5.0 | 1.875 | 0.375 | 3.0 EUR/m² | 1.125 |
| O60 | 60 | 0.750 | 5.0 | 3.750 | 0.750 | 3.0 | 2.250 |
| O80 | 80 | 1.000 | 5.0 | 5.000 | 1.000 | 3.0 | 3.000 |
| O100 | 100 | 1.250 | 5.0 | 6.250 | 1.250 | 3.0 | 3.750 |

Material monotone OK. Labor scales with wrap area under F7F (not constant ml).

## RAL (`ral_paint`)

| ID | depth | mat rate EUR/ml | mat subtotal | labor rate | labor subtotal |
|---|---|---|---|---|---|
| R30 | 30 | 2.0 | 25.0 | 1.0 | 12.5 |
| R60 | 60 | 2.5 | 31.25 | 1.0 | 12.5 |
| R80 | 80 | 3.0 | 37.5 | 1.0 | 12.5 |
| R100 | 100 | 4.0 | 50.0 | 1.0 | 12.5 |

Minimum EUR unpublished — no invented top-up.

## Gaps proven before repair

1. Dry-run enrich omitted `return_depth_mm` bridge.
2. CPP ignored per-group cant depth/perimeter (job-level only).
3. Stock depth sell delta absent by current CPP catalog (document, do not invent profile sell lines).
