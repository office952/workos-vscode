# BUILD — Intake V4 Operator UI Trust Alignment

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base audit:** `docs/audit/INTAKE_V4_OPERATOR_UI_COUNTS_HARD_AUDIT.md`

## 1. Problema

UI/API erau aliniate factual, dar terminologia amesteca contoare business cu termeni tehnici (`Child parts`, `Placements`, `nestable`, `bbox`, `candidate_tasks_count`), ceea ce reduce încrederea operatorului.

## 2. Ce s-a schimbat (doar display)

- Vocabular RO unificat în zona principală: **Artwork / logo**, **Goluri / interioare**, **Piese plasate în layout**, **Layere SVG**.
- Contorul **Piese producție** a fost mutat în detalii tehnice ca **Piese vectoriale de producție detectate** (fără OCR).
- **Rezumat lucrare** pe Review și Confirm (fără calcule noi).
- Material review: wording uman (**Arie selectată pentru review**, **Sursă calcul**, **Aplicat în ofertă finală: Nu**).
- Candidați bbox / policy table mutați în accordion **Detalii tehnice**.
- `candidate_tasks_count` (ex. 22 Ana Maria) doar ca **Taskuri candidate dry-run** în detalii tehnice.
- Placeholder curat pentru raster extern lipsă în preview SVG.

## 3. Vocabular UI final (zonă principală)

| Label | Sursă field |
|-------|-------------|
| Artwork / logo | nesting `artwork_parts` / finish artwork |
| Goluri / interioare | `inner_holes_count` |
| Piese plasate în layout | `nestable_parts + artwork_parts` |
| Layere SVG | layer chips / layer count |
| Arie selectată pentru review | `selected_quote_sheet_area_sqm` |
| Aplicat în ofertă finală | `selection.is_applied_to_quote` |

## Ambiguous production part count

The main operator summary no longer displays the numeric production part count because it can be confused with visible text characters.

The technical value remains available as:

**Piese vectoriale de producție detectate**

No OCR is used. The app reports vector geometry, not visible text character count.

## 4. Detalii tehnice (collapsed default)

Piese vectoriale de producție detectate (cu notă anti-OCR), Child parts alias, real_letters_count alias, piese nestable, artwork parts, nesting layouts, bbox metrics, candidate dry-run tasks, pricing/handoff dry-runs, task preview catalog V3.

## 5. Ana Maria — valori așteptate UI

- 2 artwork · 7 goluri · 21 piese plasate · 6 layere SVG (zona principală)  
- 19 piese vectoriale de producție detectate (detalii tehnice)  
- Material review: 1.2638 m² · Neaplicat în ofertă finală  
- 22 doar ca taskuri candidate dry-run (dacă dry-run încărcat)

## 6. PBL — valori așteptate UI

- 1 · 2 · 11 · 3 layere SVG (zona principală)  
- 10 piese vectoriale de producție detectate (detalii tehnice)  
- Material review: 0.6907 m² · Neaplicat în ofertă finală

## 7. Ce NU s-a schimbat

- Calcule geometrie / nesting / material policy  
- `selected_quote_sheet_area_sqm` și sursa `eligible_area_floor`  
- `isAppliedToQuote` (rămâne false)  
- CostEngine, Pricing Registry, Color Registry, quote/order/tasks, stock, ExecutionPlan, tasks_json  
- Re-analysis execution

## 8. Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4SheetQuoteReviewDisplay.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4ConfirmStep.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4OperatorWorkSummary.test.tsx
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4OperatorUiPolish.test.tsx
```

Backend: nu a fost modificat.
