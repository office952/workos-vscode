# Worklog — Intake V6 Step 2 LED master sold-scope gate V1

**Date:** 2026-07-13  
**HEAD:** `6d5a74c` → (commit pending)  
**Task:** INTAKE_V6_STEP2_LED_MASTER_SOLD_SCOPE_GATE_V1

## Problem

ELECTRICAL-only offer scope still exposed the editable Step 2 LED master toggle (`finish_setup.illuminated`), allowing LIGHTING-owned changes without LIGHTING sold.

## Fix

- `IntakeV6ReviewLightingSection`: render editable master only when `showLightingFields` (`soldScopeVisibility.lighting`); ELECTRICAL-only shows read-only “Iluminare neinclusă în ofertă” and always shows Electrică subsection (even when `illuminated` is false).
- `IntakeV6ReviewStep`: guard `onIlluminatedChange` when LIGHTING not sold.
- No autosave or forced `illuminated=false` on scope deselect — persisted value preserved for re-enable.

## Verification

- Vitest: `IntakeV6ReviewLightingSection.test.tsx` (10)
- Backend: live calc + lighting/electrical scope + mount gating regressions
- Playwright: `intake-v6-step2-led-master-sold-scope-gate-v1.spec.ts` (4 screenshots)

## Out of scope (unchanged)

Backing mirror cleanup, Montaj policy, Step 1 bundle, pricing/backend mapping.
