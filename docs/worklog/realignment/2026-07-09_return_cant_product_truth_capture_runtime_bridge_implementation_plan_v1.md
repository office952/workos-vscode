# 2026-07-09 - return cant product truth capture runtime bridge implementation plan v1

HEAD before:

- `3c6afb0`

Task:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1`

Mode:

- docs-only / plan-only

Safety gate:

- HEAD confirmed = `3c6afb0`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

Mandatory context read:

- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT.md`
- `docs/worklog/realignment/2026-07-09_return_cant_layer_mapping_source_contract_v1.md`
- `backend/services/intake_v6_workspace_service.py`
- `backend/schemas/intake_v4.py`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `backend/tests/test_letter_group_finish_readiness.py`

Focused findings:

- `save_finish_setup_for_intake_v6_workspace()` is the correct primary write hook because it owns normalized `finish_setup` and final persistence.
- `upload_svg_to_intake_v6_workspace()` and `save_analysis_bundle_for_intake_v6_workspace()` already invalidate `finish_setup` on SVG replacement, so future runtime `return_cant` state must be cleared there too.
- `save_layer_roles_for_intake_v6_workspace()` can change the final mapping basis and must rerun the bridge when `finish_setup` exists.
- `IntakeV4WorkspacePayload` does not yet declare a runtime Product Truth field, and `_parse_payload()` validates against schema, so schema preservation is a mandatory first step.
- readonly adapter and readonly mapper already point toward canonical `components.return_cant`, but they remain evidence and awareness layers only.
- frontend draft builder remains legacy preview shape and must not become the runtime writer.

Plan outcome fixed:

- primary integration point:
  - `backend/services/intake_v6_workspace_service.py`
  - `save_finish_setup_for_intake_v6_workspace()`
- required invalidation or rerun hooks:
  - `upload_svg_to_intake_v6_workspace()`
  - `save_analysis_bundle_for_intake_v6_workspace()`
  - `save_layer_roles_for_intake_v6_workspace()`
- required first implementation step:
  - extend workspace payload schema so runtime Product Truth survives `_parse_payload()`

Rules locked by the plan:

- stable key missing => no synthetic instance
- row-id echo alone => not final `layer_group_ids` truth
- `quote_geometry.letter_perimeter_m` => evidence only
- no automatic `confirmed` state
- legacy read allowed, legacy final write forbidden

Implementation sequence fixed:

- A. pure helper
- B. unit tests
- C. wire helper into finish save path
- D. backend service tests
- E. frontend awareness or mapper recheck only if needed
- F. runtime smoke via API or read-only UI inspection

Decision:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_READY`

Files created:

- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN.md`
- `docs/qa/return-cant-product-truth-capture-runtime-bridge-implementation-plan-2026-07-09/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_product_truth_capture_runtime_bridge_implementation_plan_v1.md`

Validation planned:

- `git diff --check`
- docs-only scoped status or diff review

Forbidden scope confirmation:

- no bridge implementation
- no Product Truth writes
- no UI changes
- no Pricing changes
- no runtime DB writes
- no seeds
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes
- no DB migration