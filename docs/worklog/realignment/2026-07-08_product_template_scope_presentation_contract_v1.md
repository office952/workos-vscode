# Product Template Scope Presentation Contract V1

Date: 2026-07-08

## Why this slice exists

The same Product Template scope truth was being re-expressed in multiple frontend places:
- Work Intake new-request modal
- Product System product cards
- Product System shared-component usage popovers
- Product System shared-base composition summaries

That duplication created drift risk between:
- design-time Product System presentation
- Work Intake operator hint presentation

## Duplicated mappings found

Frontend duplication audited:
- `frontend/src/components/workos/NewIntakeDialog.tsx`
  - local `getTemplateHintPresentation(...)`
  - hardcoded Product Template category/status/root labels for Letters and Logo
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
  - local `Work Intake DA/NU` derivation from `quote_offerable`
  - local compact status mapping `Produs ofertabil` / `In pregatire`
  - local candidate usage text `candidate / linked child`
  - local candidate direct-root warning copy

Supporting audit findings:
- `frontend/src/lib/activeTemplateScope.ts`
  - active/root offerability gate only; no UI presentation mapping
- `backend/services/product_template_availability_service.py`
  - semantic source already exposes safe frontend metadata:
    - `product_system_role`
    - `display_group`
    - `quote_offerable`
    - `owner_decision_required`
    - `ui_label`
    - `ui_description`
- `backend/services/template_usage_mode_policy.py`
  - confirms canonical product intent for Letters vs Logo, but is not a frontend presentation helper

No backend/frontend semantic conflict was found in this audit.

## Contract/helper created

Created:
- `frontend/src/lib/productTemplateScopePresentation.ts`

The helper consolidates Product Template scope presentation into one frontend adapter and returns:
- `templateCode`
- `isProductTemplate`
- `workIntakeLabel`
- `rootDirectLabel`
- `statusLabel`
- `shortDescription`
- `isDirectRootAllowed`
- `isCandidateComposition`
- `forbiddenReason`

Additional convenience fields kept local duplication down further:
- `catalogStatusLabel`
- `usageModeLabel`
- `workIntakeValueLabel`
- `familyLabel`

Separate helper kept for analyzer-first:
- `getAnalyzerFirstScopePresentation()`

## Files changed

- `frontend/src/lib/productTemplateScopePresentation.ts`
- `frontend/src/lib/productTemplateScopePresentation.test.ts`
- `frontend/src/components/workos/NewIntakeDialog.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `docs/worklog/realignment/2026-07-08_product_template_scope_presentation_contract_v1.md`

## Tests run

Focused frontend tests:

```powershell
Set-Location frontend
cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/productTemplateScopePresentation.test.ts src/components/workos/NewIntakeDialog.test.tsx src/features/product-system/TemplateLibraryView.test.tsx
```

Result:
- PASS
- 30 tests passed
- existing React `act(...)` warnings still emitted from `NewIntakeDialog.test.tsx`

Additional patch sanity:

```powershell
git diff --check
```

Result:
- PASS

## Runtime proof

### `/intake`

Verified in running browser:
- `Cerere Nouă` -> `SVG Analyzer - Intake V6` -> `Pas 2/3`
- `Analyzer-first` remains `Recomandat`
- `TPL-VOLUMETRIC-LETTERS_v2` shows:
  - `Product Template`
  - `Work Intake DA`
  - `Root direct: permis`
  - `Activ pentru ofertare`
- `TPL-VOLUMETRIC-LOGO_v1` shows:
  - `Product Template`
  - `Work Intake NU`
  - `Root direct: blocat pana la owner GO`
  - `Candidat compozitie`

### `/product-system`

Verified in running browser Products view:
- `TPL-VOLUMETRIC-LETTERS_v2` remains `Produs ofertabil` with `Work Intake DA`
- `TPL-VOLUMETRIC-LOGO_v1` remains `In pregatire` with `Work Intake NU`
- Logo remains a product/template surface, not a component root surface

### `/intake-v6/IR-MRBMAK7Z/operator`

Regression rechecked in running browser:
- `Compozitie produs propusa` still shows `Litere volumetrice + logo volumetric`
- earlier runtime check in this slice still showed `Logo 1` and `Logo 2` as `Confirmat in Pasul 1`
- `Iluminare` still shows `Surse: 200W + 100W`
- `Calcul live` still shows parent `Sursa LED 12V / 2 buc / 67,20 EUR`
- with technical details on, PSU child split still shows:
  - `Sursa 12V 100W`
  - `Sursa 12V 200W`
- no false `BLOCAT`

## Forbidden scope confirmation

Not touched:
- Logo offerability
- standalone Logo root
- component root / component quote behavior
- Quote / Order / Execution logic
- ProductAggregate / TaskGraph / ExecutionPlan
- DB / seed / migration
- pricing / LED / PSU formula logic
- broad UI redesign
- parked untracked lanes

## Remaining risks

- Product System still has some intentionally separate design-time copy that is not identical to Work Intake copy (`Produs ofertabil` / `In pregatire` vs `Activ pentru ofertare` / `Candidat compozitie`). The helper now centralizes the scope decision and the status families, but surface-specific wording still exists by design.
- Existing `NewIntakeDialog` tests still emit React `act(...)` warnings; this slice did not change that behavior.
