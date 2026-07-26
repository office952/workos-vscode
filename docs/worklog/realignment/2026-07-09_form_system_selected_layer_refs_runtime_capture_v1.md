# Form System Selected Layer Refs Runtime Capture V1

Verdict: PASS

HEAD before implementation:
- `b780edf`

Scope:
- minimal runtime capture for `svg.selected_layer_group -> svg.selected_layer_refs[]`
- no UI visual change
- no Pricing
- no DB migration
- no seed
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph changes
- no new endpoint

Implemented:
- extended workspace payload schema with `svg.selected_layer_refs[]`
- added typed runtime models for selected layer refs
- derived selected refs only from complete + operator-confirmed `layer_role_setup`
- fail-closed behavior when source is missing, unconfirmed, or ambiguous
- synchronized selected refs in both V4 and V6 workspace services whenever `layer_role_setup` is written
- added payload-aware runtime overlay in Form System backbone and mapping adapter for `svg.selected_layer_group`

Runtime payload shape:

```json
{
  "svg": {
    "selected_layer_refs": [
      {
        "layer_id": "face-1",
        "role": "vector_litere",
        "source": "operator_confirmed_layer_role",
        "confirmed": true
      }
    ]
  }
}
```

Derivation policy:
- source of truth is `layer_role_setup`
- setup must be `confirmation_status = complete`
- layer row must be `confirmation_state = confirmed`
- only semantic selected-layer roles are accepted in this slice
- stable `layer_id` is required
- no fallback from `layer_name`
- no fallback from array index
- duplicate or missing stable ids fail closed as ambiguous

Invalidation policy:
- if `layer_role_setup` is partial/unconfirmed, `selected_layer_refs[]` is not persisted
- if SVG reupload/reanalysis invalidates the source, `selected_layer_refs[]` is cleared
- if setup becomes ambiguous, `selected_layer_refs[]` is cleared

Projection behavior:
- static backbone behavior remains unchanged when no runtime payload is supplied
- payload-aware backbone calls now treat persisted selected refs as runtime truth for `svg.selected_layer_group`
- payload-aware adapter calls mirror the backbone runtime state for the same field
- missing/unconfirmed/ambiguous payload states map to explicit blockers:
  - `SELECTED_LAYER_REFS_MISSING`
  - `SELECTED_LAYER_REFS_UNCONFIRMED`
  - `SELECTED_LAYER_REFS_AMBIGUOUS`
- legacy broader blocker `SELECTED_FACE_LAYER_MISSING` remains in the default static contract surface

Files changed:
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_layer_role_service.py`
- `backend/services/intake_v4_workspace_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/form_system_contract_mapping_adapter_service.py`
- `backend/tests/test_form_system_contract_backbone.py`
- `backend/tests/test_form_system_contract_mapping_adapter.py`
- `backend/tests/test_selected_layer_refs_runtime_capture.py`

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_selected_layer_refs_runtime_capture.py -q
```

Result:
- `30 passed`

Still blocked after this slice:
- component-level mapping from selected refs toward face/return/finish ownership remains later
- finish/support/mounting canonical runtime fields remain separate future slices
- no endpoint/read model exposure yet

Recommended next prompt:
- `FORM_SYSTEM_FINISH_TARGET_RUNTIME_CAPTURE_V1`