# Form System Runtime Capture Read Model V1

Verdict: PASS

HEAD before implementation:
- `f07a72c`

Scope:
- minimal backend read-only read-model for the Form System runtime capture series
- no UI
- no Pricing
- no DB migration/schema change
- no seed live
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph
- no Product Truth write
- no endpoint in this task

Read-model shape:
- one minimal service that projects the already-green runtime capture series into a stable read-only envelope
- each field row exposes:
  - `field_key`
  - `runtime_source`
  - `product_truth_path`
  - `state`
  - `confirmation_rule`
  - `blockers[]`
  - `ready_for_product_truth`

Fields included:
- `svg.selected_layer_refs[]`
- `finish.finish_target`
- `finish.print_required`
- `finish.lamination_required`
- `mounting.mounting_scope`
- `support.support_type`

Implementation notes:
- the service reuses `build_form_system_contract_readonly_mapping(...)` as the single runtime/status authority for the six fields
- the read-model adds explicit canonical runtime source paths and explicit confirmation rules
- the service stays fail-closed: any missing adapter exposure becomes `RUNTIME_CAPTURE_FIELD_NOT_EXPOSED`
- print and lamination remain row-level only on `finish_setup.artwork_finishes[]`
- mounting scope remains separate from `mounting_system` and `support_type`
- support type remains separate from `support_required`, `mounting_system`, `mounting_scope`, and SVG evidence

Tests added:
- read-model returns all six runtime fields
- complete confirmed payload marks all six fields confirmed and ready for Product Truth
- missing `selected_layer_refs[]` stays blocked
- missing `finish_target` stays blocked
- missing row-level print / lamination stays blocked
- mounting scope does not fall back to `mounting_system`
- support type does not fall back to `support_required` / mounting / SVG evidence
- no Pricing / Quote / Execution coupling

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py tests/test_selected_layer_refs_runtime_capture.py tests/test_form_system_runtime_capture_read_model.py -q
```

Expected result:
- focused runtime capture suite green with the new read-model test included

Files changed:
- `backend/services/form_system_runtime_capture_read_model_service.py`
- `backend/tests/test_form_system_runtime_capture_read_model.py`
- `docs/worklog/realignment/2026-07-09_form_system_runtime_capture_read_model_v1.md`