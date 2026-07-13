# INTAKE_V6_SYSTEM_LED_COMMERCIAL_BUNDLE_UI_V1

**Date:** 2026-07-13  
**HEAD before:** dc3bed7  
**Branch:** main

## Objective

Present LIGHTING + ELECTRICAL as one commercial option **Sistem LED complet** in `IntakeV6OfferScopePanel` while persisting only technical codes `LIGHTING` and `ELECTRICAL`.

## Changes

- Split subset checkboxes into primary modules (Față, Cant, Spate), commercial bundle (Sistem LED complet), and advanced split (Iluminare, Electrică).
- Bundle toggle adds/removes both technical modules in one save intent.
- Partial advanced selection drives indeterminate bundle checkbox; full pair reflects bundle checked.
- No `SYSTEM_LED` sold module code introduced; save queue behavior from dc3bed7 preserved.

## Files

- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopePanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopePanel.test.tsx`
- `frontend/e2e/intake-v6-system-led-commercial-bundle-ui-v1.spec.ts`
- `docs/qa/intake-v6-system-led-commercial-bundle-ui-v1/`

## Verification

- Targeted Vitest: `IntakeV6OfferScopePanel.test.tsx`
- Playwright evidence: `intake-v6-system-led-commercial-bundle-ui-v1.spec.ts`
- Backend: existing offer-scope regressions only

## Boundary

No backend/pricing/DB changes. No dependency architecture merge. No adhesive/install gating changes.
