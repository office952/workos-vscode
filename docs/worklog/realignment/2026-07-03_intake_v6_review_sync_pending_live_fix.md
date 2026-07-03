# Intake V6 Review sync pending live fix

Date: 2026-07-03

## Scope

- Repo: `C:\Users\offic\workos_app_vs`
- Required SVG verified: `C:\Users\offic\workos_app_vs\fisiere-teste-svg\gradi-curat.svg`
- UI surface: Intake V6 operator, Step 2 - Review
- Target issue: footer status staying on `Sincronizare automata in asteptare` after Review autosave.

## Root Cause

`saveCurrentFinish` reconciled the canonical finish returned by `PUT /finish-setup` by comparing the persisted `syncedNextForm` against the outgoing request `body`.

That can skip a needed local state update when the request body already matches the persisted snapshot while the React local draft still differs. The visible symptom is that `selectorPendingSave` can continue comparing a stale local `form` against the updated workspace payload, keeping the footer in pending state.

## Change

Updated `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` so the successful save reconciliation compares the persisted canonical form against the current local `form`, not the outgoing `body`.

This keeps the draft state aligned with the saved workspace payload after autosave, without UI/UX changes.

## Validation

- `Test-Path "C:\Users\offic\workos_app_vs\fisiere-teste-svg\gradi-curat.svg"` returned `True`.
- `pnpm.cmd --dir frontend exec tsc --noEmit --pretty false` completed with no TypeScript errors. Existing pnpm config warning only.
- Live Review verification:
  - workspace route: `/intake-v6/IR-MR42Q8RI/operator`
  - visible Review layers included `maria`, `soare`, `ana`, `gradinita`, `logo dreapta`, `logo stanga/stanga`.
  - changed `intake-v6-face-type-pseudo:ana` from `oracal_641` to `oracal_651`.
  - footer changed immediately to `Sincronizare automata in asteptare`.
  - `PUT /api/v1/intake-v6/workspaces/IR-MR42Q8RI/finish-setup` returned `200`.
  - footer returned to `Preturi si materiale actualizate` after autosave.
  - no console errors and no current-workspace 404/500 were observed during the save cycle.
- User also verified the live UI result and confirmed it is OK.

## Evidence

- Screenshot saved: `docs/worklog/realignment/2026-07-03_intake_v6_review_sync_pending_live_fix.png`

## Notes

- A fresh upload with `gradi-curat.svg` was started and the UI recognized the file and six expected layers. Browser automation had trouble with the Step 1 card pagination, so final autosave verification used the Review workspace already containing the same `gradi-curat` semantic layer set.
- No UI copy, layout, flow, ProductAggregate, Task Graph, ExecutionPlan, or Employee Mobile changes were made for this fix.