# BUILD_INTAKE_V4_ARTWORK_COMPLEXITY_PRINT_LAMINATION_RULES

## Purpose

Add artwork complexity classification for Intake V4 so raster, gradient, or many-color graphics over vector production geometry are recommended as printed vinyl with lamination instead of cut vinyl.

## Context

Branch: `local/integration-pr4-plus-svg-path`

## Files changed

- `frontend/src/lib/svgAnalyzer/analyzer/rasterOverVectorArtwork.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/artworkComplexityAssessment.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/analyzeSvg.ts`, `analyzeLayers.ts`, `types.ts`, `buildOfficialAnalysisJson.ts`, `buildAnalysisReport.ts`
- `frontend/src/lib/svgAnalyzer/fixtures/ana-maria-gradinita.svg`
- `frontend/src/lib/intakeV4/intakeV4ArtworkComplexityDisplay.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4ArtworkComplexityCard.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx`
- `backend/services/intake_v4_artwork_complexity_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/schemas/intake_v4.py`
- `docs/architecture/ARTWORK_COMPLEXITY_AND_PRINT_LAMINATION_RULES.md`

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/rasterOverVectorArtwork.test.ts src/lib/svgAnalyzer/analyzer/artworkComplexityAssessment.test.ts src/components/workos/intake-v4/IntakeV4ArtworkComplexityCard.test.tsx

cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_artwork_complexity.py -q
```

## Boundary

- Classification, preview warnings, operator UI, material/operation preview rows only.
- No quote/order/tasks, ExecutionPlan, tasks_json, stock consumption.
- No Pricing Registry, Color Registry, or CostEngine rewrites.
- No employee assignment.

## Next steps

- Exact mask intersection for print area when prepress infrastructure exists.
- Wire accepted print recommendation into artwork finish execution_type hints.
