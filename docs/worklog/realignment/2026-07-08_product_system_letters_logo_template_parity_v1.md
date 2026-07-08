## Owner Problem Statement

Align `TPL-VOLUMETRIC-LETTERS_v2` and `TPL-VOLUMETRIC-LOGO_v1` as equal Product Templates in Product System while preserving the current Work Intake offerability guard: Letters offerable, Logo candidate-only.

## Current Mismatch Found

Tracked runtime/product-system policy already treated Logo as a candidate product and not Work Intake offerable.

The local mismatch was in stale backend scope/guard validation expectations:

- legacy guard tests still assumed Logo could be a Work Intake offerable root
- the helper they imported no longer existed

This made the parity contract confusing and inconsistent with current runtime policy.

## Product System Parity Rule

- Letters and Logo are both Product Templates in Product System.
- Letters remains the only Work Intake offerable root.
- Logo remains candidate / linked child / not Work Intake.
- No component root.
- No component quote.

## Files Changed

- `backend/seeds/seed_active_template_scope.py`
- `backend/tests/test_active_template_scope_postcondition.py`

## Tests Run

- `python -m pytest tests/test_active_template_scope_postcondition.py tests/test_product_template_availability.py tests/test_template_usage_mode_policy.py tests/test_form_system_backbone_api_contract.py -q`
  - Result: `27 passed`
- `npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/TemplateLibraryView.test.tsx src/lib/activeTemplateScope.test.ts`
  - Result: `16 passed`

## Runtime Proof

Product System runtime on `/product-system`:

- `TPL-VOLUMETRIC-LETTERS_v2` visible in Products view
- `Produs ofertabil`
- `Work Intake DA`
- `TPL-VOLUMETRIC-LOGO_v1` visible in Products view
- `In pregatire`
- `Work Intake NU`
- shared base / shared modules visible for both
- Logo not rendered as component

Intake V6 regression on `/intake-v6/IR-MRBMAK7Z/operator`:

- `Compozitie produs propusa` still shows `2 segmente linked`
- `Logo 1` and `Logo 2` remain `Confirmat in Pasul 1`
- PSU regression check still shows `Surse: 200W + 100W`
- `Calcul live` still shows `Sursa LED 12V / 2 buc / 67,20 EUR`

## Forbidden Scope Confirmation

- No Quote / Order changes
- No Execution changes
- No DB / seed runtime execution / migration
- No pricing changes
- No Logo root activation
- No component root
- No component quote