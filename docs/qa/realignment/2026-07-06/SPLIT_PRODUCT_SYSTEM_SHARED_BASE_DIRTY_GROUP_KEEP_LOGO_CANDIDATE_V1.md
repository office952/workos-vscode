# Split ProductSystem Shared Base Dirty Group - Keep Logo Candidate V1

## Verdict

PASS

The ProductSystem shared volumetric UI work is now separated from the incorrect Logo root-offerable assumption.

Commit recommendation: YES, for the strict ProductSystem shared-base UI group only, if the owner wants to commit this group next.

## Scope

- Code changes limited to ProductSystem UI/test files.
- No Intake V6 changes.
- No Pas 1 changes.
- No Pas 2 changes.
- No analyzer changes.
- No Product Truth schema changes.
- No ProductDefinition changes.
- No pricing changes.
- No Quote/Order changes.
- No Execution changes.
- No DB/seed/migration changes.
- No staging.
- No commit.
- No cleanup.

## Git Gate

- branch: `main...origin/main [ahead 20]`
- HEAD: `f75fdb5`
- staged files: `0`
- selected files dirty before fix:
  - `frontend/src/features/product-system/TemplateLibraryView.tsx`
  - `frontend/src/features/product-system/TemplateLibraryView.test.tsx`
  - `frontend/src/pages/ProductSystem.tsx`
- prior audit report status: untracked

## Context Read

- `docs/qa/realignment/2026-07-06/AUDIT_ONE_DIRTY_GROUP_PRODUCT_SYSTEM_SHARED_BASE_AFTER_F75FDB5_V1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`
- `docs/architecture/product-system/LINKED_TEMPLATE_COMPOSITION_CONTRACT.md`
- `docs/qa/form-system-backbone/2026-07-04/PRODUCT_TRUTH_LINKED_SEGMENT_READINESS_V1_QA.md`
- `docs/worklog/realignment/2026-07-04_product_truth_linked_segment_readiness_v1.md`

Contract anchors used:

- `TPL-VOLUMETRIC-LETTERS_v2` remains the current active offerable root / commercial container.
- `TPL-VOLUMETRIC-LOGO_v1` remains candidate and is not active in Work Intake now.
- In the current composition, Logo is linked child / segment only.
- Logo does not create a separate offer, quote, order, component root, or Work Intake root.
- Old logo backing templates must stay hidden from owner-facing active component surfaces.

## What Was Wrong

The dirty group preserved good shared modules UI work, but `TemplateLibraryView.test.tsx` encoded Logo as:

- `quote_offerable: true`
- `status: "offerable"`
- `product_system_role: "offerable_product"`
- `display_group: "active_products"`
- `Work Intake DA`

This contradicted the owner rule and the architecture contracts.

## What Was Preserved

- Shared volumetric modules UI display.
- Shared usage popovers.
- Compact/detailed density behavior.
- Hiding legacy logo backing templates from active component surfaces.
- Components tab as shared component templates rather than duplicated logo backing modules.
- Composition tab showing the six-module shared volumetric base.
- `SharedVolumetricFoundationPanel` as read-only catalog/editor display.
- No pricing, execution, Work Intake exposure, Quote, Order, or runtime activation changes.

## What Was Corrected

### `TemplateLibraryView.test.tsx`

- Changed the Logo fixture to candidate-only:
  - `quote_offerable: false`
  - `status: "not_offerable"`
  - `status_reason: "candidate_linked_child_only"`
  - `product_system_role: "candidate_product"`
  - `display_group: "candidate_products"`
  - `owner_decision_required: true`
- Updated Product view expectations so Logo shows:
  - `In pregatire`
  - `Work Intake NU`
  - profile `logo`
  - shared modules `6/6`
- Updated shared usage popover expectations so Logo shows:
  - `candidate / linked child - Work Intake NU`
  - lighting strategy/profile source still visible as strategy only.
- Updated Composition expectations so Logo shows:
  - `Work Intake: NU`
  - `candidate / linked child / Work Intake NU`
  - shared modules still present.

### `TemplateLibraryView.tsx`

- Candidate bindings now render as `candidate / linked child` instead of plain `candidate`.
- Candidate runtime binding label now reads `candidate / linked child binding`.
- Shared-base composition status now renders `Status: candidate / linked child / Work Intake NU`.
- Generic Work Intake display remains data-driven from `quote_offerable`; the test fixture now supplies the correct Logo value.

### `ProductSystem.tsx`

- Candidate binding label now reads `candidate / linked child binding`.
- Logo shared-profile editor notice now reads `Candidate / linked child only - Not Work Intake`.
- The panel remains read-only display and does not activate ProductAggregate, pricing, Work Intake, Quote, Order, or execution behavior.

## Tests

Command:

```powershell
pnpm.cmd --dir frontend exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=verbose
```

Result:

- PASS
- 1 test file passed
- 13 tests passed

Diff check:

```powershell
git.exe diff --check -- frontend/src/features/product-system/TemplateLibraryView.tsx frontend/src/features/product-system/TemplateLibraryView.test.tsx frontend/src/pages/ProductSystem.tsx
```

Result: PASS, no output.

## UI Verification

Route checked read-only:

```text
http://localhost:3000/product-system
```

Verification method:

- existing browser page navigated to `/product-system`;
- read-only DOM/snapshot inspection;
- no writes, no save, no create, no staging.

Observed:

- Overview:
  - `Letters: offerable`
  - `Logo: candidate / not Work Intake`
  - shared volumetric modules copy says no pricing, execution, or Work Intake activation.
- Produse:
  - `TPL-VOLUMETRIC-LETTERS_v2` shows `Produs ofertabil` and `Work Intake DA`.
  - `TPL-VOLUMETRIC-LOGO_v1` shows `In pregatire` and `Work Intake NU`.
- Componente:
  - shared components display the six shared primary modules.
  - old logo backing component templates are not shown in the shared component list.
- Compozitii:
  - Letters shows shared base and `Work Intake: DA`.
  - Logo shows shared base, `Work Intake: NU`, and `Status: candidate / linked child / Work Intake NU`.

## Commit Readiness

YES, for this strict group only.

Exact files for a future strict commit:

- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.test.tsx`
- `frontend/src/pages/ProductSystem.tsx`
- `docs/qa/realignment/2026-07-06/AUDIT_ONE_DIRTY_GROUP_PRODUCT_SYSTEM_SHARED_BASE_AFTER_F75FDB5_V1.md`
- `docs/qa/realignment/2026-07-06/SPLIT_PRODUCT_SYSTEM_SHARED_BASE_DIRTY_GROUP_KEEP_LOGO_CANDIDATE_V1.md`

Suggested commit message:

```text
fix(product-system): keep logo candidate in shared volumetric catalog
```

Required pre-commit validation:

```powershell
pnpm.cmd --dir frontend exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=verbose
git.exe diff --check -- frontend/src/features/product-system/TemplateLibraryView.tsx frontend/src/features/product-system/TemplateLibraryView.test.tsx frontend/src/pages/ProductSystem.tsx docs/qa/realignment/2026-07-06/AUDIT_ONE_DIRTY_GROUP_PRODUCT_SYSTEM_SHARED_BASE_AFTER_F75FDB5_V1.md docs/qa/realignment/2026-07-06/SPLIT_PRODUCT_SYSTEM_SHARED_BASE_DIRTY_GROUP_KEEP_LOGO_CANDIDATE_V1.md
git.exe status --short -- frontend/src/features/product-system/TemplateLibraryView.tsx frontend/src/features/product-system/TemplateLibraryView.test.tsx frontend/src/pages/ProductSystem.tsx docs/qa/realignment/2026-07-06/AUDIT_ONE_DIRTY_GROUP_PRODUCT_SYSTEM_SHARED_BASE_AFTER_F75FDB5_V1.md docs/qa/realignment/2026-07-06/SPLIT_PRODUCT_SYSTEM_SHARED_BASE_DIRTY_GROUP_KEEP_LOGO_CANDIDATE_V1.md
```

## Do Not Touch

- Backend availability / active-template tests that try to make Logo root offerable.
- WorkIntake routing tests.
- Intake V6 face-finish / roll-width files.
- Intake V6 hydration/footer/module-attention files.
- Product Truth / pre-order technical preview untracked code.
- Pricing, Quote, Order, Execution, ProductDefinition, Analyzer, DB, seed, migrations.
- Bulk untracked docs/screenshots/worklogs.

## Boundaries Confirmed

- no Intake V6 edit;
- no analyzer edit;
- no Product Truth schema edit;
- no ProductDefinition edit;
- no pricing edit;
- no Quote/Order edit;
- no Execution edit;
- no DB/seed/migration edit;
- no staging;
- no commit;
- no cleanup;
- no reset;
- no git clean.

## Roadmap Awareness

- Cat sunt in directia stabilita: `94/100%`
- Main risk: backend dirty tests still contain a separate Logo-root-offerable lane; do not mix them into this frontend ProductSystem UI commit.
- Next safe prompt title: `COMMIT_PRODUCT_SYSTEM_SHARED_BASE_KEEP_LOGO_CANDIDATE_V1`