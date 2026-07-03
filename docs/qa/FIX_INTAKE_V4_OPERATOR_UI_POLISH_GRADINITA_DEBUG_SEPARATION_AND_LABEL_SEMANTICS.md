# FIX_INTAKE_V4_OPERATOR_UI_POLISH_GRADINITA_DEBUG_SEPARATION_AND_LABEL_SEMANTICS

**Build:** `FIX_INTAKE_V4_OPERATOR_UI_POLISH_GRADINITA_DEBUG_SEPARATION_AND_LABEL_SEMANTICS`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Boundary:** UI/UX display only — no geometry formulas, CostEngine, Pricing/Color Registry, quote/order/task creation, ExecutionPlan, tasks_json, or stock consumption.

## Purpose

Polish Intake V4 operator review UI for mixed vector/raster artwork (Ana Maria gradiniță fixture) by separating operator-facing summaries from technical debug, fixing label semantics, units, and contradictory readiness wording.

## Before / after (operator UI)

| Area | Before | After |
|------|--------|-------|
| Layer IDs | `_2209257786352` in operation/material labels | `logo dreapta` / `logo stânga` / `artwork layer` |
| Units | `25.02 ml` for CNC/cant/cablu | `25.02 m`; adeziv stays `ml` |
| CNC section | Print/laminare mixed under CNC | Separate **Operații print / laminare / colantare** |
| Cant label | `…litere + interioare + artwork` | `Cant / volum litere — exterior + interioare eligibile` + artwork exclusion subtext |
| Material total | `Total estimat materiale (ofertă)` | `Estimare internă materiale — informativ` + QuoteWizard disclaimer |
| Readiness | `ready_for_quote_preview` + `QUOTE_HANDOFF_BLOCKED` raw | Three-line status: preview / handoff / task generation |
| Task preview | Verbose English debug inline | Compact Romanian list + `Detalii tehnice taskuri` accordion |
| Logo preview | Browser broken image icon | Controlled banner + placeholder overlay |
| Warnings | Duplicate raster messages, debug keys inline | Grouped: Atenție operator / ofertare / debug (collapsed) |

## Moved to debug accordion (`Detalii tehnice / debug`)

- Nesting trace full detail
- Pricing adapter payload / `operation_rows` raw
- Task dry-run verbose (dependencies, mapping gaps, dryrun_task_key)
- Raw internal warnings (`mapping_gap`, `missing_client_analysis_hash`, `dossier_priced_operation_split`)
- Internal layer IDs (`ID intern: _220…`) when needed for audit

## Key files

- `frontend/src/lib/intakeV4/intakeV4OperatorUiDisplay.ts` — labels, units, warning grouping, readiness helpers
- `frontend/src/components/workos/intake-v4/atoms/IntakeV4TechnicalDetailsAccordion.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ReviewStep.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionTaskDryRunPanel.tsx` — compact operator mode
- `frontend/src/lib/intakeV4/intakeV4QuoteHandoffReadiness.ts` — Romanian handoff labels

## Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4OperatorUiDisplay.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4OperatorUiPolish.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4GeometryPanel.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4ArtworkComplexityCard.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4QuoteHandoffReadiness.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4ConfirmStep.test.tsx
$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-corel-reference-perimeter-smoke.spec.ts
```

## Remaining limitations

- Logo area estimates may still be marked **nesigură** when external raster + clipPath/transform — no geometry formula change in this build.
- Print/laminare pricing may remain `missing_rate` until registry rows exist.
- Full `validate:frontend` still blocked by repo TS debt (~85 errors) — not in scope.
- Runtime visual review on live Ana Maria workspace recommended before push.

## Scope safety

- No geometry algorithm changes
- No quote/order/production task creation
- No ExecutionPlan / tasks_json changes
- No stock consumption
- No Pricing Registry / Color Registry / CostEngine changes
- No employee assignment
