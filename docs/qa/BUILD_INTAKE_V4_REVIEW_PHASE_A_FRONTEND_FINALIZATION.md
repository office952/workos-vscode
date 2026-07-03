# BUILD — Intake V4 Review Phase A Frontend Finalization

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Reference HEAD:** `e719846`  
**Scope:** Frontend-only Review operator UX finalization. **No** backend, ProductSystem, CostEngine, or schema changes in Phase A.

---

## Purpose

Close the operator Review form gap between prior cant/print/footprint fixes and a stable Phase A UX: pending-save truth, live calculation accuracy, area/footprint demotion to technical details, emblem/policromie cant coherence, CNC draft display boundaries, and task preview disclaimer.

---

## Workers delivered

| Worker | Summary |
|--------|---------|
| 0 | Preflight — classified prior vs Phase A diffs (see report §2) |
| 1 | Extended `isIntakeV4SelectorStatePendingSave`; pending-save banner; stopped breakdown/preview refetch on local form edits (`intakeV4PersistedReviewRefetchKey`) |
| 2 | Live calc: Oracal 641/651/8500 aggregation, LED consumables cost row, print+laminare dedupe retained, cant tarif lipsă |
| 3 | Footprint source radios + selected area moved to technical accordions; geometry face/emblem m² collapsed |
| 4 | `IntakeV4ArtworkFinishSection`: print+laminare, policromie, translucent/transparent, emblem cant fields |
| 5 | Face/back draft: `manual_required` hides CNC + draft totals (existing + tests retained) |
| 6 | Task preview boundary line in technical details only |
| 7 | This doc + audit pointer |

---

## Files changed (frontend)

- `frontend/src/lib/intakeV4/intakeV4FinishHydration.ts` (+ tests)
- `frontend/src/lib/intakeV4/intakeV4OperatorUiDisplay.ts`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4LiveCalculationSummary.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4SheetQuoteReviewPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4SheetFootprintOverridePanel.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ArtworkFinishSection.tsx` (+ test)

---

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v4/IntakeV4LiveCalculationSummary.test.tsx `
  src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.test.ts `
  src/lib/intakeV4/intakeV4FinishHydration.test.ts `
  src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.test.tsx `
  src/lib/intakeV4/intakeV4EdgeCantDisplay.test.ts `
  src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts `
  src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.test.tsx `
  src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftPanel.test.tsx `
  src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftSummaryCard.test.tsx `
  src/components/workos/intake-v4/IntakeV4LetterGroupFinishesSection.test.tsx `
  src/components/workos/intake-v4/IntakeV4ArtworkFinishSection.test.tsx `
  src/lib/intakeV4/intakeV4NearestOracalColor.test.ts `
  src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx `
  src/lib/intakeV4/intakeV4LedLighting.test.ts
```

*(Results: **71/71 PASS** — 15 test files, 2026-06-24.)*

---

## Boundary

- **In scope:** Review step UX, live sidebar, technical accordions, display helpers, Vitest.
- **Out of scope:** Backend breakdown services, footprint override persistence logic, ProductSystem task derivation, CostEngine rates, commits/push.
- **Not removed:** Backend area/footprint derivation; material m² in Materiale folosite / breakdown tables.

---

## Task preview audit (Worker 6)

Task preview in Review technical accordion remains **V3 catalog preview** (`getIntakeV4TaskPreview`). Operator copy:

> Task preview temporar — va fi derivat din ProductSystem după integrarea registry-ului de operații.

No ProductSystem wiring in Phase A.

---

## Next steps (Phase B+)

1. Wire task preview to ProductSystem registry when backend contract is ready.
2. Optional: refetch breakdown optimistically after save without full workspace round-trip (if latency remains an issue).
3. Frontend TS debt gate (`validate:frontend`) — separate build.

---

## Related audit

See [`AUDIT_INTAKE_V4_AREA_USAGE_AND_REMOVAL_PLAN.md`](./AUDIT_INTAKE_V4_AREA_USAGE_AND_REMOVAL_PLAN.md) — Phase A implements UI demotion items from that audit.
