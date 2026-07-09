# Form System Runtime Capture Read Model Endpoint V1

Verdict: PASS

HEAD before implementation:
- `2122cfe`

Scope:
- expose the existing Form System runtime capture read-model through one minimal backend read-only endpoint
- no UI
- no Pricing
- no DB migration/schema change
- no seed live
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph
- no Product Truth write
- no new writer

Route chosen:
- `GET /api/v1/intake-v6/workspaces/{workspace_id}/runtime-capture-read-model`

Why this route:
- the read-model is scoped to an existing Intake V6 workspace payload
- `intake_v6_workspaces` already contains neighboring read-only workspace routes such as linked-template runtime segments and letter-group finish readiness
- the route can stay minimal: fetch workspace, read payload, project read-model, return read-only envelope

Implementation:
- added a thin workspace-scoped helper in `backend/services/intake_v6_workspace_service.py`
- helper reuses `get_intake_v6_workspace(...)` plus `build_form_system_runtime_capture_read_model(...)`
- added endpoint in `backend/routers/intake_v6_workspaces.py`
- no payload mutation, no Product Truth write, no downstream write intent

Endpoint shape:

```json
{
  "read_only": true,
  "workspace_id": "...",
  "workspace_record_id": "...",
  "workspace_code": "...",
  "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "read_model_version": "v1",
  "fields": [
    {
      "field_key": "finish.finish_target",
      "runtime_source": "finish_setup.finish_target",
      "product_truth_path": "components.finish.target",
      "state": "confirmed",
      "confirmation_rule": "Explicit persisted finish_setup.finish_target and finish_setup.confirmed=true.",
      "blockers": [],
      "ready_for_product_truth": true
    }
  ],
  "blockers": [],
  "downstream_write_intent": {
    "pricing_write": false,
    "quote_write": false,
    "order_write": false,
    "product_definition_write": false,
    "product_aggregate_write": false,
    "task_graph_write": false,
    "execution_runtime_write": false,
    "inventory_movement": false,
    "db_write": false
  }
}
```

Tests added:
- endpoint returns all six runtime capture fields for a complete payload
- endpoint marks all six fields confirmed when payload is complete
- missing runtime inputs remain blocked without fallback
- endpoint remains read-only and exposes no Pricing / Quote / Execution coupling
- missing workspace returns controlled `404`

Validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_runtime_capture_read_model.py tests/test_form_system_runtime_capture_read_model_endpoint.py -q
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py tests/test_selected_layer_refs_runtime_capture.py tests/test_form_system_runtime_capture_read_model.py -q
```

Files changed:
- `backend/services/intake_v6_workspace_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/tests/test_form_system_runtime_capture_read_model_endpoint.py`
- `docs/worklog/realignment/2026-07-09_form_system_runtime_capture_read_model_endpoint_v1.md`