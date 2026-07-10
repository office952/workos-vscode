# INTAKE_V6_FOREX_BACKING_FINISH_PANEL_ORDER_V1

**Date:** 2026-07-10  
**Task:** `INTAKE_V6_FOREX_BACKING_FINISH_PANEL_ORDER_V1`  
**HEAD before:** `719844a`  
**Verdict:** PASS

---

## Before issue

After `INTAKE_V6_BACKING_FIELD_ORDER_FIX_V1`, **Spate litere** / Forex backing appeared as a **separate section** above review tabs — visually disconnected from finish dropdowns. Owner correction: integrate inside **Finisaje** panel under litere/logo finish dropdowns.

## Owner correction

Forex backing is a finish-panel field, not a standalone structural section. Same width/label style as other Finisaje dropdowns. Not under LED.

## Root cause

**Panel grouping issue (B)** — correct bindings (`backing_mode`, `back_bevel_enabled`); wrong visual container (standalone section vs Finisaje integration).

## Files changed

- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx`
- `frontend/scripts/capture-intake-v6-forex-backing-finish-panel-order-screenshots.mjs`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/*.png`
- `docs/worklog/realignment/2026-07-10_intake_v6_forex_backing_finish_panel_order_v1.md`

## What moved

- Removed standalone `intake-v6-review-section-backing` block above tabs.
- Added `IntakeV6ReviewBackingSelect` with `embedded` prop inside Finisaje panel (`intake-v6-review-backing-finish-integration`), after letter/artwork finish sections.
- Embedded styling uses `REVIEW_FIELD_*` / `REVIEW_SELECT_CLASS` to match other Finisaje dropdowns.

## What did not change

- State binding: `backing_mode`, `back_bevel_enabled` unchanged
- Options: Forex 10 mm fara/cu sanfren unchanged
- No backend / DB / pricing / calculation / payload changes

## Tests

```powershell
cd frontend
npm.cmd run test -- src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/lib/intakeV6/intakeV6ProductPlugin.test.ts
```

## Screenshots

- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/01_finish_panel_with_forex_dropdown.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/02_forex_not_under_led.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_finish_panel_order/03_led_off_forex_still_visible.png`

## Honest UI opinion

Form is clearer: Forex reads as the third finish choice (litere → logo → spate) in one panel. Dropdown alignment matches Finisaje fields. Backing only visible on Finisaje tab (acceptable per owner spec).

## Scope check

Forbidden scope respected: **YES**

## Next step

None required.

## Cat sunt in directia stabilita

**99/100%**
