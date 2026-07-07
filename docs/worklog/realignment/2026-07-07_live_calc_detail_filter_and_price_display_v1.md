# Live Calc Detail Filter And Price Display V1

Date: 2026-07-07
HEAD before work: fb4a473

## Safety state

- `git status -sb`: only unrelated untracked files already present in repo
- `git diff --cached --name-only`: empty before work
- `git status --short --untracked-files=no`: empty before work

## Files changed

- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx
- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
- docs/worklog/realignment/2026-07-07_live_calc_detail_filter_and_price_display_v1.md

## What changed

- Added display-only buckets for live calculation rows: included, diagnostic, missing, legacy, excluded.
- Changed the logical-list modal/list to show only included rows in the primary owner-facing list.
- Switched logical-list price/status column to show actual row subtotal when available instead of the word `priced`.
- Kept status as a secondary badge for context.
- Moved non-included rows into a collapsed diagnostic area.
- Kept a dedicated `Fără tarif / diagnostic` tab for inspection without polluting the main list.
- Kept existing breakdown/material/service/labor totals and formulas unchanged.

## Tests run

- `pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx --reporter=verbose`
- `git diff --check`

## Runtime impact

- Frontend/read-model presentation only.
- No backend changes.
- No pricing formula changes.
- No row deletion from source data.
- No new writes.

## Forbidden scope confirmation

- No Pricing rewrite.
- No Product Truth changes.
- No ProductDefinition changes.
- No Quote/Order changes.
- No Execution changes.
- No ProductAggregate changes.
- No TaskGraph changes.
- No ExecutionPlan changes.
- No DB, seed, or migration changes.
- No Logo offerability changes.

## Visual verification instructions

- Open `http://127.0.0.1:3000/intake`
- Open an Intake V6 workspace in Review
- Open `Calcul live — detalii`
- Verify included rows remain in main list
- Verify missing/gap/legacy rows are separated in diagnostics
- Verify the price column shows numeric values where row subtotal exists

## Next recommended slice

- LIVE_CALC_DIAGNOSTIC_REASON_COPY_POLISH_V1