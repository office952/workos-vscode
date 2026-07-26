# Intake V6 — Configuration Guidance Spine

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `9e4637a`  
**Mode:** Frontend presentation consolidation — **no domain / backend / layout redesign**

## Verdict

**PASS.** One guidance model answers: where am I, progress, next action, blocker/warning counts. Footer is the primary next-action surface; sticky Review banner no longer repeats the compact next-action paragraph.

## Guidance model

`frontend/src/lib/intakeV6/intakeV6OperatorGuidance.ts` → `buildIntakeV6OperatorGuidanceModel`

| Field | Example |
|-------|---------|
| whereAmI | Straturi / Configurare / Confirmare |
| statusLabel | Configurare incompletă / Pregătit |
| progressLabel | 2 / 3 confirmări |
| nextAction | Confirmă compoziția produsului. |
| countsLabel | 1 blocant · 2 avertizări |

Domain gates unchanged (`getIntakeV6FirstBlocker`, `canContinueFromReviewStep`, final blockers).

## Consolidation

| Before | After |
|--------|--------|
| Footer plain reason | Footer **guidance spine** (status · progress · counts · Următorul pas) |
| Sticky compact issue = same next action | Sticky: title + counts; hint → footer; details on expand |
| „propusă de analyzer” in Continuă reason | Normalized RO without analyzer |

No new banners, no new cards, no Montaj redesign.

## Files

- `intakeV6OperatorGuidance.ts` (+ test)
- `IntakeV6OperatorWorkspaceFooter.tsx` (+ test)
- `IntakeV6OperatorWorkspace.tsx` (pass continue flag)
- `IntakeV6ReviewOperatorBlockerBanner.tsx` (+ test)
- `IntakeV6ReviewStep.tsx` (suppressCompactDetail + footer-oriented guidance)
- `intakeV6Readiness.ts` / `intakeV6FinalConfirmationBlockers.ts` (copy cleanup only)

## Tests

Vitest: guidance + footer + sticky banner + readiness + final blockers — **PASS**.

## Screenshots

`screenshots/` — before pack from journey audit (same stack). Live after: HMR on FE `:3001`; footer spine is unit-proven.

## Frozen

Page 1 / composition / Finisaje / Iluminare / Montaj IA / segmented / electrical contracts / status vocabulary IDs / backend.
