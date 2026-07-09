# Return Cant Product Truth Capture Runtime Bridge Implementation V1

Decision: RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTED

Scope:
- Backend-only runtime bridge for canonical `product_truth.components.return_cant`
- No UI, pricing registry, quote/order/execution, ProductAggregate, TaskGraph, or migration changes

Files changed:
- `backend/schemas/intake_v4.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/services/intake_v4_workspace_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/tests/test_return_cant_product_truth_bridge.py`

Implementation summary:
- Extended the workspace payload schema to preserve `product_truth` through payload parsing and persistence.
- Added a pure helper that derives canonical runtime `return_cant` instances from persisted finish setup, layer role setup, and quote geometry evidence.
- Wired the bridge into both V4 and V6 workspace mutation paths:
  - apply on finish setup save
  - rerun on layer role updates when finish setup exists
  - rerun on analysis bundle save when finish setup remains valid
  - clear stale `return_cant` truth when SVG replacement invalidates finish setup

Test notes:
- Added focused helper and integration coverage in `backend/tests/test_return_cant_product_truth_bridge.py`.
- Repaired local test setup so workspace creation seeds the actual `TPL-VOLUMETRIC-LETTERS_v2` Product System template.
- Aligned integration assertions with the real HTTP contract (`201 Created` on workspace create) and current cleanup behavior (`product_truth` may become `null` after stale clear).

Validation:
- `backend\\.venv\\Scripts\\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py tests/test_letter_group_finish_readiness.py -q`
- Result: `22 passed`

Remaining limitations in this minimal bridge:
- Missing stable keys are skipped rather than recorded in a global diagnostics container.
- `confirmed_perimeter_m` is not authored in v1; quote geometry perimeter remains evidence only.
- No legacy transitional writeback to `components.returnCant`.

Recommended next prompt:
- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_QA_V1`