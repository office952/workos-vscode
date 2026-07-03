# HOTFIX: Intake Detail white page after SVG build

**Date:** 2026-06-04  
**Build status:** **PASS**  
**Commit:** not committed (per user rule)  
**Introduced by:** `892721e` — feat: implement SVG intake layer mapping persistence

## Exact crash error

```
ReferenceError: hasGeometryEstimateFromSpec is not defined
```

- **File:** `frontend/src/lib/vectorStudioPreview.ts`
- **Line:** 251 (inside `buildVectorStudioInfo`)
- **Component/hook:** `Product001IntakeSpecEditor` → `useMemo` → `vectorReviewSummary` → `buildVectorStudioInfo(spec, layerAnalysis)`
- **Route/intake:** `/intake/WI-E2E-COMMERCIAL-WARN-001` (and any intake rendering TPL-VOLUMETRIC-LETTERS spec editor)

Reproduced in unit tests (`vectorStudioPreview.test.ts`) before fix; browser showed blank page until React error boundary swallowed render.

## Root cause

During the SVG intake build, `vectorStudioPreview.ts` imported `hasGeometryEstimateInSpec` from `svgIntakeFlow.ts` but called a mistyped name `hasGeometryEstimateFromSpec` in warning logic. Any mount of `Product001IntakeSpecEditor` that computed `vectorReviewSummary` threw immediately — including legacy E2E fixtures with partial `product_spec_json` and no new SVG mapping fields.

## Fix applied

Renamed calls to the imported helper:

- `hasGeometryEstimateFromSpec(spec)` → `hasGeometryEstimateInSpec(spec)` (2 occurrences)

No feature removal; SVG intake flow unchanged.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/vectorStudioPreview.ts` | Fix typo in helper name |
| `frontend/src/lib/vectorStudioPreview.test.ts` | Regression: E2E WARN legacy spec shape |
| `frontend/src/components/workos/Product001IntakeSpecEditor.vectorFastAsk.test.tsx` | Regression: WARN fixture + empty partial spec render |
| `frontend/src/lib/intakeReadinessStages.partialSpec.test.ts` | **New** — partial/null spec does not throw |

## Hotfix behavior

- Intake detail renders for legacy/partial specs (E2E WARN fixture included)
- Vector review summary and warnings work when geometry estimate exists in spec
- New SVG intake UI (parse status, layer confirm, persist) remains intact
- Empty vector pathway shows fast-ask + review surface without crash

## Tests run

| Command | Result |
|---------|--------|
| `npm run lint` | PASS |
| `vitest run vectorStudioPreview.test.ts Product001IntakeSpecEditor.vectorFastAsk.test.tsx intakeReadinessStages.partialSpec.test.ts svgIntakeFlow.test.ts VectorIntakeFastAskPanel.test.tsx` | **61 passed** |
| `backend/.venv/Scripts/python.exe -m pytest …` | **Not run** — pytest not installed in venv |

## Remaining risk

Low. Typo was isolated to one function; no schema or API changes. Recommend adding ESLint `no-undef` coverage if not already enforced on TS (TypeScript should catch this — investigate why it slipped through CI).

## Manual verification

After fix, `http://127.0.0.1:3000/intake/WI-E2E-COMMERCIAL-WARN-001` renders volumetric intake workspace (Specificație / Simulare ofertă tabs visible).
