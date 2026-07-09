# Form System Runtime Capture Series Recheck Final V1

Verdict: READY

HEAD before final recheck:
- `134f986`

Scope:
- final docs + tests recheck of the full Form System runtime capture series
- no endpoint
- no UI
- no Pricing
- no DB
- no seed live
- no migration
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph
- no runtime rewrite

Series confirmed in final recheck:
- `svg.selected_layer_refs[]`
- `finish_setup.finish_target`
- `finish_setup.artwork_finishes[].print_required`
- `finish_setup.artwork_finishes[].lamination_required`
- `finish_setup.mounting_scope`
- `finish_setup.support_type`

Final audit summary:
- `svg.selected_layer_refs[]` is a real runtime field, persisted in payload and backed by a dedicated persistence test that now runs in the focused backend suite.
- `finish_setup.finish_target` remains a real runtime field and only becomes confirmed when explicitly persisted and `finish_setup.confirmed = true`.
- `finish_setup.artwork_finishes[].print_required` remains row-level only and is not promoted to a global finish field.
- `finish_setup.artwork_finishes[].lamination_required` remains row-level only and is not promoted to a global finish field.
- `finish_setup.mounting_scope` remains separate from `mounting_system` and `support_type`.
- `finish_setup.support_type` remains separate from `support_required`, `mounting_system`, `mounting_scope`, and SVG evidence.

Fail-closed summary:
- missing values remain blocked
- unconfirmed values do not become confirmed runtime truth
- no suggested/default/probe/hydrated signal silently upgrades into confirmed truth
- no fallback was found from label, UI zone, template label, array index, `mounting_system`, `support_required`, or SVG evidence in the audited series

Runtime capture matrix:

| field | runtime source | Product Truth projection path | confirmation rule | blockers | ready_for_read_model |
|---|---|---|---|---|---|
| `svg.selected_layer_refs[]` | persisted `svg.selected_layer_refs[]` synchronized from confirmed `layer_role_setup` | `svg.selected_layer_refs[]` | `layer_role_setup.confirmation_status = complete` and selected layer rows require stable `layer_id` + `confirmation_state = confirmed` | `SELECTED_LAYER_REFS_MISSING`, `SELECTED_LAYER_REFS_UNCONFIRMED`, `SELECTED_LAYER_REFS_AMBIGUOUS` | `yes` |
| `finish.finish_target` | `finish_setup.finish_target` | `components.finish.target` | explicit persisted value and `finish_setup.confirmed = true` | `FINISH_TARGET_MISSING` / static backbone `FACE_FINISH_TARGET_MISSING` | `yes` |
| `finish.print_required` | `finish_setup.artwork_finishes[].print_required` | `components.artwork.items[].printRequired` | explicit value on every persisted artwork row and row confirmed or `finish_setup.confirmed = true` | `PRINT_REQUIRED_UNKNOWN` | `yes` |
| `finish.lamination_required` | `finish_setup.artwork_finishes[].lamination_required` | `components.artwork.items[].laminationRequired` | explicit value on every persisted artwork row and row confirmed or `finish_setup.confirmed = true` | `LAMINATION_REQUIRED_UNKNOWN` | `yes` |
| `mounting.mounting_scope` | `finish_setup.mounting_scope` | `components.mounting.mountingScope` | explicit persisted value and `finish_setup.confirmed = true` | `MOUNTING_SCOPE_MISSING` | `yes` |
| `support.support_type` | `finish_setup.support_type` | `components.support.supportType` | explicit persisted value and `finish_setup.confirmed = true` | `SUPPORT_TYPE_MISSING` | `yes` |

Tests run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py tests/test_selected_layer_refs_runtime_capture.py -q
```

Result:
- `70 passed, 20 warnings in 3.48s`

Read-model readiness decision:
- `READY`

Decision rationale:
- the full focused runtime-capture suite now passes with the selected-layer persistence coverage included
- all six runtime fields have explicit canonical runtime sources, explicit blocker states, and stable Product Truth projection paths
- the remaining downstream gaps are consumer gaps only; they are not blockers for a minimal read-only runtime capture read-model

First correct next task:
- `FORM_SYSTEM_RUNTIME_CAPTURE_READ_MODEL_V1`

Constraints preserved:
- no UI changes
- no Pricing changes
- no DB changes
- no live seed changes
- no migration
- no endpoint in this task
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph changes
- no runtime rewrite

Files changed:
- `docs/worklog/realignment/2026-07-09_form_system_runtime_capture_series_recheck_final_v1.md`