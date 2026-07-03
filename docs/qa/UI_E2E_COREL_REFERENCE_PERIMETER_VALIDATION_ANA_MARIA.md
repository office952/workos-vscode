# UI/E2E — Corel reference perimeter validation (Ana Maria)

## Purpose

Validate Ana Maria Grădiniță SVG geometry against owner CorelDRAW curve-length measurements, with operator-friendly mismatch diagnostics when deltas exceed tolerance.

## Corel reference (owner)

| Metric | Corel value |
|--------|-------------|
| Litere volumetrice | 26.747203 m (2674.7203 cm) |
| Logo-uri | 4.891010 m (489.1010 cm) |
| Total brut litere + logo | 31.638213 m |

Fixture: `frontend/src/lib/svgAnalyzer/fixtures/ana-maria-gradinita-fara-layere.svg`

## Expected interpretation

| Group | Role |
|-------|------|
| gradinita, ana, maria, soare | Față litere / geometrie volumetrică |
| logo stânga, logo dreapta | Artwork / print / autocolant |

Comparison:

- **Volumetric letters (app)** = sum of confirmed `face` layer perimeters → compare to **26.747203 m**
- **Logo perimeter (app)** = sum of artwork layer vector perimeters; raster logos may be **null** → report `logo_excluded_as_artwork`
- **UI LED perimeter** = exterior letter perimeter (parts outer path), typically **lower** than Corel total curve length on fills

## Application metrics (HEAD diagnostic run)

| Metric | Value | Notes |
|--------|-------|-------|
| Volumetric letters (layer sum) | 26.747 m | Δ ≈ 0.00002% vs Corel |
| LED exterior (quote UI) | 20.88 m | Exterior only |
| CNC face | 23.71 m | Includes inner cuts |
| Document total vector | 36.24 m | All paths including logo strokes |
| Logo vector perimeter | null | Raster artwork layers |

## Tolerance

- **PASS:** ±5% on volumetric letters perimeter
- **PASS with warning:** ±10% with documented mismatch reason
- Logo: skip numeric compare when raster; must report reason

## Mismatch reason taxonomy

See `corelAnaMariaReference.ts` — e.g. `app_uses_exterior_perimeter_only`, `logo_excluded_as_artwork`, `path_flattening_tolerance_difference`.

## Tests

| Test | Path |
|------|------|
| API diagnostic | `ana-maria-corel-perimeter-diagnostic.test.ts` |
| Regression gate | `svgAnalyzerRegressionGate.test.ts` (Corel row) |
| UI smoke | `e2e/intake-v4-corel-reference-perimeter-smoke.spec.ts` |

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts
$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-corel-reference-perimeter-smoke.spec.ts
```

## PASS / HOLD

- **PASS:** 6 layers, confirm complete, volumetric letters within ±5% (or ±10% with reason)
- **HOLD:** UI smoke not run, or letters delta > 10% without explained taxonomy

## Boundary

Diagnostic / test only — no quote/order/tasks, ExecutionPlan, stock, Pricing/Color Registry, CostEngine changes.
