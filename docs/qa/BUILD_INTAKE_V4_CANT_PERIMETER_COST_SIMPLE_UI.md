# BUILD — Intake V4 Cant Perimeter Cost Simple UI

## Purpose

Operator-friendly **Cant / volum** card on Intake V4 Review: primary perimeter from vector letter groups (+ emblem when cant active), EUR/ml pricing from material breakdown, cost formula on the main card, per-layer breakdown inside collapsed **Detalii cant**.

## Context

Prior cant UI mixed LED outer perimeter, quote geometry, breakdown priced qty (+20% waste), and operations preview into operator-visible space. Operators need one perimeter truth (Corel-comparable vector sum) and a simple cost line.

**Note:** Layer breakdown structure is intended to feed ProductSystem / task preview later — no task generation in this build.

## Files changed

| Area | File |
|------|------|
| Display helpers | `frontend/src/lib/intakeV4/intakeV4EdgeCantDisplay.ts` |
| Review card | `frontend/src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.tsx` |
| Review step wiring | `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` |
| Tests | `frontend/src/lib/intakeV4/intakeV4EdgeCantDisplay.test.ts` |
| Tests | `frontend/src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.test.tsx` |

**Unchanged (already correct):**

- `resolveIntakeV4OperatorCantPerimeterDisplay()` — primary perimeter source
- `sumActiveLetterGroupCantPerimeterM()` — letter group vector sum
- `buildIntakeV4LiveMaterialsUsedRows()` — cant row uses operator perimeter
- `IntakeV4LiveCalculationSummary` — cant cost from breakdown `return_material`

## Primary perimeter

Sum of volumetric face layers with **active cant** (`return_finish_type` not `none` / `no_return` / etc.) plus emblem layers when cant active. Resolved via:

```text
resolveIntakeV4OperatorCantPerimeterDisplay({ geometryMetrics, geometry, letterGroups, artworkFinishes })
```

Fallback order for letters: `sumActiveLetterGroupCantPerimeterM(letterGroups)` → `corelComparableCurveLengthM`.

**Not used on main card:** LED exterior, quote geometry `return_material_perimeter_ml`, breakdown `priced_quantity` / +20% waste.

## Main card layout

```text
CANT / VOLUM
Perimetru cant total: XX.XX m
Finisaj: …
Adâncime: 60 mm
Preț cant: X.XX EUR/ml  OR  tarif lipsă
Cost cant: XX.XX m × X.XX EUR/ml = Y.YY EUR  OR  indisponibil — tarif lipsă
```

Formula: **Perimetru cant × Preț/ml = Cost cant** (operator perimeter × `return_material.unit_price`).

## Missing tariff behavior (report only)

`return_material` row shows **tarif lipsă** when:

- `price_source === "missing"`, or
- `unit_price` is null/undefined

In local dev this is common: aluminum cant registry rate for `return_material` may not be seeded in owner pricing tables. Frontend does **not** invent rates — it reads breakdown only.

Breakdown may still expose `base_quantity`, `priced_quantity`, and +20% waste for quote geometry scope; those stay inside **Detalii cant** debug rows.

## Detalii cant (accordion, default closed)

1. **Per layer** — letter groups (all layers; inactive → "fără cant"); emblem layers only when cant active
2. **Totals** — Total litere, Total emblemă cu cant, Total cant
3. **Debug / backend** — LED exterior, quote geometry, breakdown cant, priced qty + waste, adeziv, Oracal wrap, operations preview

## Calcul live / Materiale folosite

- **Cant row (Calcul live):** `estimated_cost` from `return_material` when present; else "tarif lipsă"
- **Materiale folosite — Cant / volum:** operator perimeter (e.g. 26.75 m), not breakdown priced qty (e.g. 25.17 m with waste)

## Boundary

- **No backend** changes
- **No CostEngine** changes
- **No ProductSystem** / task generation changes
- Frontend display + tests only

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.test.tsx `
  src/components/workos/intake-v4/IntakeV4LiveCalculationSummary.test.tsx `
  src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts `
  src/lib/intakeV4/intakeV4EdgeCantDisplay.test.ts
```

_(Fill PASS/FAIL after run.)_

**Result:** PASS — 18/18 tests (4 files), 2026-06-24.

## Next steps

- Seed dev registry rate for `return_material` if operators need non-missing cant price in local QA
- Wire `buildIntakeV4EdgeCantLayerBreakdown` into ProductSystem task preview when that build starts
