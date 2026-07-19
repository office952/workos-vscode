# Worklog — Intake V6 Desktop Presentation Reset V1

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Functional baseline:** `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602`  
**Audit commit:** `62308fc0bb8f3b764f22a1ebef8745873b89b481`  
**Owner decisions:** D1–D7 GO  

## Pre-flight

- FE `:3000` · BE `:8003` · `BACKEND_PORT=8003`
- Foreign WIP present — untouched
- Checkpoint: `docs/qa/intake-v6-desktop-presentation-reset-v1-2026-07-19/RESET_CHECKPOINT.md`

## Removed / demoted from L1

- Full-bleed rose banner weight → compact expandable chip
- “Următorul pas este în footer” banner + composition action footer-hint copy
- Duplicate Iluminare contract section (`renderSectionByKey("iluminare")`)
- Montaj floating template fields at top; Product System L1 badge/hash
- Empty inactive Montaj prep/site cards
- Confirmare purpose behind collapsed accordion
- Raw fatal blocker dump on handoff panel
- Persistent autosave success chrome (D1 → sr-only)
- Pricing composition-gate essay → short “confirmă produsul”
- Page1 detached “use footer” handoff hint

## Disclosures reused

- `IntakeV6TechnicalDetailsAccordion` — Diagnostic tehnic (collapsed)
- Confirmare “Recapitulare și diagnostic tehnic” (collapsed)
- Product composition technical details (collapsed by default)
- Commercial adjustments disclosure
- Montaj Avansat / commercial clusters

## Warning channels

| Before | After |
|--------|-------|
| Product badge + local CTA + rose slab + pricing paragraph + footer + drawer | Local CTA + compact chip + footer next action + drawer inventory |
| Page-level Cant amber with letter groups | Local Cant only when letters present |

## Nesting / width

- Finisaje / Montaj shells compact; Fundal `order-1` when ACM
- Decision + pricing rail grid retained; tab content starts earlier

## Tests

```
vitest: ConfirmStep, HandoffPanel, Composition, BlockerBanner, LiveCalc, FinalConfirmationBlockers, QuoteHandoffReadiness
72 passed
```

## Runtime

ACM `854fbb73-2329-4ee2-b9a0-21158f8eb1b9` · simple `6fcdb7e7-b9b8-4249-9c77-b270a6c34f2f`  
Screenshots under `docs/qa/intake-v6-desktop-presentation-reset-v1-2026-07-19/screenshots/`

## Remaining visual debt

- Global header “Stare sistem: necesită verificare” still dominates chrome (not Intake-owned)
- Footer dual bars still consume height
- Confirmare status rose slab remains assertive when blocked (truthful, not quiet)
- Some drawer info rows still technical (`canonical_unresolved_warning:…`)
- Montaj still denser than Finisaje for ACM

## Owner acceptance

`PENDING_OWNER_VISUAL_ACCEPTANCE`
