# INTAKE_V6_BACKING_FIELD_ORDER_FIX_V1

**Date:** 2026-07-10  
**Task:** `INTAKE_V6_BACKING_FIELD_ORDER_FIX_V1`  
**HEAD before:** `df6dd1e`  
**Verdict:** PASS

---

## Before issue

On Intake V6 operator review (`/intake-v6/:id/operator`), **Spate / backing** (`SPATE LITERE` / `intake-v6-backing-mode`) was rendered inside the **Iluminare & spate** tab, visually **after** LED configuration. Backing appeared coupled to illumination in the UI.

## Owner rule

Backing is a structural volumetric letter body decision. It must appear immediately after layer/composition decisions and **before** Finisaje, Iluminare, and Montaj. Not a child of LED.

## Root cause

**UI field grouping / render order only (B)** — `backing_mode` / `back_bevel_enabled` were already independent form fields (`domains: ["backing"]`). No data model or pricing coupling to LED.

## Files changed

- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/scripts/capture-intake-v6-backing-order-fix-screenshots.mjs` (new)
- `docs/qa/screenshots/2026-07-10_intake_v6_backing_order_fix/*.png`
- `docs/worklog/realignment/2026-07-10_intake_v6_backing_field_order_fix_v1.md` (this file)

## What changed

- Moved `IntakeV6ReviewBackingSelect` to a dedicated **Spate / backing** section (`intake-v6-review-section-backing`) placed immediately after product composition panel and before review tab navigation.
- Renamed Iluminare tab section from **Iluminare & spate** to **Iluminare**; removed backing block from that tab.
- Same bindings: `backing_mode`, `back_bevel_enabled` on mode change.

## What did not change

- No backend / DB / seed / migration
- No pricing or calculation logic
- No API payload shape
- No ProductDefinition / ProductSystem / Execution
- No route changes

## Tests

```powershell
cd frontend
npm.cmd run test -- src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/lib/intakeV6/intakeV6ProductPlugin.test.ts
```

`IntakeV6ReviewStep.commercialSettings.test.tsx` — pre-existing import resolution failure (`preOrderTechnicalPreviewApi`); unrelated to this change.

## Screenshots

- `docs/qa/screenshots/2026-07-10_intake_v6_backing_order_fix/01_backing_after_composition.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_backing_order_fix/02_backing_before_led.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_backing_order_fix/03_led_off_backing_still_visible.png`

## Honest UI opinion

Form is logically clearer: backing reads as structural body choice before finish/lighting tabs. Minor duplicate heading (`Spate / backing` shell + `Spate litere` label in select) — acceptable for this scoped fix.

## Scope check

Forbidden scope respected: **YES**

## Next step

None required for this fix; optional polish: unify backing section title to single label in a future UI pass.

## Cat sunt in directia stabilita

**99/100%**
