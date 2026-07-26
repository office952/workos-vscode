Purpose

- Normalize live calculation badge semantics so missing price, explicit gaps, partial trace, split runtime, and missing quantity are not collapsed into the same operator-facing label.

Audit Finding

- `IntakeV6LiveCalculationSummary` mixed real missing pricing with technical gaps, partial trace, and split-runtime statuses under generic diagnostic labels.

Files Changed

- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx
- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx

Behavior Adjusted

- `Lipsa cantitate` remains only for invalid or missing quantity.
- `Fără tarif` remains only for missing price/cost cases.
- `Gap explicit` is surfaced when explicit `gaps[]` exist and value still exists.
- `Trace partial` is reserved for partial trace states.
- `Fallback` is reserved for fallback-driven rows.
- `SPLIT_IN_RUNTIME` remains explicit as status instead of being conflated with missing pricing.

Tests Run

- `npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- Result: `22 passed`

Runtime Route Checked

- `http://127.0.0.1:3000/intake-v6/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/operator`

Runtime Outcome

- `Logo 1` and `Logo 2` still show `Confirmat in Pasul 1`.
- Valid priced rows remain `PRICED`.
- Explicit gap rows surface `GAP EXPLICIT` instead of `Fără tarif`.
- Totals remained unchanged.

Forbidden Scope Confirmation

- No backend behavior changes.
- No pricing logic changes.
- No Quote/Order changes.
- No Execution changes.
- No DB/seed/migration changes.
- No Logo root activation.
- No untracked parked lane usage as authority.