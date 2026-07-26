## TASK

INTAKE_V6_LAYER_ROLE_DROPDOWN_OWNER_TAXONOMY_FIX_V1

## HEAD before work

- `6527ac2`

## Safety state

- `git status -sb`: no staged files; tracked modifications already existed from the current positional-logo-label slice
- `git diff --cached --name-only`: empty
- `git status --short --untracked-files=no`: tracked modified files were limited to the active Intake V6 logo-labeling slice

## Root cause

- The operator-facing selector in [frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx) reused the broad role taxonomy instead of a strict owner-only dropdown.
- The broad options came from [frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts) through `getIntakeV6RoleOptionsForLayer(...)`.
- The old narrowing depended on `ownerRoleTaxonomyActive`, which only became true in mixed letters+logo contexts. Single-logo contexts fell back to the grouped global role list, so `Vinil aplicat`, `Ignora strat`, `De confirmat`, `Cant / volum`, `Spate / backing`, and similar roles reappeared.

## Fix summary

- Added an explicit owner-only dropdown option list in [frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts):
  - `face` -> `Vector Litere`
  - `printed_artwork` -> `Vector Logo`
- Added `normalizeIntakeV6OwnerSelectableRole(...)` so legacy/internal states like `vinyl`, `unknown`, or other non-owner roles normalize safely to one of the two operator roles.
- Updated `LayerRoleSelect` in [frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx) to render only those two owner-safe options.
- Kept the rest of the broader taxonomy helper intact for non-dropdown/internal contexts.
- Preserved neutral display labels such as `Logo 1`.

## Files changed for this task

- [frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx)
- [frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx)

## Tests run

- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts --reporter=verbose`
  - PASS
- `git diff --check`
  - PASS

## Visual verification

- Route checked: `http://127.0.0.1:3000/intake-v6/0cfafcb6-ea95-4ff5-9799-bbd88b24bf71/operator`
- Step checked: `Straturi`
- Verified current `Rol producție` combobox accessibility/options show only:
  - `Vector Litere`
  - `Vector Logo`
- Verified selected logo-layer value is `Vector Logo`
- Verified `Logo 1` neutral label remains in:
  - `Decizii straturi`
  - `Compoziție produs propusă`
  - `Atenție analiză`
- No old/global roles were visible in the current operator dropdown snapshot.
- No mutating workflow actions were triggered.

## Forbidden scope confirmation

- No Pricing changes
- No Quote/Order changes
- No Execution changes
- No ProductAggregate / TaskGraph / ExecutionPlan changes
- No DB / seed / migration work
- No Logo offerability activation
- No component root / quote rule changes