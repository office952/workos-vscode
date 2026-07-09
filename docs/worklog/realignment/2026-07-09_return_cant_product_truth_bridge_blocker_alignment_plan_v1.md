# 2026-07-09 - return cant product truth bridge blocker alignment plan v1

HEAD before:

- `6a60cd3`

Task:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1`

Files read:

- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN.md`
- `docs/qa/return-cant-product-truth-capture-runtime-bridge-plan-2026-07-09/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_product_truth_capture_runtime_bridge_plan_v1.md`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- selected tests around Product Truth / backbone / Intake V6 workspace save

Files touched:

- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN.md`
- `docs/qa/return-cant-product-truth-bridge-blocker-alignment-plan-2026-07-09/RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_product_truth_bridge_blocker_alignment_plan_v1.md`

Decision:

- `RETURN_CANT_BRIDGE_BLOCKERS_ALIGNMENT_READY`

Main findings:

1. blockerul structural principal este lipsa containerului runtime canonic pentru `components.return_cant.instances.<instance_key>`;
2. builderul legacy `components.returnCant` si backbone-ul `components.return.*` confirma ca primul pas trebuie sa fie contractul target shape, nu implementation write;
3. readonly adapter pricing targets legacy pot fi aliniate separat, dar nu inlocuiesc nevoia de target shape contract;
4. confirmation semantics si perimeter source semantics trebuie definite dupa container contract, nu inainte.

Ordered next slices recorded:

1. `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`
2. `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`
3. `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1`
4. `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1`
5. `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_V1`

First recommended slice:

- `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`

Reason:

- all remaining slices depend on a final canonical path model;
- without it, legacy and final shapes would stay mixed;
- adapter alignment alone would still leave write target ambiguity unresolved.

Validation run:

- read-only audit only
- `git diff --check`

Next recommended prompt:

- `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`