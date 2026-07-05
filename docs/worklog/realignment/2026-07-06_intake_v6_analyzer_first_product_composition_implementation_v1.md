# 2026-07-06 — Intake V6 Analyzer-First Product Composition Implementation V1

## Scope

Implemented analyzer-first product composition for Intake V6 without activating downstream Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, seeds, migrations, or manual DB writes.

## Result

PASS for the requested implementation boundary after artifact fix V1.

Initial artifact audit returned PARTIAL because evidence files were incomplete or contradictory, not because the Gradi Product Truth core was wrong. The artifact fix pass recaptured the analyzer-first new-request screenshot, recaptured the operator-friendly role dropdown with visible options, regenerated the typecheck artifact, and updated the QA report. No product implementation or downstream scope was changed in the artifact fix pass.

The critical proof point is Gradi: `gradi-curat.svg` now produces explicit product composition in Review:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`

Logo-only remains valid as `TPL-VOLUMETRIC-LOGO_v1`, but PASS was not based only on standalone logo.

## Main Changes

- Added pure backend composition recommendation service.
- Persisted additive payload fields for analyzer mode, layer role review, product composition recommendation, and operator confirmation.
- Added product composition confirmation endpoint.
- Changed Work Intake new request to analyzer-first with optional template hint.
- Routed analyzer-first requests by ensured workspace id even when template truth is not final yet.
- Added composition panel in Straturi and Review.
- Required product composition confirmation before quote-preview readiness.
- Exposed composition metadata in logical-list and priced dry-run responses.
- Replaced primary `artwork/policromie` / owner-GO copy with `logo/vector constructiv` operator wording.
- Normalized standalone `logo.svg` pseudo labels to `Logo volumetric` in operator-facing layer rows.

## Runtime Artifacts

QA folder:

`docs/qa/intake-v6-analyzer-first-product-composition-implementation/2026-07-06/`

Includes screenshots, runtime workspace JSON, composition JSON, logical-list JSON, priced dry-run JSON, backend/frontend test logs, typecheck/build summaries, and full QA report.

Artifact fix additions:

- `screenshots/analyzer_first_new_request.png` now shows the actual Work Intake dialog with analyzer-first and optional Product System hint.
- `screenshots/role_dropdown_operator_friendly.png` now shows visible operator-friendly role options.
- `screenshots/role_dropdown_operator_friendly_options_visible.png` was added as an explicit options-visible audit artifact.
- `screenshots/gradi_composition_letters_plus_logo.png` was recaptured to show both `TPL-VOLUMETRIC-LETTERS_v2` and `TPL-VOLUMETRIC-LOGO_v1`.
- `frontend_typecheck_result_summary.txt` was added after rerunning the real frontend typecheck.

## Validations

- Backend targeted pytest: `37 passed, 3 warnings`.
- Frontend focused Vitest: `25 passed | 7 skipped`.
- Final frontend label regression: `2 passed | 7 skipped`.
- Frontend typecheck: PASS.
- Frontend Vite build: PASS with known existing warnings.

## Notes

The implementation keeps the current V6 shell and does not rewrite ProductDefinition/Form System. It produces ProductDefinition-ready composition payload metadata for downstream work.

Secondary legacy terminology remains visible in finish-related UI/data, for example `artwork` / `Policrom`. This is not the primary Product Truth composition label and is not the constructive logo/vector blocker, but it should be cleaned in a separate terminology pass if owner wants the UI fully purged.
