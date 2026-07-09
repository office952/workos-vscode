# Form System Mounting Scope Runtime Capture V1

Verdict: PASS

HEAD before implementation:
- `c0fe87d`

Scope:
- minimal runtime capture for `mounting.mounting_scope`
- canonical runtime field `finish_setup.mounting_scope`
- no UI visual change
- no Pricing
- no DB migration
- no seed
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph changes
- no new endpoint
- no `support_type` implementation

Canonical payload decision:
- runtime field is `finish_setup.mounting_scope`
- projection path remains `components.mounting.mountingScope`
- `mounting_system` remains the technical mounting method field and is not reused as commercial scope
- `support_type` remains separate and is not reused as commercial scope

Implemented:
- extended backend finish setup schema with first-class `mounting_scope`
- added fail-closed runtime helper for `finish_setup.mounting_scope`
- added backbone runtime field and payload-aware overlay for `mounting.mounting_scope`
- updated mapping adapter to read runtime source from backbone instead of treating scope as permanently blocked docs-only metadata
- preserved blocked behavior when scope is missing or the finish setup is unconfirmed

Runtime payload shape:

```json
{
  "finish_setup": {
    "mounting_scope": "mounting_included",
    "mounting_system": "steel_bars",
    "support_type": "steel_frame",
    "confirmed": true
  }
}
```

Rules enforced in this slice:
- `mounting_scope` becomes confirmed only when it is explicitly present and `finish_setup.confirmed = true`
- missing `mounting_scope` stays blocked with `MOUNTING_SCOPE_MISSING`
- no fallback from `mounting_system`
- no fallback from `support_type`
- no fallback from template label or UI zone

Files changed:
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_finish_truth_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/form_system_contract_mapping_adapter_service.py`
- `backend/tests/test_finish_target_runtime_capture.py`
- `backend/tests/test_form_system_contract_backbone.py`
- `backend/tests/test_form_system_contract_mapping_adapter.py`
- `backend/tests/test_intake_v4_finish_truth.py`

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py -q
```

Expected result for this slice:
- focused runtime capture tests green

Still blocked after this slice:
- no backend runtime field yet for `support_type`
- no downstream Quote/Order/Execution/ProductAggregate/TaskGraph consumer for `mounting_scope`