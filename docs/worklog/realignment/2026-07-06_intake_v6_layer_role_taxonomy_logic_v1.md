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
  - `WORKOS_STEP1_LAYER_ROLE_OWNER_TAXONOMY_2026-07-06.md` (root session note; absorbed below and removed 2026-07-16)

## Owner Decision

Only two owner-facing roles for volumetric letters + logo context:

- Vector Litere
- Vector Logo

Absorbed from root session note `WORKOS_STEP1_LAYER_ROLE_OWNER_TAXONOMY_2026-07-06.md` (2026-07-06): operator dropdown taxonomy for Letters+Logo is exactly those two roles; global fallback / `Vector Atipic` / stroke-only labels must not leak into the owner-facing options.

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

## Post-Commit Follow-up: Analysis Panel Alignment

Owner observed after commit `a1a1fef` that the right-side `Atenție analiză` panel was not fully covered by the Step 1 dropdown verification and could still expose technical/analyzer language in the operator warning surface.

Fix applied:

- `Atenție analiză` uses the same owner-facing taxonomy as `Decizii straturi`:
  - Vector Litere
  - Vector Logo
- Technical analyzer messages for pseudo generated layers and stroke-only/logo-artwork candidates are filtered out of the operator-facing warning list.
- The panel explains the analyzer suggestion but points the operator back to `Decizii straturi` for confirmation.
- The Step 1 dropdown logic was not changed.

Focused tests:

- `pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.test.tsx --reporter=verbose` PASS, `2 passed`.
- `pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx --reporter=verbose` PASS, `6 passed`.
- `pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.test.tsx src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx --reporter=verbose` PASS, `8 passed`.
- `git diff --check` PASS.
- `git diff --cached --check` PASS.

UI verification:

- route: `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator?t=20260706-step1`;
- workspace: `IV6-0EFC6C31`;
- SVG: `gradi-curat.svg`;
- current step: `Straturi`;
- `Atenție analiză` shows `Layere propuse ca Vector Litere` and `Layere propuse ca Vector Logo`;
- `Atenție analiză` does not show `Vector Atipic`, `Vector Atipic / logo`, `stroke-only`, `artwork candidate`, or `logo/artwork candidate`;
- dropdowns remain exact owner taxonomy:
  - layers 1-4 selected `Vector Litere`;
  - layers 5-6 selected `Vector Logo`;
  - each dropdown has exactly `Vector Litere`, `Vector Logo`;
  - optgroups: none;
- template composition remains visible:
  - `TPL-VOLUMETRIC-LETTERS_v2`;
  - `TPL-VOLUMETRIC-LOGO_v1`.

Boundaries confirmed:

- analyzer untouched;
- dropdown untouched;
- template mapping untouched;
- Pas 2 logical list untouched;
- Pas 3 untouched;
- pricing/nesting/material untouched;
- Product Truth/ProductDefinition untouched;
- Quote/Order untouched;
- Execution/ProductAggregate/TaskGraph untouched;
- DB/seed/migration untouched.

## Next Step

After commit:

- continue with realignment audit or Pas 2 logical list only after owner GO.