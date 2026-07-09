# Form System Finish Target Runtime Capture V1

Verdict: PASS

HEAD before implementation:
- `37b66ba`

Scope:
- minimal runtime capture for `finish.finish_target`
- no UI visual change
- no Pricing
- no DB migration
- no seed
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph changes
- no new endpoint

Canonical naming decision:
- runtime payload field is `finish_setup.finish_target`
- Product Truth/projection path remains `components.finish.target`
- `finishTarget` is not persisted as a competing runtime name

Implemented:
- extended backend finish setup schema with first-class `finish_target`
- kept persistence inside the existing `save_finish_setup` path; no new writer surface added
- added payload-aware runtime overlay in the Form System backbone for `face.finish_artwork_target`
- added payload-aware runtime overlay in the mapping adapter for `finish.finish_target`
- preserved default static blocked behavior when no runtime payload is supplied

Runtime payload shape:

```json
{
  "finish_setup": {
    "face_finish_type": "oracal_8500",
    "finish_target": "face",
    "confirmed": true
  }
}
```

Rules enforced in this slice:
- runtime confirmation only when `finish_setup.finish_target` exists and `finish_setup.confirmed = true`
- missing `finish_target` remains blocked
- unconfirmed finish setup does not become confirmed runtime truth
- no target inference from UI zone or template label
- no second runtime key such as `finishTarget`

Projection behavior:
- backbone static field `face.finish_artwork_target` stays unchanged by default
- when payload runtime exists and finish setup is confirmed, backbone reads runtime source and marks the field confirmed
- adapter reads the same runtime payload and upgrades `finish.finish_target` to `source = payload_persisted`, `state = confirmed`
- if payload is missing or unconfirmed, adapter remains blocked with `FINISH_TARGET_MISSING`

Files changed:
- `backend/schemas/intake_v4.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/form_system_contract_mapping_adapter_service.py`
- `backend/services/intake_v6_layer_role_service.py`
- `backend/tests/test_form_system_contract_backbone.py`
- `backend/tests/test_form_system_contract_mapping_adapter.py`
- `backend/tests/test_finish_target_runtime_capture.py`

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py -q
```

Result:
- `32 passed`

Still blocked after this slice:
- row-level canonical runtime capture for `print_required` and `lamination_required`
- support runtime truth remains separate from mounting bridge evidence
- `mounting_scope` remains unimplemented in backend payload
- no endpoint/read model exposure yet

Recommended next prompt:
- `FORM_SYSTEM_PRINT_LAMINATION_RUNTIME_CAPTURE_V1`