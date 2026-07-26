# Form System Print Lamination Runtime Capture V1

Verdict: PASS

HEAD before implementation:
- `9bce190`

Scope:
- minimal runtime capture for `finish.print_required`
- minimal runtime capture for `finish.lamination_required`
- row-level only on `finish_setup.artwork_finishes[]`
- no UI visual change
- no Pricing
- no DB migration
- no seed
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph changes
- no new endpoint

Canonical payload decision:
- row-level fields are persisted on `finish_setup.artwork_finishes[].print_required`
- row-level fields are persisted on `finish_setup.artwork_finishes[].lamination_required`
- no global `finish_setup.print_required`
- no global `finish_setup.lamination_required`
- no fallback inference from template label, UI zone, or default

Read-only projection decision:
- adapter `finish.print_required` now points to `components.artwork.items[].printRequired`
- adapter `finish.lamination_required` now points to `components.artwork.items[].laminationRequired`
- backbone fields with the same keys read only persisted row booleans
- runtime confirmation requires explicit values on every persisted artwork finish row plus `finish_setup.confirmed = true` or row-level `confirmed = true`

Implemented:
- extended `IntakeV4ArtworkFinish` with `print_required` and `lamination_required`
- added fail-closed runtime helper for artwork row booleans
- added backbone runtime overlay for row-level print/lamination source reads
- updated mapping adapter to stop pointing at aggregated finish-level paths
- kept missing or unconfirmed rows blocked with `PRINT_REQUIRED_UNKNOWN` / `LAMINATION_REQUIRED_UNKNOWN`

Payload shape:

```json
{
  "finish_setup": {
    "confirmed": true,
    "artwork_finishes": [
      {
        "layer_key": "logo-left",
        "print_required": true,
        "lamination_required": false
      },
      {
        "layer_key": "logo-right",
        "print_required": false,
        "lamination_required": true
      }
    ]
  }
}
```

Rules enforced in this slice:
- no global aggregation is persisted
- missing row value remains blocked
- explicit but unconfirmed row value does not become confirmed
- runtime source is row-level only
- finish/execution/pricing/product aggregate scopes remain untouched

Files changed:
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_finish_truth_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/form_system_contract_mapping_adapter_service.py`
- `backend/tests/test_intake_v4_finish_truth.py`
- `backend/tests/test_form_system_contract_backbone.py`
- `backend/tests/test_form_system_contract_mapping_adapter.py`
- `backend/tests/test_finish_target_runtime_capture.py`

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_print_lamination_runtime_capture.py tests/test_intake_v4_finish_truth.py -q
```

Expected result for this slice:
- focused runtime capture tests green

Updated validation command:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py -q
```

Still blocked after this slice:
- no backend runtime field yet for `support_type`
- no backend runtime field yet for `mounting_scope`
- no quote/order/execution consumers for the new row booleans