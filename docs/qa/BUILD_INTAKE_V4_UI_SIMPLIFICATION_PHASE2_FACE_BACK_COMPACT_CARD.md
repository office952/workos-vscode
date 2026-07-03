# BUILD — Intake V4 UI Simplification Phase 2 (Face/Back Compact Card)

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`

## Scop

Card compact **CNC față/spate — draft intern** în Review main (totals + toggle șanfren). Detaliu complet în accordion via `IntakeV4FaceBackPrepCostDraftPanel` — un singur fetch partajat prin `useIntakeV4FaceBackPrepCostDraft`.

## Fișiere

| File | Change |
|------|--------|
| `useIntakeV4FaceBackPrepCostDraft.ts` | Hook partajat |
| `IntakeV4FaceBackPrepCostDraftSummaryCard.tsx` | Card compact main |
| `IntakeV4FaceBackPrepCostDraftSummaryCard.test.tsx` | Teste |
| `IntakeV4FaceBackPrepCostDraftPanel.tsx` | Acceptă viewModel; toggle doar când standalone |
| `IntakeV4ReviewStep.tsx` | Summary în main + panel în accordion |

## Ce NU s-a schimbat

Backend endpoint, pass-count, calcule cost draft, ProductSystem, CostEngine.

## Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftSummaryCard.test.tsx src/components/workos/intake-v4/IntakeV4FaceBackPrepCostDraftPanel.test.tsx
```
