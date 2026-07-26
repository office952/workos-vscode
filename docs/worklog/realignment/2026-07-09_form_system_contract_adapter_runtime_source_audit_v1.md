# Form System Contract Adapter Runtime Source Audit V1

Verdict: PASS

Accepted HEAD:
- `30d9bab`

Safety gate:
- `git status -sb`: dirty worktree with unrelated untracked files already present before this audit
- `git rev-parse --short HEAD`: `30d9bab`
- `git diff --cached --name-only`: empty before this docs-only audit
- `git diff --check`: clean before edits

Scope:
- audit only
- no backend/runtime implementation
- no UI
- no Pricing
- no DB
- no seed
- no migration
- no endpoint exposure

Goal:
- inspect real runtime sources for the 6 fields currently mapped by the read-only Form System contract adapter
- decide whether any field is ready for endpoint/read model exposure before a source-alignment slice

Key findings:
- the adapter is correct as a read-only contract surface, but it does not prove runtime source completeness
- `finish.print_required`, `finish.lamination_required`, `finish.finish_target`, `support.support_type`, and `mounting.mounting_scope` are not first-class backend workspace payload fields today
- those five fields exist mainly as frontend Product Truth draft input semantics and/or documented target contracts
- `svg.selected_layer_group` is the only field with an existing backend Form System backbone row, but its canonical truth path `svg.selected_layer_refs[]` is still a contract target rather than a persisted runtime payload field
- component linkage exists for finish and mounting/support through shared component contracts and backbone component ownership
- `svg.selected_layer_group` is product-context / svg-layer-role owned, not component-template-owned

Runtime source matrix:

| field_key | current_runtime_source | owner | product_truth_path | confirmation_required | current_state | blocker | next_action |
|---|---|---|---|---|---|---|---|
| `finish.print_required` | frontend draft only: `artwork_finishes[].print_required` when probe input supplies it, otherwise derived from `artwork_finishes[].execution_type` in `productTruthDraftBuilder` | `finish_artwork` via `VOLUMETRIC_FINISH_TEMPLATE_CODE` linkage | `components.finish.printRequired` is target path only; not a backend workspace payload field today | yes when artwork path active | `draft` | `PRINT_REQUIRED_UNKNOWN`; backend payload/schema missing; execution_type encoding is not canonical truth | align canonical runtime source and payload field before any endpoint/read model |
| `finish.lamination_required` | frontend draft only: `artwork_finishes[].lamination_required` when probe input supplies it, otherwise derived from `artwork_finishes[].execution_type` in `productTruthDraftBuilder` | `finish_artwork` via `VOLUMETRIC_FINISH_TEMPLATE_CODE` linkage | `components.finish.laminationRequired` is target path only; not a backend workspace payload field today | yes when print/policy path active | `draft` | `LAMINATION_REQUIRED_UNKNOWN`; backend payload/schema missing; still encoded through execution_type | align canonical runtime source and payload field before any endpoint/read model |
| `finish.finish_target` | frontend draft/probe input `finish.finish_target`; otherwise only implicit UI-zone meaning and docs/backbone target row | `finish_artwork` via `VOLUMETRIC_FINISH_TEMPLATE_CODE` linkage | backbone target `components.finish.target`; not a backend workspace payload field today | yes | `blocked` | `FINISH_TARGET_MISSING`; path naming split between contract `target` and draft `finishTarget`; no backend payload field | unify target path and define first-class runtime capture before exposure |
| `support.support_type` | frontend draft/probe input `finish.support_type`; otherwise only bridge evidence from `mounting_system` and SVG support hints in `productTruthDraftBuilder` | `mounting_support` via `STRUCTURE_PREMOUNT_TEMPLATE_CODE` linkage | `components.support.supportType` is target path only; not a backend workspace payload field today | yes when support active/suspected | `blocked` | `SUPPORT_TYPE_MISSING`; current source is bridge evidence, not canonical support truth | perform support runtime-source and payload alignment before exposure |
| `mounting.mounting_scope` | frontend draft/probe input `finish.mounting_scope`; otherwise draft defaults to `to_be_decided` | `mounting_support` via `STRUCTURE_PREMOUNT_TEMPLATE_CODE` linkage | `components.mounting.mountingScope` is target path only; not a backend workspace payload field today | yes | `blocked` | `MOUNTING_SCOPE_MISSING`; documented-not-implemented; current Intake V6 backend schema has `mounting_system` but not `mounting_scope` | add canonical runtime source/payload contract before any endpoint/read model |
| `svg.selected_layer_group` | backend backbone + `layer_role_setup` / SVG analyzer/operator role evidence; frontend awareness/projection can display it, but no persisted `selected_layer_refs[]` field exists in workspace payload schema | `svg_layer_roles` product-context owner; no component template linkage | `svg.selected_layer_refs[]` is contract target path; not a backend schema field today | yes | `missing` with suggestion/evidence nearby | `SELECTED_FACE_LAYER_MISSING`; no canonical persisted selected layer refs | define explicit selected-layer capture/alignment before exposing as truth read model |

Field-by-field audit notes:

## `finish.print_required`

- appears in frontend draft input types and draft builder logic
- does not appear as a first-class backend schema field in `IntakeV4FinishSetup`
- current real source is artwork execution semantics, not canonical operator-captured truth
- component linkage exists through the finish/artwork reusable component contract
- confirmation policy is clear in docs: explicit boolean required when artwork/print path matters

## `finish.lamination_required`

- same shape as `print_required`
- current real source is execution-type-derived or probe-provided draft input only
- not present as first-class backend schema/runtime field
- confirmation policy is clear in docs, but runtime source is still insufficient

## `finish.finish_target`

- exists as desired contract field in backbone/docs and as draft input in frontend Product Truth types
- not present in backend `finish_setup` schema
- current runtime semantics are partially implied by UI zone separation rather than explicit payload truth
- component linkage exists through `volumetric_surface_finish`
- blocker remains canonical target capture and naming/path alignment

## `support.support_type`

- documented target field with clear owner and values
- current runtime logic only suggests support via mounting bridge or SVG support evidence unless probe input explicitly supplies `support_type`
- not present in backend `finish_setup` schema
- component linkage exists through `volumetric_mounting_interface`
- should not be exposed before support truth is separated from mounting truth

## `mounting.mounting_scope`

- documented values and policy exist in docs
- current runtime source is draft-only/probe-only
- backend schema contains `mounting_system`, not `mounting_scope`
- component linkage exists through mounting/support contract, but runtime payload does not
- should remain blocked until explicit capture exists

## `svg.selected_layer_group`

- exists in backend backbone today with owner, blocker, and target path
- current source is layer-role/operator evidence from `layer_role_setup`, not canonical persisted `selected_layer_refs[]`
- not component-template-owned; it is a product-context/svg-layer-role boundary field
- this is the closest field to a backend read surface, but still not ready as canonical truth output

Decision:
- fields ready for endpoint/read model now: none as canonical runtime truth fields
- closest field to future read exposure: `svg.selected_layer_group`, but only as evidence/readiness status, not as canonical truth
- fields with insufficient runtime source: all six; the first five because they are draft/probe/doc-level only, and `svg.selected_layer_group` because canonical selected refs are not persisted
- fields needing Product Template / Component Template linkage clarification: `finish.*`, `support.support_type`, `mounting.mounting_scope`
- field that must not be exposed yet: all six as canonical truth read model fields

Why endpoint/read model is not next:
- an endpoint now would mainly expose target contract rows, not owner-safe runtime source truth
- this would overstate runtime maturity and blur evidence vs confirmed truth boundaries

Recommended next prompt:
- `FORM_SYSTEM_CONTRACT_FIELDS_RUNTIME_SOURCE_ALIGNMENT_V1`