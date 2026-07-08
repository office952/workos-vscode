# Audit One Dirty Group - ProductSystem Shared Base After f75fdb5 V1

## Verdict

AUDIT_ONLY / MIXED

This group is not safe as a strict commit candidate yet.

The dirty UI diff has a coherent ProductSystem display direction around shared volumetric modules, hiding legacy logo backing templates, compact density, usage popovers, and shared-base composition cards. However, the tests and mocked availability data also encode `TPL-VOLUMETRIC-LOGO_v1` as `offerable` / `Work Intake DA`, which conflicts with the current architecture contracts and owner direction.

Conclusion: C. Grup amestecat, trebuie impartit in subgrupuri.

## Scope

No code changes.
No staging.
No commit.
No cleanup.

Only this audit report was created.

## Git Gate

- branch: `main...origin/main [ahead 20]`
- HEAD: `f75fdb5`
- staged: `0`
- dirty total: `383`
- tracked modified: `28`
- untracked: `355`

Note: the dirty count is one higher than the prior dirty inventory because `WORKTREE_DIRTY_STATE_INVENTORY_AFTER_F75FDB5_V1.md` is now also untracked.

## Files Audited

| File | Status | Diff size | Area |
|---|---|---:|---|
| `frontend/src/features/product-system/TemplateLibraryView.tsx` | modified | 325-line diff | ProductSystem catalog UI, shared volumetric modules, products/components/compositions |
| `frontend/src/features/product-system/TemplateLibraryView.test.tsx` | modified | 190-line diff | ProductSystem catalog UI tests and mocked availability semantics |
| `frontend/src/pages/ProductSystem.tsx` | modified | 18-line diff | ProductSystem editor/shared foundation panel |

Other ProductSystem-relevant dirty files mentioned by the prior inventory but not included in this audited group:

- `backend/tests/test_active_template_scope.py`
- `backend/tests/test_product_template_availability.py`
- related untracked ProductSystem / QA docs under `docs/`

These are relevant because they also touch Logo offerability semantics, but they were not audited as part of the strict three-file group.

## Context Sources Read

Read:

- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`
- `docs/architecture/product-system/INTAKE_V6_LAYER_ROLE_TAXONOMY_CONTRACT.md`
- `docs/architecture/product-system/GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT.md`
- `docs/qa/realignment/2026-07-06/WORKTREE_DIRTY_STATE_INVENTORY_AFTER_F75FDB5_V1.md`
- `docs/architecture/product-system/LINKED_TEMPLATE_COMPOSITION_CONTRACT.md`
- `docs/qa/form-system-backbone/2026-07-04/PRODUCT_TRUTH_LINKED_SEGMENT_READINESS_V1_QA.md`
- `docs/worklog/realignment/2026-07-04_product_truth_linked_segment_readiness_v1.md`

Missing optional docs: none.

Key contract anchors:

- `TPL-VOLUMETRIC-LETTERS_v2` is the current active offerable root.
- `TPL-VOLUMETRIC-LOGO_v1` remains candidate and is not active in Work Intake now.
- In the current linked composition, Logo is child/segment only, not separate offer, quote, order, component root, or Work Intake root.
- The forbidden old logo backing templates must not be displayed owner-facing as active component templates.
- The Step 2 logical-list UI remains read-only and must not create commercial meaning.

## Diff Summary

### TemplateLibraryView.tsx

Superseded note:
- Superseded by `d8b70ab`: canonical runtime/backend mounting template code is `TPL-METAL-PREMOUNT-STRUCTURE_v1`.
- Historical alias references below are retained only as then-observed UI state and must not be reused as canonical template code.

- Adds `Share2` icon usage for a new shared component usage popover.
- Adds `SharedComponentUsagePopover`, showing which products use a shared component and whether each binding is candidate/offerable with Work Intake status.
- Adds a hardcoded shared volumetric base map for six common modules:
  - `TPL-VOLUMETRIC-FACE_v1`
  - `TPL-VOLUMETRIC-BACK_v1`
  - `TPL-VOLUM-ALUMINIU_v1`
  - `TPL-VOLUMETRIC-FINISH_v1`
  - `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`
  - `TPL-VOLUMETRIC-LED_v1`
- Adds helper functions for shared module display keys/names, formatting shared base modules, detecting shared base availability, and resolving lighting strategy source.
- Hides legacy logo backing templates from the Components list:
  - `TPL-VOLUMETRIC-LOGO-FACE_v1`
  - `TPL-VOLUMETRIC-LOGO-BACK_v1`
  - `TPL-VOLUMETRIC-LOGO-RETURN_v1`
  - `TPL-VOLUMETRIC-LOGO-FINISH_v1`
  - `TPL-VOLUMETRIC-LOGO-MOUNTING_v1`
- Renames the previous shared-contract framing toward shared modules / shared components.
- Changes component cards from detailed binding rows to compact shared component cards with usage popovers.
- Changes Composition view to prefer a shared volumetric base card when a product has six shared component contracts.
- Preserves copy saying shared modules do not activate pricing, execution, or Work Intake.
- Risk: the usage popover and composition panel faithfully render backend availability. If dirty backend/test state marks Logo as offerable, this UI will surface `Logo offerable / Work Intake DA`, which conflicts with the current contracts.

### TemplateLibraryView.test.tsx

- Updates tests to expect the new compact shared module cards, usage popovers, detailed-density behavior, and shared-base composition cards.
- Adds expectations that legacy logo backing templates/labels are hidden from Components and Composition surfaces.
- Adds density assertions for compact vs detailed mode.
- Adds tests that strategy details are hidden in compact mode and shown in detailed mode.
- Problem: multiple assertions expect Logo as `offerable` / `Work Intake DA`, including:
  - Product view compact foundation for Logo.
  - Shared component usage popover entries for Logo.
  - Shared lighting usage entry for Logo.
  - Composition shared-base panel for Logo.
- The tests therefore cover the new UI mechanics, but they also lock in a semantic deviation from the contracts. They are not a clean regression guard for owner direction as written.

### ProductSystem.tsx

- Adds `SHARED_VOLUMETRIC_EDITOR_MODULES`, a hardcoded map from shared component keys to the six canonical shared module template codes.
- Changes `SharedVolumetricFoundationPanel` copy from `Backing module` to `Shared module` and prefers the hardcoded shared module map.
- Detects `isLogoSharedProfile` from `availability.shared_component_contracts` containing `profile_key === "logo"`.
- For Logo shared profile, shows `SharedVolumetricFoundationPanel` instead of `ProductAggregateOverviewPanel`.
- Prevents the aggregate details block from rendering for Logo shared profile.
- Risk: this is small but behavior-visible editor logic. It is aligned with the shared-module direction, but it also relies on availability/profile data being semantically correct.

## Semantic Assessment

| Concern | Verdict | Notes |
|---|---|---|
| Produse vs Componente separation | PARTIAL | Products and Components are visually separated, and old logo backing templates are hidden from Components. But tests also allow Logo to look like an offerable product/root. |
| Compozitii meaning | PARTIAL | Composition view is clearer for the shared volumetric base, but it may over-summarize real composition modules as `Shared base: 6/6` and hide candidate/root boundaries. |
| Shared volumetric base | GOOD_DIRECTION | The six shared modules model matches the canonical contract better than duplicated logo backing templates. |
| Logo candidate / linked child boundary | FAIL | Tests encode Logo as `offerable` / `Work Intake DA`; contracts say Logo remains candidate, child/segment only in this flow, and not Work Intake root. |
| UI hardcoding risk | MEDIUM | The six shared module codes are hardcoded in UI helpers. This may be acceptable as a display adapter only if it mirrors ProductSystem API truth, but it should not become commercial authority. |
| Pricing/Quote/Order boundary | PASS | No pricing, quote, order, CostEngine, execution, ProductAggregate, TaskGraph, or ExecutionPlan changes are in the three audited files. UI copy explicitly says shared modules do not activate pricing/execution/Work Intake. |

## Audit Answers

### A. What changes in `TemplateLibraryView.tsx`?

- Tabs: existing catalog tabs remain; copy changes `Shared contracts` toward `Shared modules` / `Componente comune`.
- Cards: Overview and Components cards become more compact; shared module usage is behind a `Share2` popover.
- Componente: legacy logo backing templates are filtered out; six shared components become primary visible units.
- Produse: product rows show shared-base badges and Work Intake status from availability.
- Compozitii: shared volumetric base becomes the primary displayed model for products with six shared contracts.
- Compact mode/density: compact hides detailed strategy/confidence copy; detailed reveals it.
- Shared base: hardcoded six-module shared base is introduced as display model.
- Logo candidate: UI can still show candidate if backend availability says candidate, but the dirty tests use Logo as offerable.
- Click/navigate to dossier: no dossier navigation change identified in this diff.

### B. What changes in `TemplateLibraryView.test.tsx`?

- Tests now cover compact/detailed density, shared usage popovers, hidden legacy logo backing templates, and shared-base composition cards.
- Tests do cover real UI mechanics.
- Tests do not fully guard the correct product boundary because they assert Logo is `offerable` / `Work Intake DA`.
- Verdict: tests were adapted partly to a semantic deviation, not only to a visual refactor.

### C. What changes in `ProductSystem.tsx`?

- Not just controlled state or tab/density.
- Adds editor behavior for Logo shared profile by rendering shared foundation instead of ProductAggregate overview.
- Adds hardcoded shared module mapping for editor display.
- Risk: behavior-visible and unvalidated by a `ProductSystem.test.tsx` file, which does not exist.

### D. Is the group coherent?

MIXED.

The UI display work is coherent around shared volumetric base. The Logo offerability stance is not coherent with the current contracts and appears to belong with the separate backend ProductSystem availability / active-template dirty group.

### E. Does it respect owner direction?

PARTIAL.

Respects:

- legacy logo backing templates are not shown as active components;
- shared base does not duplicate six logo component templates;
- no pricing/quote/order/execution code is touched;
- UI copy avoids claiming pricing/execution activation.

Violates or risks violating:

- tests lock in Logo as `offerable` / `Work Intake DA`;
- ProductSystem can display Logo as root offerable if paired with dirty backend availability changes;
- this blurs the candidate/linked child boundary for `TPL-VOLUMETRIC-LOGO_v1`.

### F. Is it safe for separate commit?

NO as-is.

It is PARTIAL if split:

- candidate subcommit: shared modules UI display + hiding legacy logo backing templates, while keeping Logo candidate / Work Intake NU in mocks and expectations;
- separate blocked/owner-decision subcommit: any change that makes Logo root offerable / Work Intake DA.

## Test Results

- `pnpm.cmd --dir frontend exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=verbose`: PASS, 13 tests passed.
- `frontend/src/pages/ProductSystem.test.tsx`: missing; no test file found.
- `git diff --check -- frontend/src/features/product-system/TemplateLibraryView.tsx frontend/src/features/product-system/TemplateLibraryView.test.tsx frontend/src/pages/ProductSystem.tsx`: PASS, no output.
- Note: the first parallel `git diff --check` attempt failed because one terminal session did not have `git` on PATH. Re-run with `git.exe` passed.

## Recommendation

SPLIT_GROUP_FIRST

Reason:

The display direction should be preserved, but the Logo root offerable assumption should not be committed without explicit owner GO. A strict commit now would smuggle in a ProductSystem semantic change through frontend tests and mocked availability.

Suggested split:

1. `ProductSystem shared volumetric display only`
   - keep shared modules UI, hidden old logo backing templates, usage popovers, compact/detailed density;
   - keep Logo candidate / Work Intake NU in tests and fixtures;
   - no backend availability changes.
2. `Logo root offerability owner decision`
   - blocked until owner explicitly approves changing `TPL-VOLUMETRIC-LOGO_v1` from candidate/linked child to root offerable.

## If Commit Candidate

Not a commit candidate as-is.

Exact files if split and corrected later:

- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.test.tsx`
- possibly `frontend/src/pages/ProductSystem.tsx` if editor shared-foundation behavior is intentionally included and tested/reviewed

Suggested commit message after split/fix:

`fix(product-system): clarify shared volumetric component display`

Required final validation before commit:

- `pnpm.cmd --dir frontend exec vitest run src/features/product-system/TemplateLibraryView.test.tsx --reporter=verbose`
- `git diff --check -- frontend/src/features/product-system/TemplateLibraryView.tsx frontend/src/features/product-system/TemplateLibraryView.test.tsx frontend/src/pages/ProductSystem.tsx`
- manual review that Logo remains candidate / Work Intake NU in mocks and visible expectations unless owner GO changes that contract

## Do Not Touch

Unrelated dirty files not included in this audit:

- backend availability / active-template tests;
- WorkIntake routing tests;
- Intake V6 face-finish and roll-width files;
- Intake V6 hydration/footer/module-attention files;
- untracked pre-order technical preview / Product Truth code;
- untracked docs/QA/screenshots;
- `WORKOS_*.md` local notes;
- `database_candidates/`;
- SVG fixtures.

## Boundaries Confirmed

- no code edit;
- no staging;
- no commit;
- no cleanup;
- no reset;
- no git clean.

## Roadmap Awareness

- Cat sunt in directia stabilita: `78/100%`
- Main risk: a good shared-component UI cleanup is currently entangled with a Logo root-offerability assumption that conflicts with ProductSystem/Form System/linked-template contracts.
- Next safe prompt title: `SPLIT_PRODUCT_SYSTEM_SHARED_BASE_DIRTY_GROUP_KEEP_LOGO_CANDIDATE_V1`