# SAVE_TRIGGER_CONTROL_MATRIX_BEFORE

Baseline HEAD: `4d90f48e`

## Spine

`markLocalFinishChanged` → debounce → `PUT .../finish-setup` → `bumpPreviewRefresh` → offer-critical GETs

## Policy before

| Policy | ms | Used for |
|---|---:|---|
| short | **700** | Almost all discrete selectors |
| long | **1400** | Mounting template area typing (sticky latch) |
| commercial | **700** | Markup / discount / manual |
| AcmPanel draft | **500** | Numeric drafts then immediate PUT |
| immediate | 0 | Mounting scope, segmented confirms, Acm apply |

## Control classes

| Class | Examples | Debounce before |
|---|---|---|
| DISCRETE_SELECTOR | Face finish, return finish/depth, backing, lighting, PSU | **700 ms** |
| CONTINUOUS_NUMERIC | Template area m² | **1400 ms** |
| CONTINUOUS_NUMERIC | Commercial sliders | **700 ms** |
| CONTINUOUS_NUMERIC | AcmPanel W/H… | **500 ms** then immediate |
| FREE_TEXT | Footprint reason | Explicit Save only |
| EXPLICIT_CONFIRM | Artwork confirm, Acm confirms | Immediate / flush |

## Operator impact

Discrete selection waited **≥700 ms** before save started even though CPP itself is fast.