# FIX — Intake V4 Full Vector Perimeter in Operator Summary

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`

## 1. Problema

Summary-ul operator afișa **26.747 m** ca „Perimetru total vectorial”, dar Corel raportează pentru același fișier (Ana Maria):

```txt
Length of curve: 3,163.8202 cm = 31.638202 m
```

UI folosea `corelComparableCurveLengthM` — suma perimetrelor straturilor **face** (producție), fără artwork/logo vectorial.

## 2. Referință Corel

- **3,163.8202 cm** = **31.638202 m** (curve length total comparabil Corel)

## 3. UI anterior

- **Perimetru total vectorial:** 26.747 m (`corelComparableCurveLengthM` — doar straturi face)

## 4. Diferența explicată

- **26.747 m** = perimetru vectorial producție (layer-sum face)
- **4.891 m** = perimetru artwork/logo vectorial (stroke vector pe logo-uri)
- **26.747 + 4.891 = 31.638 m** ✓ confirmat pe fixture Ana Maria

## 5. Decizie owner

Afișăm **tot perimetrul vectorial al fișierului** în summary, comparabil cu Corel — fără filtrare doar pe roluri de producție.

## 6. Sursă folosită acum

Frontend display helper `buildIntakeV4GeometryMetricDisplay`:

| Câmp | Semnificație |
|------|--------------|
| `corelComparableCurveLengthM` | Perimetru vectorial producție (face) — neschimbat |
| `artworkLogoVectorPerimeterM` | Perimetru artwork/logo vectorial (sau stroke diagnostic vector, fără raster fără contur) |
| `fullVectorPerimeterM` | Sumă: producție + artwork/logo vectorial |
| `getFullVectorPerimeterM()` | Helper pentru summary card |

Summary card: `getFullVectorPerimeterM(metrics)` → label **Perimetru total vectorial**.

Geometrie avansată (accordion): breakdown reconciliere (total, producție, artwork, CNC, LED, cant).

## 7. Confirm no hardcoded runtime values

Componentele afișează doar câmpuri din `metrics`; valorile 26.747 / 31.638 apar doar în teste/fixture.

## 8. Confirm CNC cost rules unchanged

- Face/Back Prep cost draft: neschimbat
- pass-count: neschimbat
- CNC folosește perimetre vectoriale relevante pieselor CNC, nu `fullVectorPerimeterM`

## Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts src/components/workos/intake-v4/IntakeV4OperatorGeometrySummaryCard.test.tsx
```
