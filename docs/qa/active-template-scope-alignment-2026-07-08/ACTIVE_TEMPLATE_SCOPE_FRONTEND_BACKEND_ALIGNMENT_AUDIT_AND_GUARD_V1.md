# ACTIVE_TEMPLATE_SCOPE_FRONTEND_BACKEND_ALIGNMENT_AUDIT_AND_GUARD_V1

## Status

- Date: 2026-07-08
- Mode: FRONTEND_GUARD_FIX_PLUS_RUNTIME_AUDIT
- Frontend edits: MINIMAL_LOCAL_GUARD
- Backend edits: NONE
- DB writes: NONE
- Seed changes: NONE

## Scope

Target:

- align frontend owner-valid active template scope with backend authority
- verify that Product System UI labels remain coherent after the guard
- verify that shared component templates remain visible as Product System/shared-module entries without becoming owner-valid quote roots

Out of scope:

- backend policy changes
- Work Intake root activation changes
- Pricing activation
- Quote / Order / Execution behavior changes
- component root or component-only quote activation
- migrations, seeds, parked lanes

## Files Changed

- `frontend/src/lib/activeTemplateScope.ts`
- `frontend/src/lib/activeTemplateScope.test.ts`

## Files And Surfaces Inspected

Frontend:

- `frontend/src/lib/activeTemplateScope.ts`
- `frontend/src/lib/activeTemplateScope.test.ts`
- `frontend/src/features/product-system/templateSelectionStorage.ts`
- `frontend/src/features/product-system/productSystemNavigation.ts`
- `frontend/src/features/product-system/TemplateSelectorSheet.tsx`
- `frontend/src/features/product-system/TemplateDownstreamLinkagePanel.tsx`
- `frontend/src/components/workos/NewIntakeDialog.tsx`
- `frontend/src/components/workos/NewIntakeDialog.test.tsx`

Backend:

- `backend/services/active_template_scope.py`
- `backend/services/template_usage_mode_policy.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/tests/test_active_template_scope.py`
- `backend/tests/test_active_template_scope_guard.py`
- `backend/tests/test_logo_seed_scope_guard.py`
- `backend/tests/test_product_template_availability.py`
- `backend/tests/test_intake_v6_workspace_offer_context.py`

Runtime UI checked:

- `/product-system`

## Local Hypothesis And Resolution

Hypothesis before edit:

- frontend wrongly treated `TPL-METAL-PREMOUNT-STRUCTURE_v1` as owner-valid active for quote/product-system scope
- backend authority already fail-closed to root-offerable scope only, so the mismatch was local to frontend filtering, labels, default-selection and downstream-linkage loading

Discriminating check:

- compare `frontend/src/lib/activeTemplateScope.ts` with `backend/services/active_template_scope.py` and backend tests for `tpl-metal-premount-structure-v1`

Result:

- hypothesis confirmed
- frontend included premount structure in `OWNER_VALID_ACTIVE_TEMPLATE_CODES`
- backend tests explicitly require `tpl-metal-premount-structure-v1` to be false for owner-valid active scope

Applied fix:

- removed `TPL-METAL-PREMOUNT-STRUCTURE_v1` from frontend `OWNER_VALID_ACTIVE_TEMPLATE_CODES`
- added explicit frontend guard coverage asserting premount structure remains false and archived/experimental in quote scope filters

## Findings

### 1. Backend authority was already correct

Confirmed:

- backend owner-valid active scope derives from `ROOT_OFFERABLE_TEMPLATE_CODES`
- current owner-valid root remains `TPL-VOLUMETRIC-LETTERS_v2`
- premount structure remains shared/component-only policy, not root-offerable
- logo remains candidate-only, not owner-valid root

Assessment:

`PASS`

### 2. Frontend mismatch was real and functionally relevant

Observed before fix:

- frontend helper marked `TPL-METAL-PREMOUNT-STRUCTURE_v1` as owner-valid active
- affected surfaces included active/archive filtering, editability, default selection and downstream linkage fallback decisions

Assessment:

`FIXED`

### 3. Work Intake root selection was already backend-aligned

Observed:

- `NewIntakeDialog` uses backend availability API
- visible intake choices remain offerable product plus candidate product surfaces only
- runtime modules/shared components are not promoted into root Work Intake selection by this frontend helper

Assessment:

`PASS`

### 4. Product System runtime labels remain coherent after the guard

Observed in runtime UI:

- overview still states `Letters: offerable` and `Logo: candidate / not Work Intake`
- products tab still shows `Work Intake DA` only for `TPL-VOLUMETRIC-LETTERS_v2`
- products tab still shows `Work Intake NU` and `GO owner` messaging for `TPL-VOLUMETRIC-LOGO_v1`
- components tab still exposes the six shared volumetric modules/components as reusable technical entries without implying root offerability

Assessment:

`UI_PASS_WITH_SCREENSHOTS`

## Alignment Matrix

| Template / scope item | Frontend after guard | Backend authority | Owner-valid root? | Work Intake root? | Notes |
|---|---|---|---|---|---|
| `TPL-VOLUMETRIC-LETTERS_v2` | active | active | YES | YES | current canonical owner-valid root |
| `TPL-VOLUMETRIC-LETTERS` | archived / experimental in helper scope | not owner-valid | NO | legacy alias only | still used in compatibility slices, not current root authority |
| `TPL-VOLUMETRIC-LOGO_v1` | non-active root / candidate surface | candidate-only | NO | NO | requires owner GO; composition intent only |
| `TPL-VOLUMETRIC-FACE_v1` | non-root shared/component entry | component-only | NO | NO | shared technical component |
| `TPL-VOLUMETRIC-BACK_v1` | non-root shared/component entry | component-only | NO | NO | shared technical component |
| `TPL-VOLUMETRIC-LED_v1` | non-root shared/component entry | component-only | NO | NO | shared primary LED module; letters strategy source |
| `TPL-VOLUMETRIC-FINISH_v1` | non-root shared/component entry | component-only | NO | NO | shared finish module |
| `TPL-VOLUM-ALUMINIU_v1` | non-root shared/component entry | component-only | NO | NO | shared return/side module |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | non-root after guard | component-only | NO | NO | exact mismatch fixed in frontend helper |
| `TPL-VOLUMETRIC-LOGO-LIGHTING_v1` / profile source | strategy/profile source only | not root-offerable | NO | NO | appears in UI as logo lighting strategy/profile source, not duplicated primary shared module |

## Runtime Evidence

Observed at `/product-system` after the guard:

- Overview: `Letters: offerable`, `Logo: candidate / not Work Intake`
- Products detailed view:
  - `TPL-VOLUMETRIC-LETTERS_v2` shows `Work Intake: DA`
  - `TPL-VOLUMETRIC-LOGO_v1` shows `Work Intake: NU` and `GO owner`
- Components detailed view:
  - shared entries remain listed as technical/shared modules
  - no shared component is presented as owner-valid root

## Commands Run

- `cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/activeTemplateScope.test.ts`
- `cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/features/product-system/templateSelectionStorage.test.ts`

Results:

- `activeTemplateScope.test.ts`: PASS
- `templateSelectionStorage.test.ts`: PASS

## Screenshots

See:

- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/01_product_system_overview.png`
- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/02_product_system_products_tab.png`
- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/03_product_system_components_tab.png`
- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/04_product_system_letters_detail.png`
- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/05_product_system_logo_detail.png`
- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/06_product_system_shared_modules_or_components.png`
- `docs/qa/active-template-scope-alignment-2026-07-08/screenshots/07_product_system_scope_labels.png`

## Verdict

Overall:

`PASS_WITH_LOCAL_GUARD_FIX`

Meaning:

- backend/frontend owner-valid active scope is aligned again for the known mismatch
- shared components remain visible in Product System as shared technical entries only
- no evidence was found that this guard activates component root, component quote or downstream protected flows

## Next Safe Step

If follow-up is needed, the correct next slice is not activation.

The next safe slice is to consolidate canonical naming around mounting/finish aliases so UI labels, shared contracts and backend component policy describe the same component boundary without implying root offerability.
