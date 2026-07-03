# SVG analyzer regression gate policy

## Rule

No change to the SVG analyzer, Intake V4 layer classification, pseudo-layer expansion, artwork complexity, or dependent material-breakdown inputs is **PASS** without running the regression gate below and completing the full operator checklist in [`docs/qa/STANDARD_CONFIRMATION_CHECKLIST_FOR_INTAKE_V4_ANALYZER_BUILDS.md`](../../qa/STANDARD_CONFIRMATION_CHECKLIST_FOR_INTAKE_V4_ANALYZER_BUILDS.md).

Pseudo-layer classification must remain **fallback-only**: it must not replace validated Corel layer structure or geometry already extracted from canonical fixtures.

## Mandatory checks before merge

| Gate | Requirement |
|------|-------------|
| A | New or changed fixture behavior verified |
| B | **PBL** (`pbl-layere.svg`) metrics unchanged |
| C | Material breakdown for PBL-relevant paths unchanged (backend tests) |
| D | Layer finish pricing matrix unchanged |
| E | Edge/cant quote paths unchanged |
| F | Raster/image elements excluded from child parts |
| G | Confirm-all auto roles complete on gate fixtures |

## Canonical fixtures

### PBL — stable baseline

`frontend/src/lib/svgAnalyzer/fixtures/pbl-layere.svg`

Expected truth:

- Width ≈ 2700 mm, height ≈ 350 mm
- 10 real letters / 10 letter child parts + 1 artwork layer-as-part (11 total)
- Face area ≈ 0.691 m²
- LED exterior perimeter ≈ 11.63 m
- CNC face perimeter ≈ 13.62 m
- Inner holes = 5, cut contours = 15
- Corel layers `Layer_x0020_1/2/3` — no `pseudo:*` takeover
- Raster artwork not a volumetric child part

### Ana Maria layered

`frontend/src/lib/svgAnalyzer/fixtures/ana-maria-gradinita.svg`

- 6 semantic real layers
- 4 production geometry (face), 2 artwork
- Confirm all → complete

### Ana Maria unlayered

`frontend/src/lib/svgAnalyzer/fixtures/ana-maria-gradinita-fara-layere.svg`

- 6 entities (4 pseudo face + 2 raster artwork)
- Confirm all → complete
- Volumetric letter perimeter ≈ **26.747 m** Corel reference (±5% on layer-sum metric)

### Ana Maria — Corel perimeter reference

`ana-maria-gradinita-fara-layere.svg` vs owner Corel curve lengths:

- Volumetric letters: **26.747203 m** (compare app face-layer perimeter sum)
- Logo curves: **4.891010 m** (compare when vector perimeter available; raster logos → diagnostic skip)
- See `docs/qa/UI_E2E_COREL_REFERENCE_PERIMETER_VALIDATION_ANA_MARIA.md`

Regression matrix (required):

1. PBL baseline
2. Ana Maria layered (6 rows)
3. Ana Maria unlayered (6 pseudo/raster rows)
4. **Corel reference perimeter comparison** (`ana-maria-corel-perimeter-diagnostic.test.ts`)
5. Layer finish pricing matrix (backend)
6. Owner Oracal guard (backend)

## Pseudo-layer fallback policy

```text
IF real semantic six-group letter/logo layers exist:
    preserve real layers
ELSE IF two or more Corel Layer_x0020_N groups already carry drawable geometry:
    preserve existing extraction (PBL guard)
ELSE IF single generic layer with no useful semantic grouping:
    generate pseudo-layers from solid fills + raster logo split
ELSE:
    manual review
```

Implementation: `pseudoLayerExpansionGuard.ts`, `semanticAndPseudoLayerExpansion.ts`.

## Commands

### Frontend regression gate (required)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts
```

Full analyzer matrix (optional but recommended):

```powershell
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/lib/intakeV4/intakeV4LayerRoleDisplay.test.ts

$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-analyzer-regression-gate-smoke.spec.ts e2e/intake-v4-corel-reference-perimeter-smoke.spec.ts
```

### Backend pricing guards (required when touching pricing-adjacent intake paths)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_layer_finish_pricing_matrix.py tests/test_intake_v4_oracal_641_651_pricing.py -q
```

## Scope boundaries

This gate does not replace dedicated builds for quote/order creation, ExecutionPlan, stock consumption, CostEngine, or Pricing/Color Registry changes — those remain protected areas with their own tests.

## Related docs

- `docs/qa/STANDARD_CONFIRMATION_CHECKLIST_FOR_INTAKE_V4_ANALYZER_BUILDS.md` — **mandatory PASS checklist**
- `docs/qa/STABILIZE_ANALYZER_CHANGE_POLICY_AND_PBL_REGRESSION_GATE.md`
- `docs/qa/UI_E2E_COREL_REFERENCE_PERIMETER_VALIDATION_ANA_MARIA.md`
