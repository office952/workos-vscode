## Audit Finding

Frontend Review and backend runtime were using different PSU allocation policies for the same required wattage on `IR-MRBMAK7Z`.

- Review `Detalii calcul LED`: `160W + 60W + 60W`
- Backend runtime / Calcul live: `200W + 100W`

## Canonical Policy Chosen

Use backend policy as canonical:

1. fewer PSUs first
2. then lower spare capacity
3. then larger max PSU if still tied

Reason: fewer power supplies usually mean simpler mounting and wiring in production.

## Files Changed

- `frontend/src/lib/psuAllocation.ts`
- `frontend/src/lib/intakeV6/intakeV6LedLighting.test.ts`

## Tests Run

- `npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/intakeV6LedLighting.test.ts`
  - Result: `7 passed`

## Runtime Before / After

Before:

- Review `Detalii calcul LED`: `Surse: 160W + 60W + 60W`
- Backend runtime already used: `200W + 100W`

After:

- Review `Detalii calcul LED`: `Surse: 200W + 100W`
- Backend runtime still uses: `200W + 100W`
- `Calcul live` remains:
  - parent `Sursa LED 12V` -> `2 buc` -> `67.2 EUR`
  - child rows `MAT-LED-PSU-12V-200W x1`, `MAT-LED-PSU-12V-100W x1`

## Forbidden Scope Confirmation

- No LED formula change
- No PSU reserve formula change
- No pricing rate change
- No Quote / Order / Execution work
- No DB / seed / migration work
- No parked untracked lane staging