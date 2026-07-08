# Calcul Live PSU Child Rows Visibility V1

Date: 2026-07-08

## Owner issue

Owner reported that Intake V6 `Calcul live` still looked regressed for PSU composition even though the backend was already returning the split PSU rows.

Observed UI behavior before fix:
- parent row `Sursa LED 12V` stayed visible
- details mode showed only `child rows: 2`
- the actual PSU split lines remained hidden in the UI

## Root cause

The frontend logical-list renderer already received `child_rows`, but `IntakeV6LiveCalculationSummary` flattened them into:
- `childCount`
- technical detail strings

It never preserved structured child row display data for rendering in the technical-details block.

## Fix applied

Frontend-only narrow fix in `Calcul live`:
- keep parent quantity and subtotal unchanged
- keep child split hidden when `Afișează detalii tehnice` is off
- render generic `child_rows` entries when technical details are on
- keep the rendering generic instead of hardcoding a workspace or PSU-only branch

For PSU rows, the runtime now surfaces:
- `Sursa 12V 100W · 1 buc · 19,20 EUR`
- `Sursa 12V 200W · 1 buc · 48,00 EUR`

No backend, DB, pricing, quote, order, execution, or Product System contract changes were made.

## Files changed

- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `docs/worklog/realignment/2026-07-08_calcul_live_psu_child_rows_visibility_v1.md`

## Commands run

Focused test:

```powershell
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
```

Result:
- PASS
- 24 tests passed

## Runtime proof

### `/intake-v6/IR-MRBMAK7Z/operator`

Verified in the running browser session:
- `Calcul live` still shows parent row `Sursa LED 12V`
- parent quantity remains `2 buc`
- parent subtotal remains `67,20 EUR`
- enabling `Afișează detalii tehnice` now reveals two child rows
- child rows show `Sursa 12V 100W` and `Sursa 12V 200W`
- no false `BLOCAT` badge was introduced for the PSU row in this proof

### `/product-system`

Rechecked parity surface in the running browser session:
- `TPL-VOLUMETRIC-LETTERS_v2` remains `Produs ofertabil` with `Work Intake DA`
- `TPL-VOLUMETRIC-LOGO_v1` remains `In pregatire` with `Work Intake NU`

### `/intake`

Rechecked the already-modified hint modal in the running browser session:
- `Analyzer-first` remains `Recomandat`
- letters card still shows `Product Template`, `Work Intake DA`, `Root direct: permis`, `Activ pentru ofertare`
- logo card still shows `Product Template`, `Work Intake NU`, `Root direct: blocat pana la owner GO`, `Candidat compozitie`

## Boundary

Not touched:
- backend logical-list generation
- pricing / CostEngine
- DB / seeds / migrations
- Quote / Order / Execution flows
- Product System activation or owner GO logic
- Work Intake routing rules