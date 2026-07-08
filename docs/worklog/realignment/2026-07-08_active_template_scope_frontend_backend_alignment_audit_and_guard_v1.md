# 2026-07-08 - active template scope frontend backend alignment audit and guard v1

## Summary

Closed the known frontend/backend owner-valid active template mismatch with a strict local frontend guard.

The only runtime code change was in the frontend helper that defines owner-valid active quote scope.

## What Changed

- removed `TPL-METAL-PREMOUNT-STRUCTURE_v1` from `frontend/src/lib/activeTemplateScope.ts` owner-valid active scope
- added explicit frontend test coverage proving premount structure remains false for owner-valid active scope
- revalidated default-template selection because it depends on the same helper

## Why This Was Safe

- backend authority already excluded premount structure from root-offerable owner-valid scope
- Work Intake root selection already came from backend availability, so no backend or intake contract change was needed
- the change narrows frontend behavior to existing backend truth instead of introducing new policy

## Runtime Proof Captured

- Product System overview
- Product System products tab
- Product System components tab
- filtered Letters product view
- filtered Logo product view
- detailed components/shared-modules view
- detailed products scope-label view

Stored under:

- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/`

## Commands Run

- `cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/activeTemplateScope.test.ts`
- `cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/templateSelectionStorage.test.ts`

## Results

- both targeted Vitest commands passed
- runtime Product System labels remained coherent after the guard
- no backend changes were necessary

## Remaining Risks

- mounting/finish alias naming still needs canonical cleanup in a later read-only/documentation or presentation slice
- the repo worktree still contains substantial pre-existing untracked noise; this pass did not attempt cleanup

## Commit Status

No commit created in this pass.

Reason:

- the requested workflow is safer as an uncommitted narrow slice while the worktree remains noisy and other unrelated changes are present
