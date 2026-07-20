# Worklog — ACM_PANEL_OPERATOR_INPUT_COMMIT_SEMANTICS_V1

**Date:** 2026-07-20  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Mode:** Isolated fix after S0–S2 soak PASS WITH GUARDS

---

## Root cause

`IntakeV6AcmPanelInspector` called `onUpdateField` → `operatorPatch` → `PUT finish-setup` on every `onChange` keystroke. Typing `60` produced N PUTs (soak: 3).

## Controls audited

| Control | Policy |
|---------|--------|
| panel_width/height, thickness, l1, l2, fold_count | local string draft + 500ms debounce + blur/Enter/flush |
| Confirm geometry/construction/technical/relation | **one** combined patch (pending updates + confirm); `onMouseDown` preventDefault avoids blur-before-click double PUT |
| Segmented | flush drafts first if needed; segmented path unchanged |
| Unmount | cancel debounce only — no async persist |
| beforeunload | warn if pending/invalid — no sendBeacon |

## Debounce / flush design

- Constant: `ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS = 500` in `commitSemantics.ts`
- Hook: `useAcmPanelOperatorDrafts` — epoch cancels stale timers
- `flushAll()` → `AcmPanelFlushResult` (`nothing_to_commit` | `committed` | `blocked_invalid`)
- Confirm uses `takePendingUpdates()` + `buildAcmPanelConfirmActionWithUpdatesPatch` (single PUT)
- Bridge: `AcmPanelDraftFlushContext` for Back/Next/step click await

## Files

- `frontend/src/lib/intakeV6/acmPanel/commitSemantics.ts`
- `frontend/src/lib/intakeV6/acmPanel/useAcmPanelOperatorDrafts.ts` (+ test)
- `frontend/src/lib/intakeV6/acmPanel/operatorPatch.ts` (+ batch/confirm-with-updates)
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelInspector.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelConfigRegion.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/AcmPanelDraftFlushContext.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkspace.tsx` (provider + flush glue)
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` (thin jump flush)

## Tests

- Unit drafts: 12 passed
- operatorPatch batch/confirm-with-updates: passed
- Inspector commitSemantics: 5 passed
- Regression acmPanel + composition + coalesce: passed

## Runtime network proof

`docs/audits/_evidence/2026-07-20_acm-panel-input-commit-semantics/network-proof.json`

| Case | PUTs |
|------|-----:|
| typing 65 | 1 |
| paste 75 | 1 |
| rapid replace | 1 |
| blur / Enter | 1 |
| section switch | 1 |
| confirm + pending | **1** |
| two fields flush | 1 |

Before (soak keystroke): 3 PUTs for one typing flow. After: 1.

## Risks

- Blur between fields still commits per field (acceptable per owner).
- ReviewStep only calls flush bridge — draft ownership remains in acm-panel.
- Invalid draft blocks confirm/nav; operator must fix field.

## Commit

- Full: `1edccf2c36688d8f5065cc6ef05aab58eca7d51e`
- Short: `1edccf2`
- Message: `fix(intake-v6): debounce AcmPanel inspector field commits`
- HEAD before: `779bf25`

## Roadmap

S0–S2 can move to full PASS after owner accepts this commit. Next large choices remain owner-gated (remediation / blueprint / MULTI).
