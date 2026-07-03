# FIX_INTAKE_V4_GRADINITA_UI_METRIC_SEMANTICS_AND_CANT_VISIBILITY

**Build:** `FIX_INTAKE_V4_GRADINITA_UI_METRIC_SEMANTICS_AND_CANT_VISIBILITY`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Scope:** Intake V4 operator UI — geometry metric labels, count semantics, cant visibility, Material Breakdown pending messaging.  
**Non-goals:** geometry algorithm changes, CostEngine, Pricing Registry, quote/order/tasks.

---

## Context

Audit `AUDIT_INTAKE_V4_ANA_MARIA_GRADINITA_ELEMENT_BY_ELEMENT_GEOMETRY_AND_UI` confirmed:

- Layer-sum volumetric letters perimeter matches Corel (26.747208 m vs 26.747203 m).
- UI showed LED exterior (20.8795 m) without Corel-comparable label.
- UI showed 19 as “litere” without explaining production subpath parts.
- Cant/volum conflated with LED or hidden until Review/analysis-bundle persist.
- Material Breakdown empty without explicit operator message.

---

## UI before / after

### Counts

| Before | After |
|--------|-------|
| `Litere / piese reale: 19` | `Grupuri volumetrice: 4` · `Piese producție: 19` · `Caractere text: n/a` · `Artwork/logo: 2` |
| No soare note | `Soare = piesă volumetrică / emblemă face` |

### Perimeters

| Before | After |
|--------|-------|
| Primary: `Perimetru LED litere / exterior` | Table with labeled sources: |
| CNC/cant in secondary grid only | `Corel curve length / layer-sum` · `LED exterior only` · `CNC cut perimeter` · `Cant / return material perimeter` · `Artwork logo perimeter` (raster n/a) |

### Cant / volum

| Before | After |
|--------|-------|
| Optional row in contour breakdown, often equal to LED | Dedicated `Cant / volum litere` section: depth, finish, source, calculated perimeter |
| No pending explanation | Pending message when analysis-bundle or finish save missing |

### Material Breakdown

| Before | After |
|--------|-------|
| Empty / “indisponibil” | Explicit: *Material Breakdown nu este complet încă. Salvează Review/Setări…*

---

## Metric definitions (operator)

| Label | Source | Ana Maria unlayered |
|-------|--------|---------------------|
| Corel curve length / layer-sum | Sum `perimeterMl` on confirmed/auto **face** layers | ~26.747 m |
| LED exterior only | `led_perimeter_ml` / parts outer | ~20.880 m |
| CNC cut perimeter | `cutting_perimeter_ml` | ~23.713 m |
| Cant / return material | `return_material_perimeter_ml` (enriched after finish) | ~20.880 m pre-finish; ~23.713 m after finish+inner |
| Artwork raster | No vector perimeter when `raster_artwork` | n/a |

**Corel vs app:** Corel “Length of curve” on letter fills ≈ layer-sum. LED/CNC/cant are production metrics — never compare LED to Corel without labels.

---

## Files changed

- `frontend/src/lib/intakeV4/intakeV4GeometryMetricDisplay.ts` (new)
- `frontend/src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts` (new)
- `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.test.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx`
- `docs/qa/STANDARD_CONFIRMATION_CHECKLIST_FOR_INTAKE_V4_ANALYZER_BUILDS.md`

---

## Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/ana-maria-corel-perimeter-diagnostic.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4GeometryPanel.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4LayerRoleDisplay.test.ts
$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-corel-reference-perimeter-smoke.spec.ts
```

---

## Remaining gaps

- Character count from curve-converted text remains **n/a** (no OCR/tracing).
- Material Breakdown full rows still require analysis-bundle persist (by design).
- Priced cant perimeter (waste/registry) only after MB with persisted payload.

---

## Boundary

No changes to: nest2 geometry algorithms, CostEngine, Pricing Registry, Color Registry, quote/order/tasks, ExecutionPlan, stock.
