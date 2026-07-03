# BUILD — Intake V4 geometric pseudo-layer classification and 6-layer UI tests

## Purpose

Six semantic entities for Ana Maria Gradinita fixtures: four solid-color volumetric letter groups + two logo artwork groups, with UI/tests for layered and unlayered SVG paths.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD: `d93df06` (artwork complexity + print lamination)
- Fixtures: `ana-maria-gradinita.svg` (6 Corel semantic groups), `ana-maria-gradinita-fara-layere.svg` (generic layer → pseudo expansion)

## Expected six entities

| Entity | Role | Layered (real) | Unlayered (pseudo) |
|--------|------|----------------|---------------------|
| gradinita / orange | face / production geometry | `gradinita` | `pseudo gradinita (orange)` |
| ana / green | face | `ana` | `pseudo ana (green)` |
| maria / blue | face | `maria` | `pseudo maria (blue)` |
| soare / red | face | `soare` | `pseudo soare (red)` |
| logo stânga | printed_artwork | `logo stanga` | `logo stanga` (raster) |
| logo dreapta | printed_artwork | `logo dreapta` | `logo dreapta` (raster) |

## Files changed

| Area | Files |
|------|-------|
| Semantics | `anaMariaLetterSemantics.ts`, `layerNameSemantics.ts` |
| Expansion | `semanticAndPseudoLayerExpansion.ts`, `pseudoLayerExpansionGuard.ts` |
| Roles | `guessLayerAutoRole.ts`, `analyzeLayers.ts`, `analyzeSvg.ts` |
| Display | `intakeV4LayerRoleDisplay.ts`, `intakeV4LayerRoleOptions.ts` |
| UI | `IntakeV4SvgAnalyzerStep.tsx`, `IntakeV4GeometryPanel.tsx` |
| Fixture | `ana-maria-gradinita.svg` (restructured to 6 semantic groups) |
| Tests | `ana-maria-layer-roles.test.ts`, `intakeV4LayerRoleDisplay.test.ts`, `pblLayerePseudoLayerGuard.test.ts`, `pseudoLayerExpansionGuard.test.ts`, `pblLayereChildParts.regression.test.ts` |

## PBL regression guard

Commit `9488e2c` applied color-based pseudo-layer expansion to all mixed SVGs without real six-group semantics. That regressed **`pbl-layere.svg`**: green `#009846` mapped to `pseudo:ana`, cyan `#66C3D0` to a generic fill pseudo-layer, collapsing Corel `Layer_x0020_*` structure and breaking child parts / quote geometry.

**Guard policy (fallback-only):**

1. If six named semantic letter/logo groups exist → use real layers (Ana Maria layered).
2. Else if **two or more** Corel `Layer_x0020_N` groups already carry drawable geometry → preserve structure (PBL).
3. Else → generate pseudo-layers from solid fills + raster logo split (Ana Maria unlayered).

**PBL metrics preserved (regression tests):**

| Metric | Expected |
|--------|----------|
| Child parts | 11 (10 letters + 1 artwork) |
| Real letters | 10 |
| Face area | ≈ 0.691 m² |
| LED perimeter | ≈ 11.63 m |
| CNC face perimeter | ≈ 13.62 m |
| Cut contours | 15 |
| Inner holes | 5 |
| Layers | 3 Corel (`Layer_x0020_1/2/3`), no `pseudo:*` |

Ana Maria layered and unlayered six-entity classification remains green alongside PBL tests.

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts src/lib/svgAnalyzer/analyzer/pseudoLayerExpansionGuard.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/lib/intakeV4/intakeV4LayerRoleDisplay.test.ts
```

**Result:** PASS (18 tests — PBL + Ana Maria layered/unlayered)

## Boundary

- Classification + analyzer UI only — no quote/order/tasks, ExecutionPlan, stock, Pricing/Color Registry, CostEngine, employee assignment.
- No push (local commit only).

## Limitations

- Letter pseudo-layers use solid-fill color heuristics (no OCR for text labels).
- Child letter split may still be pending when paths are combined — geometry panel shows explicit pending message.
- Layered fixture restructured from single `maria` bucket to six semantic groups to match owner contract.

## Runtime smoke (manual)

1. Load `pbl-layere.svg` → 3 Corel layers, 10 real letters, geometry quote ≈ baseline (face 0.691 m², LED 11.63 m, CNC 13.62 m), Confirm all → `complete`.
2. Load `ana-maria-gradinita.svg` → 6 Corel rows, Confirm all → `complete`.
3. Load `ana-maria-gradinita-fara-layere.svg` → 6 pseudo/raster rows, Confirm all → `complete`.
