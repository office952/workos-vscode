# LED lighting density rules (shared)

## Purpose

Shared area-based LED module density for emblemă, casetă luminoasă, and illuminated surfaces — **not** hardcoded in `TPL-VOLUMETRIC-LETTERS`.

## Area density constant

```txt
LED_AREA_DENSITY_MODULES_PER_SQM = 60
```

## Formula

```txt
modules = ceil(area_sqm × 60)
```

## Geometry basis

- Use **outbox / bounding box area** (`artwork_area_m2` in Intake V4 quote geometry).
- Do **not** use filled area or letter perimeter for emblem/casetă lighting.

## Letter vs emblem separation

| Surface | Basis | Intake V4 field |
|---------|--------|-----------------|
| Litere volumetrice | Exterior perimeter + pitch (250 mm) | `letter_led_module_count` |
| Emblemă luminoasă | Outbox area × 60 module/m² | `emblem_led_module_count` when `emblem_lighting_mode = area_lit` |
| Total | Sum when emblem active | `total_led_module_count` |

PSU, adhesive LED, and consumable wiring use **total** modules when emblem lighting is active.

## Implementation

- Backend: `backend/services/shared_led_lighting_density_rules.py`
- Frontend preview sync: `frontend/src/lib/intakeV4/sharedLedLightingDensity.ts`
- Pricing preview sync: `intake_v4_pricing_preview_sync_service.py` (persists counts on `finish_setup`)

## UI modes (`emblem_lighting_mode`)

- `excluded` — emblem LED neincluse
- `area_lit` — calculate on outbox
- `needs_decision` — draft/review only; client/order/production blocked per policy

## Reuse

Same rule applies to future lightbox / classic casetă templates without duplicating density in template dossiers.
