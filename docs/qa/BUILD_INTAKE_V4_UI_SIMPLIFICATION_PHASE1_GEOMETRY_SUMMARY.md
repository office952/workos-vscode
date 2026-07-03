# BUILD — Intake V4 UI Simplification Phase 1 (Geometry Summary)

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base:** `docs/audit/INTAKE_V4_DRASTIC_UI_SIMPLIFICATION_AUDIT.md`

## Scop

Înlocuire `GEOMETRIE QUOTE` din zona principală cu card compact **Dimensiuni și perimetru** (Lățime, Înălțime, Perimetru total vectorial). Panelul complet rămâne în accordion **Detalii tehnice** ca **Geometrie avansată**.

## Fișiere

| File | Change |
|------|--------|
| `IntakeV4OperatorGeometrySummaryCard.tsx` | Nou — summary operator |
| `IntakeV4OperatorGeometrySummaryCard.test.tsx` | Teste |
| `IntakeV4SvgAnalyzerStep.tsx` | Summary în main; GeometryPanel în accordion |
| `IntakeV4ReviewStep.tsx` | Summary în main; GeometryPanel în accordion |
| `IntakeV4GeometryPanel.tsx` | Titlu „Geometrie avansată”; variant accordion |

## Sursă perimetru

`buildIntakeV4GeometryMetricDisplay().corelComparableCurveLengthM` — label UI **Perimetru total vectorial**.

## Ce NU s-a schimbat

Backend, calcule geometrie, nesting, pass-count, CostEngine, quote/order/tasks, stock.

## Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.test.tsx
```

## Verdict

Display-only — ierarhie UI; date tehnice păstrate în accordion.
