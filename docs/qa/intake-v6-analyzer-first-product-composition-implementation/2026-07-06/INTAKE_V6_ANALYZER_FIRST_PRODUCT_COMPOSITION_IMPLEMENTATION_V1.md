# INTAKE_V6_ANALYZER_FIRST_PRODUCT_COMPOSITION_IMPLEMENTATION_V1

Date: 2026-07-06
Verdict: PASS for analyzer-first Product Composition implementation scope after artifact fix V1.

Artifact audit/fix note, 2026-07-06: the first artifact audit found PARTIAL evidence because the analyzer-first screenshot was wrong, the role dropdown screenshot did not show the options list, and the typecheck artifact was stale/contradictory. This folder now contains recaptured screenshots and regenerated validation logs. No product implementation, Product Truth logic, DB write, seed, migration, Quote, Order, Execution, ProductAggregate, TaskGraph, or ExecutionPlan change was made by the artifact-fix pass.

## Purpose

Implement the route:

Work Intake / Cerere noua -> SVG Analyzer first -> upload SVG -> layer/group detection -> operator-friendly role confirmation -> recommended product composition -> operator confirms composition -> Review / Form System -> Product Truth payload -> logical-list / priced dry-run preview.

No real Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, seed, migration, or manual DB write was performed.

## Implementation Summary

- Backend now derives and persists `layer_role_review`, `product_composition_recommendation`, `product_composition_confirmed`, `analyzer_mode`, `template_hint_code`, and `terminology_mode` in the Intake V6 workspace payload.
- Product composition recommendation is analyzer-first and explicit:
  - logo-only -> `TPL-VOLUMETRIC-LOGO_v1`
  - letters-only -> `TPL-VOLUMETRIC-LETTERS_v2`
  - letters + logo -> `TPL-VOLUMETRIC-LETTERS_v2` + `TPL-VOLUMETRIC-LOGO_v1`
  - support/background roles -> explicit pending support item, not absorbed.
- Work Intake `Cerere Noua` now creates analyzer-first V6 workspaces with optional template hint; selected template is no longer final Product Truth before SVG analysis.
- V6 route resolution now uses ensured workspace id as V6 proof even before template truth exists.
- Operator UI now shows a `Compozitie produs propusa` panel in Straturi and Review and requires operator confirmation before quote-preview readiness.
- Main operator copy now uses `logo/vector constructiv`, not `artwork/policromie` or owner-GO root blocker copy.
- Logical-list and priced dry-run responses now expose composition metadata; dry-run blocks with `PRODUCT_COMPOSITION_NOT_CONFIRMED` until composition is confirmed.

## Files Changed In This Slice

Backend:
- `backend/services/intake_v6_product_composition_recommendation_service.py`
- `backend/tests/test_intake_v6_product_composition_recommendation.py`
- `backend/schemas/intake_v4.py`
- `backend/schemas/intake_v6.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/intake_v6_priced_quote_dry_run_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`

Frontend:
- `frontend/src/components/workos/NewIntakeDialog.tsx`
- `frontend/src/components/workos/NewIntakeDialog.test.tsx`
- `frontend/src/lib/volumetricIntakeRoute.ts`
- `frontend/src/lib/volumetricIntakeRoute.test.ts`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.ts`
- `frontend/src/lib/intakeV6/intakeV6Readiness.ts`
- `frontend/src/lib/intakeV6/intakeV6Readiness.test.ts`
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.ts`
- `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkOnlyDecisionPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`

## Validation Commands

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_intake_v6_workspace_offer_context.py tests\test_gradi_logical_list_read_model.py tests\test_shared_material_color_catalog_registry.py tests\test_intake_v6_product_composition_recommendation.py -q
```

Result: `37 passed, 3 warnings`.

Frontend focused:

```powershell
cd frontend
npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx src/lib/volumetricIntakeRoute.test.ts src/lib/intakeV6/intakeV6Readiness.test.ts src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts -t "exposes Step 1 operator message constant|NewIntakeDialog|volumetricIntakeRoute|intakeV6Readiness boundary|IntakeV6ProductCompositionPanel"
```

Result: `5 passed`, `25 passed | 7 skipped`. The skipped tests depend on missing local SVG fixture files under `fisiere-teste/`, not this implementation.

Final quick frontend regression after label patch:

```powershell
npx/pnpm vitest run src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts -t "exposes Step 1 operator message constant|IntakeV6ProductCompositionPanel"
```

Result: `2 passed | 7 skipped`.

Frontend typecheck:

```powershell
npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit -p tsconfig.app.json
```

Result: PASS, no output. Raw artifact: `frontend_typecheck_result.txt`. Summary artifact: `frontend_typecheck_result_summary.txt`.

Frontend build:

```powershell
npx/pnpm vite build
```

Result: PASS. Known warnings remain: old Browserslist data, existing CSS minifier bracket warning, dynamic/static config chunk warning, large chunk warning.

## Runtime Proof

Live stack used:
- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8000`

Runtime workspaces created through app APIs/UI:
- Logo workspace: `0f08c338-c435-4e01-a243-7c19ff12ad44`
- Gradi workspace: `dcf3c7ea-1e26-44d0-a159-6c78a638a528`

Screenshots:
- `screenshots/analyzer_first_new_request.png`
- `screenshots/logo_svg_straturi_role_clean.png`
- `screenshots/logo_svg_composition_recommendation.png`
- `screenshots/logo_svg_review_price_ready.png`
- `screenshots/gradi_straturi_roles_clean.png`
- `screenshots/gradi_composition_letters_plus_logo.png`
- `screenshots/gradi_review_composition_price.png`
- `screenshots/role_dropdown_operator_friendly.png`
- `screenshots/role_dropdown_operator_friendly_options_visible.png`

Runtime JSON artifacts:
- `runtime_logo_workspace_state.json`
- `runtime_logo_composition_recommendation.json`
- `runtime_logo_logical_list.json`
- `runtime_logo_priced_quote_dry_run.json`
- `runtime_gradi_workspace_state.json`
- `runtime_gradi_composition_recommendation.json`
- `runtime_gradi_logical_list.json`
- `runtime_gradi_priced_quote_dry_run.json`

Observed runtime facts:
- `logo.svg` shows `Logo volumetric` as the operator-facing standalone layer label and recommends `TPL-VOLUMETRIC-LOGO_v1`.
- `gradi-curat.svg` Review shows explicit composition: `TPL-VOLUMETRIC-LETTERS_v2` + `TPL-VOLUMETRIC-LOGO_v1`.
- Gradi Review shows price preview values and composition metadata together.
- Main flow no longer presents `artwork/policromie`, `owner GO`, or `root comercial neofertabil` as the primary blocker/copy for constructive logo/vector.
- Recaptured `analyzer_first_new_request.png` now shows the actual Work Intake new request UI with `Hint Product System optional`, `Analyzer-first`, and template hint choices.
- Recaptured `role_dropdown_operator_friendly.png` shows the role select expanded as an audit-only browser overlay, with operator-friendly options visible.
- Recaptured `gradi_composition_letters_plus_logo.png` now shows both `TPL-VOLUMETRIC-LETTERS_v2` and `TPL-VOLUMETRIC-LOGO_v1` in the Review composition panel.

## Boundaries Confirmed

No quote/order/execution writes were implemented or invoked by this build. ProductAggregate, TaskGraph, ExecutionPlan, seeds, migrations, and manual DB writes stayed out of scope.

## Residual Notes

- Some old diagnostic copy still contains internal terms like `logo/artwork candidate` in analyzer warnings; these are not the main operator decision copy and can be cleaned separately.
- Review/finish secondary UI still contains legacy labels such as `artwork` / `Policrom` in finish-related copy. These are not the Product Truth composition label and are not the primary constructive logo/vector blocker, but they remain visible as secondary legacy terminology.
- Existing full frontend test gate remains subject to repository-wide TS/test debt per `AGENTS.md`; this build used focused tests plus app typecheck/build.
- Fixture-dependent guard tests under `frontend/src/lib/intakeV6/intakeV6ArtworkOnlyGuard.test.ts` still skip/fail if `fisiere-teste/*` fixtures are absent; unrelated to this implementation.
