# Worklog — Intake V6 Finisaje SURFACE_FINISH ownership cleanup

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Initial HEAD:** `51ea07a`  
**Scope:** Frontend presentation only — Finisaje ownership accordion demotion

## Research tracks

See agent research + `docs/qa/intake-v6-finisaje-surface-finish-cleanup-2026-07-19/DESIGN_CHECKPOINT.md`.

Key finding: accordion was static JSX diagnostic prose above finish controls; no required operator action; collapsed hint leaked `SURFACE_FINISH` / `RETURN-CANT`.

## Design checkpoint

`docs/qa/intake-v6-finisaje-surface-finish-cleanup-2026-07-19/DESIGN_CHECKPOINT.md`

## Raw vocabulary found (primary before)

- `SURFACE_FINISH`, `RETURN-CANT`, `WORKSPACE`, sold `FINISH` in title/hint/body

## Primary vs advanced split

- **Primary:** Finisaje pe layer (Față / Cant / Spate / Vector Logo) first
- **Advanced:** `Detalii tehnice despre finisaj` after controls; RO summary + labelled raw tokens when expanded; collapsed by default with RO hint only

## Files changed

- `IntakeV6ReviewStep.tsx` (Finisaje ownership block only)
- `intakeV6OperatorVocabulary.ts` (+ finish ownership helpers)
- `intakeV6FinisajeOwnership.vocab.test.ts` (new)
- `frontend/e2e/intake-v6-finisaje-surface-finish-cleanup.spec.ts` (new)
- QA design/screenshots + this worklog

## Frozen (untouched)

Page 1 · composition · Montaj IA · segmented · electrical · sticky blocker architecture

## Tests / E2E

- Vitest vocab + placement guards
- Playwright Finisaje cleanup live
- Segmented CASE 1 regression

## Remaining risks

- Montaj still has a separate `Ownership: MOUNTING…` advanced note (intentionally frozen)
- Product System admin `FinishMountingOwnershipPanel` still shows SURFACE_FINISH (out of Intake V6 operator scope)

## Next step

Optional: demote Montaj ownership technical note with the same pattern — only if owner reopens that surface; not automatic.
