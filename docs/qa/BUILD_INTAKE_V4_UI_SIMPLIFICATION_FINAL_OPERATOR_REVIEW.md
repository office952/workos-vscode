# BUILD — Intake V4 UI simplification final operator review

## Purpose

Final UX cleanup pass on Intake V4 Review before Phase 2 (Face/Back compact card) commit. Transform Review from debug-heavy screen into operator-facing volumetric form.

## Boundaries (confirmed)

- **Backend:** not modified
- **ProductSystem:** not modified
- **CostEngine:** not modified
- **pass-count:** not modified
- **full vector perimeter (`getFullVectorPerimeterM` / commit `e719846`):** not modified
- **No runtime hardcoded numeric values** — all metrics from analyzer/geometry/breakdown APIs

## UI principal (operator) — after declutter pass

Ordine fixă, fără mesaje tehnice:

1. **Dimensiune lucrare** — L/H/perimetru vectorial (fără footnote)
2. **Finisaje litere** — față + cant per strat, fără arie/P per strat în header
3. **Cant — perimetru total** — doar valoarea mare; breakdown în accordion
4. **Emblemă** — print+laminare, fără paragrafe explicative
5. **Iluminare** — perimetru + decizii LED; module/PSU în accordion
6. **Spate litere** — un singur select (fără prose CNC)
7. **Fișiere proiect** — sloturi simple
8. **Salvare** — footer sticky separat
9. **Calcul live** — sidebar sticky

## Eliminated from main UI (this pass)

- CNC față/spate draft summary card
- ProductSystem / rezumat / AI / artwork complexity / breakdown
- Mesaje helper în finisaje (plexi tăiat, rolă, etc.)
- Setări globale fallback (mutat în detalii tehnice)
- Readiness status (mutat sub detalii tehnice)
- Prose backing/emblemă separată (emblemă lighting integrat în Iluminare)

## Mutat în detalii tehnice

- ProductSystem binding
- Rezumat lucrare tabelar
- AI semantic assist
- Artwork complexity (accept/override vechi)
- Material breakdown complet + footprint manual
- Geometrie avansată
- Face/Back CNC draft panel complet
- Cant breakdown (calculat / pentru preț / operații)
- Detalii calcul LED (module, PSU, consum)
- V3 dry-run, pricing preview, handoff, task generation, commercial spine
- Task preview V3 catalog (banner: preview temporar până la ProductSystem)

## Implementări cheie

### Oracal nearest color
- `frontend/src/lib/intakeV4/intakeV4NearestOracalColor.ts`
- Aplicat la `deriveLetterGroupsFromAnalyzer` și `mergeLetterGroupFinishes`

### Copy cant to all
- Buton pe primul strat în `IntakeV4LetterGroupFinishesSection`

### Cant perimeter display
- UI principal: `geometryMetrics.cantReturnPerimeterM` → `quote_geometry.return_material_perimeter_ml`
- Breakdown `calculatedCantM` (~20.97 m pe fixture Ana Maria) rămâne în accordion — poate reflecta scope breakdown backend parțial vs geometry; **fix backend necesită confirmare** dacă trebuie aliniat la ~26.747 m production face

### LED perimeter
- UI principal: `geometryMetrics.ledExteriorPerimeterM` (~20.88 m exterior) — by design pentru module pe contur exterior
- Diferit de full vector 31.638 m (include artwork + inner curves)

### Artwork vechi eliminat din principal
- `IntakeV4ArtworkComplexityCard` mutat în detalii tehnice
- `IntakeV4ArtworkFinishSection` simplificat — fără accept/override recomandări

## Strategic note

După stabilizarea formularului și template-ului, **taskurile finale trebuie să vină din ProductSystem / TPL-VOLUMETRIC-LETTERS**, nu din formular.

## Files changed

- `frontend/src/lib/intakeV4/intakeV4NearestOracalColor.ts` (+ test)
- `frontend/src/lib/intakeV4/intakeV4LetterGroups.ts`
- `frontend/src/lib/intakeV4/intakeV4ArtworkFinish.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4LetterGroupFinishesSection.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4ArtworkFinishSection.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4LiveCalculationSummary.tsx` (+ test)
- `frontend/src/components/workos/intake-v4/IntakeV4ProjectFilesPlaceholder.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx`
- Plus uncommitted Phase 2 / footprint files from prior work (separate commits recommended)

## Commands + results

See agent report — targeted vitest runs requested in build spec.

## Next steps

- Confirm commit scope (final pass vs Phase 2 vs footprint UX as separate commits)
- Backend alignment for cant breakdown perimeter if operator expects production-face total in pricing row
- Project file upload backend build
- ProductSystem-owned task preview replacement
