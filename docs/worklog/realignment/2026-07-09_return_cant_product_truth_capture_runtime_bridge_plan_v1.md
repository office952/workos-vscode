# 2026-07-09 - return cant product truth capture runtime bridge plan v1

HEAD before:

- `ef30518`

Task:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN_V1`

Files read:

- `docs/qa/return-cant-pricing-keys-readonly-verification-2026-07-09/RETURN_CANT_PRICING_KEYS_READONLY_VERIFICATION_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_keys_readonly_verification_v1.md`
- `docs/architecture/product-system/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN.md`
- `docs/architecture/product-system/REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnCantBridge.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishModel.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/product_truth_audit_view_service.py`

Files touched:

- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN.md`
- `docs/qa/return-cant-product-truth-capture-runtime-bridge-plan-2026-07-09/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_product_truth_capture_runtime_bridge_plan_v1.md`

Decision:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_BRIDGE_PLAN_BLOCKED`

Why blocked:

1. runtime persist path exists, but only for `finish_setup` and additive derived payload fields;
2. no canonical persisted `components.return_cant.instances.<instance_key>` container exists today;
3. no canonical `components.face.confirmed_perimeter` runtime source exists today;
4. no explicit component-level confirmation field exists for `return_cant`;
5. readonly adapter still references legacy/lowercase pricing targets for the new verified keys;
6. product truth draft / backbone contracts remain on legacy `components.returnCant.*` and `components.return.*` shapes.

Correct future implementation point found:

- backend persist-time derivation inside `save_finish_setup_for_intake_v6_workspace(...)`

Reason:

- same payload already contains `finish_setup`, `layer_role_setup`, `quote_geometry`, and composition confirmation evidence;
- backend already applies additive derivations such as product composition recommendation and pricing preview derived state;
- no public endpoint addition is needed.

Important confirmation rules documented:

- `quote_geometry.letter_perimeter_m` is context only
- Step 1 confirmation is not component confirmation
- row `confirmed` is not component confirmation
- global `finish_setup.confirmed` is not `return_cant.confirmation_state = confirmed`

Terminology alignment documented:

- UI: `Culoare Stoc`, `Folie autocolanta`, `Vopsit RAL`
- technical/Product Truth/backend: `stock_color`, `vinyl_application`, `paint_application`
- Product Truth must not adopt legacy aliases as final runtime truth

Validation run:

- read-only audit only
- `git diff --check`

Next recommended prompt:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1`