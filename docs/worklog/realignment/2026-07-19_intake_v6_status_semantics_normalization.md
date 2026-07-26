# Worklog — Intake V6 status semantics normalization

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `a657600`

## Inventory

Audit accepted. Drift: OK/Confirmat, Propus/Propunere, De confirmat, Draft/neconfirmat, Totul OK, Lipsă overload, owner gate phrasing.

## Mapping chosen

8 canonical semantics via `intakeV6OperatorVocabulary` (+ rejected/inactive/informational helpers).  
Propunere ≠ Necesită confirmare kept on Page 1 (text vs icon).

## Files changed (product)

- `frontend/src/lib/intakeV6/intakeV6OperatorVocabulary.ts` (+ tests)
- `frontend/src/lib/intakeV6/segmentedBackground.ts`
- `frontend/src/lib/intakeV6/intakeV6ConfirmConsolidatedStatus.ts` (+ tests)
- `frontend/src/lib/intakeV6/intakeV6ReviewHeaderStatus.ts` (+ tests)
- `frontend/src/lib/intakeV6/intakeV6WorkspaceHeaderStatus.test.ts`
- `frontend/src/lib/intakeV6/intakeV6OperatorStateBadges.ts` (+ tests)
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.ts`
- Page 1 / Finisaje / electrical / composition / system checks / ACP / ReviewStep status labels
- Matching component tests

## Not changed

Backend, schemas, contracts, Montaj structure, analyzer, PD, Aggregate, pricing, Execution, foreign WIP.

## Tests

`vitest run` targeted suite — **83 passed**.

## Screenshots

`docs/qa/intake-v6-status-semantics-normalization-2026-07-19/screenshots/` (`before_*`).

## Next step

Owner GO only if further polish needed (sticky/footer count split, live after screenshot pack). Otherwise freeze vocabulary and continue roadmap.
