# STABILIZE — Analyzer change policy and PBL regression gate

## Purpose

Establish a mandatory regression matrix for any SVG analyzer / layer classification change. PBL is the canonical stable fixture; Ana Maria layered/unlayered cover mixed vector/raster pseudo-layer paths.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base remote: `d93df06`
- Pseudo-layer feature: `9488e2c` (regressed PBL without guard)
- Guard fix: `36070df` (fallback-only preserve for multi-layer Corel exports)

## PBL audit (9488e2c vs guarded HEAD)

| Check | Validated baseline | `9488e2c` (broken) | Guarded HEAD |
|-------|-------------------|-------------------|--------------|
| Layer structure | 3 Corel `Layer_x0020_*` | 2 pseudo color layers | 3 Corel preserved |
| Child parts | 11 | 10 | 11 |
| Real letters | 10 | null | 10 |
| Face area m² | ≈ 0.691 | altered | ≈ 0.691 |
| LED perimeter m | ≈ 11.63 | altered | ≈ 11.63 |
| CNC face perimeter m | ≈ 13.62 | altered | ≈ 13.62 |
| Holes / contours | 5 / 15 | altered | 5 / 15 |
| Image child parts | 0 | — | 0 |
| Confirm all | complete | blocked | complete |

Regression was **structural and computational** (not label-only): pseudo regrouping changed layer assignment, child parts, and quote geometry.

## Regression matrix

| # | Fixture / test | Assert |
|---|----------------|--------|
| 1 | `svgAnalyzerRegressionGate.test.ts` → PBL | Metrics + child parts + no pseudo layers |
| 2 | `svgAnalyzerRegressionGate.test.ts` → Ana layered | 6 layers, 4 face, 2 artwork, confirm complete |
| 3 | `svgAnalyzerRegressionGate.test.ts` → Ana unlayered | 6 pseudo/raster, confirm complete |
| 4 | `test_intake_v4_layer_finish_pricing_matrix.py` | Layer finish pricing unchanged |
| 5 | `test_intake_v4_oracal_641_651_pricing.py` | Owner Oracal guard unchanged |

Additional coverage: `pblLayereChildParts.regression.test.ts`, `pblLayerePseudoLayerGuard.test.ts`, `ana-maria-layer-roles.test.ts`, `intakeV4LayerRoleDisplay.test.ts`.

## Files changed (this build)

| Area | Files |
|------|-------|
| Gate test | `frontend/src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts` |
| Guard | `pseudoLayerExpansionGuard.ts`, `semanticAndPseudoLayerExpansion.ts` |
| PBL tests | `pblLayerePseudoLayerGuard.test.ts`, `pseudoLayerExpansionGuard.test.ts` |
| Policy | `docs/architecture/SVG_ANALYZER_REGRESSION_GATE_POLICY.md` |
| QA | this file |

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/lib/intakeV4/intakeV4LayerRoleDisplay.test.ts

cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_layer_finish_pricing_matrix.py tests/test_intake_v4_oracal_641_651_pricing.py -q
```

Record PASS/FAIL in commit or PR notes before declaring analyzer work green.

## Boundary

- Analyzer classification + regression gate only
- Full PASS requires `docs/qa/STANDARD_CONFIRMATION_CHECKLIST_FOR_INTAKE_V4_ANALYZER_BUILDS.md`
- No quote/order/tasks, ExecutionPlan, tasks_json, stock consumption
- No Pricing Registry, Color Registry, CostEngine, employee assignment changes
- No push without PBL + Ana Maria PASS (automated + UI smoke)

## UI smoke (manual)

1. `pbl-layere.svg` — 10 real letters, face ≈ 0.691 m², roles confirmable
2. `ana-maria-gradinita.svg` — 6 rows, 4 face, 2 artwork, confirm complete
3. `ana-maria-gradinita-fara-layere.svg` — 6 rows, 4 pseudo face, 2 raster, confirm complete

## Next steps

- Run UI smoke when dev stack is up before push
- Reference `docs/architecture/SVG_ANALYZER_REGRESSION_GATE_POLICY.md` in future analyzer PRs
