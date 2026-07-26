# Build — Intake ACM panel-alone element needs teaching v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Boundary** | UI/capture honesty only; no new adhesive/frame rates; no Form System ACM-root |

## Problem

Intake amesteca cerințele VL (Față/Cant/Adeziv/LED) cu oferta panou ACM singur. Operatorul nu știa ce cere fiecare element.

## Fix

Un singur flag `support_only` / ACM-only propagat pe:

1. **Offer Scope panel** — înlocuiește checkboxes Față/Cant/LED cu „În scope / Nu se cere”
2. **Sold-scope visibility** — FACE/CANT/BACK/LED = false (nu mai cere finish litere)
3. **Review chip + Montaj** — scope „Panou Alucobond · fără litere”; ascunde cluster montaj comercial VL
4. **Live calc** — `suppressLetterCantChrome` (fără perimetru cant / artwork-only banner)
5. **Confirm summary** — rezumat ACM, fără adeziv cant litere

## Fix follow-up (JSX parse)

`IntakeV6ReviewStep` montaj ternary needed a Fragment (`<>…</>`) around commercial +
fundal/advanced siblings — without it Vite failed: `Expected ")" but found "className"`.

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vite build
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV6/acmPanel/acmPanelOnlyComposition.test.ts `
  src/lib/intakeV6/intakeV6SoldScopeVisibility.test.ts `
  src/components/workos/intake-v6/IntakeV6OfferScopePanel.test.tsx
```
