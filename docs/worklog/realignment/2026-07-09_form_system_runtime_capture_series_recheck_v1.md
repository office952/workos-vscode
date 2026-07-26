# Form System Runtime Capture Series Recheck V1

Verdict: BLOCKED

HEAD before recheck:
- `87181d0`

Scope:
- short recheck of the complete Form System runtime capture series
- audit + focused test re-run only
- no UI
- no Pricing
- no DB
- no seed
- no migration
- no endpoint
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph

Series audited:
- `svg.selected_layer_refs[]`
- `finish_setup.finish_target`
- `finish_setup.artwork_finishes[].print_required`
- `finish_setup.artwork_finishes[].lamination_required`
- `finish_setup.mounting_scope`
- `finish_setup.support_type`

Mandatory read recheck summary:
- `selected_layer_refs[]` remains a real runtime field anchored in persisted payload `svg.selected_layer_refs[]`, not evidence-only.
- `finish_target` remains a real runtime field only when `finish_setup.finish_target` exists and `finish_setup.confirmed = true`.
- `print_required` remains row-level only on `finish_setup.artwork_finishes[]` and is not promoted to a global finish field.
- `lamination_required` remains row-level only on `finish_setup.artwork_finishes[]` and is not promoted to a global finish field.
- `mounting_scope` remains separate from `mounting_system` and `support_type`.
- `support_type` remains separate from `support_required`, `mounting_system`, `mounting_scope`, and SVG evidence.

Fail-closed recheck summary:
- missing values remain blocked across all six runtime fields
- unconfirmed values do not become confirmed runtime truth
- suggested, fallback, hydrated, or probe-like values do not silently upgrade
- no fallback was found from label, UI zone, template label, array index, `mounting_system`, `support_required`, or SVG evidence in the audited backbone/adapter surfaces

Coupling recheck summary:
- no UI coupling found in the audited backend runtime capture surfaces
- no Pricing coupling found in the audited backbone/adapter surfaces
- no Quote/Order/Execution coupling found in the audited backbone/adapter surfaces
- no ProductAggregate/TaskGraph coupling found in the audited backbone/adapter surfaces
- no DB migration or seed dependency is required for the finish-target / print-lamination / mounting-scope / support-type runtime fields themselves
- explicit `downstream_write_intent` remains all-false in both backbone and mapping adapter read-only services

Runtime capture matrix:

| field | runtime source | Product Truth projection path | confirmation rule | blockers | ready_for_read_model |
|---|---|---|---|---|---|
| `svg.selected_layer_refs[]` | `svg.selected_layer_refs[]` synchronized from confirmed `layer_role_setup` | `svg.selected_layer_refs[]` | `layer_role_setup.confirmation_status = complete` and each selected row has stable `layer_id` + `confirmation_state = confirmed` | `SELECTED_LAYER_REFS_MISSING`, `SELECTED_LAYER_REFS_UNCONFIRMED`, `SELECTED_LAYER_REFS_AMBIGUOUS` | `blocked_by_recheck_gap` |
| `finish.finish_target` | `finish_setup.finish_target` | `components.finish.target` | explicit persisted value and `finish_setup.confirmed = true` | `FINISH_TARGET_MISSING` / backbone static `FACE_FINISH_TARGET_MISSING` | `yes` |
| `finish.print_required` | `finish_setup.artwork_finishes[].print_required` | `components.artwork.items[].printRequired` | explicit value on every persisted artwork row and row confirmed or `finish_setup.confirmed = true` | `PRINT_REQUIRED_UNKNOWN` | `yes` |
| `finish.lamination_required` | `finish_setup.artwork_finishes[].lamination_required` | `components.artwork.items[].laminationRequired` | explicit value on every persisted artwork row and row confirmed or `finish_setup.confirmed = true` | `LAMINATION_REQUIRED_UNKNOWN` | `yes` |
| `mounting.mounting_scope` | `finish_setup.mounting_scope` | `components.mounting.mountingScope` | explicit persisted value and `finish_setup.confirmed = true` | `MOUNTING_SCOPE_MISSING` | `yes` |
| `support.support_type` | `finish_setup.support_type` | `components.support.supportType` | explicit persisted value and `finish_setup.confirmed = true` | `SUPPORT_TYPE_MISSING` | `yes` |

Tests run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py -q
```

Result:
- `66 passed, 20 warnings in 3.29s`

Optional selected-layer runtime test attempt:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py tests/test_selected_layer_refs_runtime_capture.py -q
```

Result:
- mandatory four-file slice still passed (`66 passed`)
- `tests/test_selected_layer_refs_runtime_capture.py` failed at fixture setup with 4 errors
- failure shape:
  - `TypeError: 'NoneType' object is not callable`
  - source: `seeds/seed_build4_templates.py` via `db_manager.async_session_maker()` being unset during test setup

Read-model readiness decision:
- `NOT_READY`

Reason:
- the runtime capture contract itself is coherent and fail-closed for all six fields, but the series recheck is not fully green because the dedicated persistence test for `selected_layer_refs[]` is not currently runnable in the present backend test setup
- until that proof path is green again, the series should not be promoted as fully closed for a new minimal read-model slice

First correct minimal read-model after blocker removal:
- a read-only backend service that summarizes the six runtime capture fields from an existing workspace payload, exposing: field key, persisted source path, current value/state, blocker code, and Product Truth projection path
- no new writes, no pricing, no quote/order/execution, no ProductAggregate/TaskGraph

Single blocker to resolve next:
- restore a runnable focused persistence test path for `svg.selected_layer_refs[]` by fixing the selected-layer runtime test setup so it no longer depends on an uninitialized global seed session maker

Files changed:
- `docs/worklog/realignment/2026-07-09_form_system_runtime_capture_series_recheck_v1.md`