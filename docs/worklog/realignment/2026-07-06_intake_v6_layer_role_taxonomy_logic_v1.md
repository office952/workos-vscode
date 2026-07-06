# 2026-07-06 - Intake V6 Layer Role Taxonomy Logic V1

## Scope

Controlled implementation + documentation for owner-facing layer role taxonomy in Intake V6.

## Git Gate

- branch: `main`
- HEAD before commit: `5c3c50e`
- staged state: none
- dirty state relevant:
  - `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts`
  - `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts`
  - `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6ConfirmOperationalSummary.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.tsx`
  - `WORKOS_STEP1_LAYER_ROLE_OWNER_TAXONOMY_2026-07-06.md`

## Owner Decision

Only two owner-facing roles for volumetric letters + logo context:

- Vector Litere
- Vector Logo

## Runtime Context

Canonical file:

- `C:\Users\offic\workos_app_vs\fisiere-teste-svg\gradi-curat.svg`

Workspace:

- `IV6-0EFC6C31`
- `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator?t=owner-taxonomy-v1`

Expected composition:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`

## What Changed

- Contextual role options now activate when the Step 1 table detects both target templates:
  - `TPL-VOLUMETRIC-LETTERS_v2`
  - `TPL-VOLUMETRIC-LOGO_v1`
- The Step 1 dropdown is flat for this context.
- The owner-facing label for logo layers is `Vector Logo`.
- Review / Confirm / WorkSummary owner-facing labels were aligned to `Vector Logo`.
- A regression test covers the path where `workspaceTemplateCode` is missing but the layer target templates still establish the Letters + Logo context.

Files changed:

- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.test.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ConfirmOperationalSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.tsx`

## UI Verification

Runtime verification:

- Layer 1-4 selected: Vector Litere;
- Layer 5-6 selected: Vector Logo;
- all 6 dropdowns contain exactly:
  - Vector Litere
  - Vector Logo;
- optgroups: none;
- no Vector Atipic;
- no Vector Atipic / logo;
- no global list;
- composition unchanged.

## Tests

- `IntakeV6LayersRoleTable.test.tsx` PASS, `6 passed`;
- `IntakeV6LayersRoleTable + IntakeV6ArtworkFinishSection` PASS, `19 passed`;
- required helper batch PASS, `22 passed`;
- `git diff --check` PASS;
- `git diff --cached --check` PASS.

## Boundaries

Confirmed:

- analyzer untouched;
- templates untouched;
- Product Truth schema untouched;
- ProductDefinition untouched;
- pricing untouched;
- nesting/material untouched;
- Quote/Order untouched;
- Execution/TaskGraph/ProductAggregate untouched;
- DB/seed/migration untouched.

## Documentation

Created:

- `docs/architecture/product-system/INTAKE_V6_LAYER_ROLE_TAXONOMY_CONTRACT.md`

## Remaining Risks

- The global/legacy role list remains in helper code for other contexts.
- Internal legacy values may still exist but must not leak as owner-facing labels.
- Pas 2 logical list/material/nesting is separate backlog.

## Next Step

After commit:

- continue with realignment audit or Pas 2 logical list only after owner GO.