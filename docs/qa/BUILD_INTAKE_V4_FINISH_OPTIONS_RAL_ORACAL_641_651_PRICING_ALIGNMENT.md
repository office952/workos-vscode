# BUILD_INTAKE_V4_FINISH_OPTIONS_RAL_ORACAL_641_651_PRICING_ALIGNMENT

## Purpose

Align Intake V4 operator finish choices and material pricing for face Oracal 641/651 and return/cant finishes with owner production policy — without quote policy changes, quote/order/task creation, ExecutionPlan, `tasks_json`, or stock consumption.

## Before / after — face (FAȚĂ / PLEXIGLAS)

| Before | After |
|--------|-------|
| Oracal 641 had no color picker | Oracal 641 shows color selector |
| Oracal 641 used series `641` registry palette (sparse / separate) | Oracal 641 reuses Oracal **651** color palette in UI |
| Single `face_vinyl` row priced via registry `MAT-ORACAL-651` (5.0 EUR/m² seed) for all Oracal face | Series-specific rows `face_vinyl_641` / `face_vinyl_651` with owner prices |
| 641 could be priced same as 651 | 641 = **6.5 EUR/m²** excl. VAT; 651 = **9.0 EUR/m²** excl. VAT |

Payload convention unchanged: `face_finish_type: "oracal_641" | "oracal_651"` + `face_oracal_code` / `face_oracal_name`.

## Oracal 641 / 651 palette

- UI filter: `oracalColorPaletteSeriesForFace()` → `"651"` for both `oracal_641` and `oracal_651`.
- Source: `frontend/src/lib/colorRegistry/oracal651.ts` (`ORACAL_651_REGISTRY`).
- Persisted identity: `oracalSeriesForFace()` still returns `641` vs `651` for pricing/material keys.

## Oracal 641 / 651 pricing (excl. VAT)

| Series | Unit price | Price source | Material key |
|--------|------------|--------------|--------------|
| 641 | 6.5 EUR/m² | `intake_v4_owner_oracal_641` | `face_vinyl_641` |
| 651 | 9.0 EUR/m² | `intake_v4_owner_oracal_651` | `face_vinyl_651` |

Implementation: `backend/services/intake_v4_oracal_face_pricing_service.py` — applied in `intake_v4_material_breakdown_service.py`; owner rows skip registry override in `_apply_registry_prices`.

Vinyl area source: per-group `face_area_m2` summed via `_vinyl_area_from_letter_groups`, scaled to roll nesting total when present (`compute_roll_nesting_vinyl_estimate`). Example at 0.5834 m² base + 20% waste: 641 cost ≈ 0.7001 × 6.5 = 4.5507 EUR; 651 ≈ 0.7001 × 9.0 = 6.3009 EUR.

**Not changed:** Oracal 8500, print/laminare pricing (still registry `face_vinyl` legacy path).

## Return / cant (CANT / VOLUM)

Delivered in prior commit `89f9d0b`; verified unchanged by this build:

| UI label | Canonical payload |
|----------|-------------------|
| Alb | `white_aluminum` |
| Negru | `black_aluminum` |
| Auriu | `gold_aluminum` |
| Argintiu | `mirror_silver` (legacy `standard_aluminum` → Argintiu) |
| Vopsit RAL | `ral_paint` + RAL via V2 `ColorRegistrySelect` |
| Colantat | `oracal_wrapped` + Oracal **651** only |

**Gap (documented):** return Colantat has no separate return vinyl m² pricing row — return material uses aluminum profile registry by depth, not Oracal m² cant area.

## RAL selector

Reuses V2 `ColorRegistrySelect` + `RAL_COLOR_REGISTRY` via `IntakeV4ReturnCantFields` for `Vopsit RAL`.

## Legacy compatibility

Old payload values still read/display:

- `standard_aluminum` → Argintiu
- `oracal_wrapped` → Colantat Oracal 651
- `painted` / `ral_paint` → Vopsit RAL
- `same_as_face` — not offered in dropdown; preserved if present
- `unspecified` — warning / needs decision

## Review / Confirm labels

`intakeV4ConfirmSummary.ts` shows operator labels, e.g. `Oracal 641 <color>`, `Oracal 651 <color>`, `Colantat Oracal 651`, `Vopsit RAL RAL xxxx`.

## Files changed

- `backend/services/intake_v4_oracal_face_pricing_service.py` (new)
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/tests/test_intake_v4_oracal_641_651_pricing.py` (new)
- `backend/tests/test_intake_v4_material_breakdown.py`
- `frontend/src/lib/intakeV4/intakeV4FaceFinishOptions.ts`
- `frontend/src/lib/intakeV4/intakeV4FaceFinishOptions.test.ts` (new)
- `frontend/src/components/workos/intake-v4/IntakeV4LetterGroupFinishesSection.tsx`
- `frontend/src/lib/intakeV4/intakeV4ConfirmSummary.ts`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_oracal_641_651_pricing.py tests/test_intake_v4_material_breakdown.py -q
# 29 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4FaceFinishOptions.test.ts src/lib/intakeV4/intakeV4ReturnFinishOptions.test.ts src/components/workos/intake-v4/IntakeV4ReturnCantFields.test.tsx
# 10 passed
```

## Runtime smoke

- API-level: material breakdown on fixture payloads returns `face_vinyl_641` @ 6.5 EUR/m² and `face_vinyl_651` @ 9.0 EUR/m² with correct `price_source`.
- Browser smoke on PBL workspace: pending if frontend `:3000` not running during session.

## Boundary

- No quote policy change
- No quote / order / task creation
- No ExecutionPlan / `tasks_json`
- No stock consumption
- No global CostEngine / Pricing Registry edits (owner prices scoped to Intake V4 material breakdown)
- No V2 / V3 / Auth changes
- No push
