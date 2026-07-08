Purpose

- Refine Intake V6 Review layout density and reduce badge noise in the main live-calculation list without changing backend behavior or totals.

Owner Observation

- `Compozitie produs propusa` consumed too much vertical space after confirmation.
- `Calcul live` right panel was too narrow for operator review.
- Technical status badges cluttered the main visible list even when `Afiseaza detalii tehnice` was off.

Files Changed

- frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx
- frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx
- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx
- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
- frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx

Before / After

- Product composition panel now collapses when already confirmed and no issues demand attention.
- Collapsed header still shows composition summary, confirmation state, and linked segment count.
- Right review rail for `Calcul live` is wider by roughly 15%.
- Technical-only badges such as `PRICED` and `GAP EXPLICIT` stay hidden from the main row list until technical details are enabled.
- Actionable badges such as `BLOCAT` remain visible in the main list.

Tests Run

- `npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- Result: `27 passed`

Runtime Route Checked

- `http://127.0.0.1:3000/intake-v6/IR-MRBMAK7Z/operator`

Runtime Outcome

- `Compozitie produs propusa` loads collapsed with summary visible and expands to show all previous details.
- Review layout uses a visibly wider `Calcul live` rail.
- With `Afiseaza detalii tehnice` off:
  - `Plexiglas 3 mm` shows only `33,03 EUR`
  - `Forex 10 mm` shows only `35,59 EUR`
  - `Material print Orafol` shows only `1,44 EUR`
- With `Afiseaza detalii tehnice` on:
  - `Plexiglas 3 mm` shows `PRICED`
  - `Forex 10 mm` shows `GAP EXPLICIT`
  - `Material print Orafol` shows `GAP EXPLICIT`
- `Logo 1` and `Logo 2` still show `Confirmat in Pasul 1`.

Forbidden Scope Confirmation

- No backend behavior changes.
- No pricing logic changes.
- No material-breakdown/logical-list/nesting-preview changes.
- No Quote/Order changes.
- No Execution changes.
- No DB/seed/migration changes.
- No Logo root activation.
- No untracked parked lane usage as authority.