# Form System Contract Fields Runtime Source Alignment V1

Verdict: READY

Accepted HEAD:
- `8cc626d`

Safety gate:
- `git status -sb`: dirty worktree with unrelated pre-existing untracked files
- `git rev-parse --short HEAD`: `8cc626d`
- `git diff --cached --name-only`: empty before this docs-only plan slice
- `git diff --check`: clean before edits

Scope:
- audit + implementation planning only
- no runtime writer implementation in this slice
- no UI
- no Pricing
- no DB
- no seed
- no migration
- no endpoint exposure
- no Quote/Order/Execution changes

Purpose:
- align the next implementation order for canonical runtime source capture of the six Form System contract fields already mapped by the read-only adapter
- choose one first field only for the next implementation slice

Sources reviewed:
- `docs/worklog/realignment/2026-07-09_form_system_contract_adapter_runtime_source_audit_v1.md`
- `backend/services/form_system_contract_mapping_adapter_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/schemas/intake_v4.py`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `docs/architecture/product-system/FORM_SYSTEM_FIELD_CONTRACT_MAP.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`

## Alignment Decisions

### 1. `svg.selected_layer_group`

- target canonical runtime source: explicit operator-confirmed selected layer/group refs derived from existing `layer_role_setup` rows
- runtime capture surface: backend workspace payload, adjacent to `layer_role_setup` and `layer_role_review`, not inside Pricing or ProductDefinition
- owner: `svg_layer_roles` at capture time; later consumed by face / return / finish boundaries
- payload path to extend: `payload.product_truth_context.selected_layer_refs[]` is not recommended; prefer workspace-root canonical capture path aligned with backbone contract: `payload.svg.selected_layer_refs[]` equivalent runtime subtree, or a first-class `selected_layer_refs[]` path near `layer_role_setup` that the backbone can truthfully project to `svg.selected_layer_refs[]`
- confirmation required: yes, explicit operator confirmation
- evidence-only remaining after first slice: analyzer suggested roles, auto-detected face/artwork candidates, any unconfirmed group-to-component mapping
- tests needed: focused backend persistence + reread tests; clear-on-reanalysis safety; no invention when no operator selection exists; backbone/adapter projection remains `missing` until refs exist, then changes to confirmed/available evidence-safe state

Decision: this is the first recommended implementation field because it already has owner, blocker, backbone row, and a backend-adjacent source family (`layer_role_setup`) that can be extended without inventing a new finish/support payload model first.

### 2. `finish.finish_target`

- target canonical runtime source: explicit operator-confirmed finish target selection per active finish path
- runtime capture surface: `finish_setup` payload extension in backend schema and workspace persistence
- owner: `finish_artwork`
- payload path to extend: backend runtime payload should add first-class `finish_setup.finish_target`; Product Truth target remains `components.finish.target`
- confirmation required: yes
- evidence-only remaining after first slice: UI zone implication, target inferred from face/cant/artwork card placement, any stage/process-specific downstream consequence
- tests needed: schema acceptance; persistence; missing blocker when finish active and target absent; no fallback from UI zone; adapter/backbone projection alignment

Decision: not first because although ownership is clear, the field still requires schema expansion and it is coupled to target naming alignment (`target` vs `finishTarget`) and downstream finish scope policy.

### 3. `finish.print_required`

- target canonical runtime source: explicit per-artwork-row or per-finish-scope operator boolean, not execution-type decoding
- runtime capture surface: `finish_setup.artwork_finishes[]` first, with later aggregation/read model into `components.finish.printRequired` if needed
- owner: `finish_artwork`
- payload path to extend: backend `IntakeV4ArtworkFinish` / `finish_setup.artwork_finishes[].print_required`
- confirmation required: yes when artwork path is commercially active
- evidence-only remaining after first slice: execution_type-derived suggestion, analyzer printed-artwork hints, grouped finish aggregation
- tests needed: persistence of explicit booleans; no silent derivation when missing; blocker/warning alignment for artwork decision gaps; aggregated projection tests if a read surface is added later

Decision: not first because its safest canonical source is artwork-row scoped, not global finish scoped, and it depends on clarifying the row truth model before any root-level projection.

### 4. `finish.lamination_required`

- target canonical runtime source: explicit per-artwork-row or per-finish-scope operator boolean, separate from print
- runtime capture surface: `finish_setup.artwork_finishes[]`
- owner: `finish_artwork`
- payload path to extend: backend `IntakeV4ArtworkFinish` / `finish_setup.artwork_finishes[].lamination_required`
- confirmation required: yes when print/policy path is active
- evidence-only remaining after first slice: execution_type encoding, default `print_laminate` implication
- tests needed: persistence; separation from `print_required`; lamination-without-print policy warnings; no invention from encoded execution types

Decision: not first because it should follow the same row-level truth capture shape as `print_required`, and separating the pair across slices would create asymmetry.

### 5. `support.support_type`

- target canonical runtime source: explicit operator selection after support requirement is known, not mounting bridge inference
- runtime capture surface: `finish_setup` extension or a dedicated support subtree in workspace payload; do not piggyback only on `mounting_system`
- owner: `mounting_support`
- payload path to extend: `finish_setup.support_type` and likely `finish_setup.support_required` + `finish_setup.support_source`
- confirmation required: yes when support is active/suspected
- evidence-only remaining after first slice: `mounting_system` bar evidence, SVG support hints, `metal_support_required` product-definition consequence
- tests needed: explicit support-required/type persistence; no silent inference from `mounting_system`; warnings for evidence-only bridge; alignment with component ownership contract

Decision: not first because the field is structurally dependent on `support_required`, and the current codebase explicitly treats support bridge inference as non-canonical.

### 6. `mounting.mounting_scope`

- target canonical runtime source: explicit operator commercial scope choice
- runtime capture surface: `finish_setup` payload extension in backend schema and workspace persistence
- owner: `mounting_support`
- payload path to extend: `finish_setup.mounting_scope`
- confirmation required: yes
- evidence-only remaining after first slice: `mounting_system`, template area/material, site notes
- tests needed: schema acceptance and persistence; blocker when absent; no fallback beyond `to_be_decided`; adapter projection tests

Decision: not first because it requires adding a brand-new backend payload field with no adjacent existing backend truth row other than the broader mounting hydration row.

## Runtime Source Alignment Matrix

| field_key | target_runtime_source | payload_path | owner | first_implementation_slice | tests_needed | risk |
|---|---|---|---|---|---|---|
| `svg.selected_layer_group` | operator-confirmed selected refs from existing layer-role workflow | canonical runtime capture aligned to `svg.selected_layer_refs[]` near `layer_role_setup` | `svg_layer_roles` | add explicit selected layer refs capture + persistence + backbone projection recheck | persistence, clear/rerun safety, no-invention, projection/readiness tests | lowest of the six; still has mapping-boundary risk to face/return ownership |
| `finish.finish_target` | explicit operator target selection | `finish_setup.finish_target` | `finish_artwork` | add first-class finish target payload field and align target naming | schema/persistence/blocker/projection tests | medium; naming split and target scope policy |
| `finish.print_required` | explicit artwork-row boolean | `finish_setup.artwork_finishes[].print_required` | `finish_artwork` | row-level boolean capture before any aggregated finish truth | schema/persistence/no-derivation/policy tests | medium-high; aggregation ambiguity if done too early |
| `finish.lamination_required` | explicit artwork-row boolean | `finish_setup.artwork_finishes[].lamination_required` | `finish_artwork` | capture together with print boolean, not separately | schema/persistence/separation/policy tests | medium-high; tied to print model |
| `support.support_type` | explicit support selection after support-required decision | `finish_setup.support_type` plus companion support fields | `mounting_support` | support subtree capture after support-required contract alignment | schema/persistence/no-bridge-inference tests | high; current bridge is explicitly non-canonical |
| `mounting.mounting_scope` | explicit operator commercial mounting scope | `finish_setup.mounting_scope` | `mounting_support` | payload field capture after or alongside broader mounting truth cleanup | schema/persistence/blocker/projection tests | medium; field is simple but currently isolated from backend payload |

## First Recommended Implementation Field

Recommended first field:
- `svg.selected_layer_group` via canonical runtime capture of `selected_layer_refs[]`

Why this first:
- owner already exists in backbone: `svg_layer_roles`
- blocker already exists: `SELECTED_FACE_LAYER_MISSING`
- target path already exists in backbone and adapter: `svg.selected_layer_refs[]`
- runtime neighborhood already exists in backend payload: `layer_role_setup`, `layer_role_review`, SVG analyzer bundle
- does not require inventing a new finish/support/mounting backend subtree before proving the capture pattern
- lets the next slice validate the canonical pattern: evidence -> operator confirmation -> persisted runtime field -> backbone/adapter projection

## Why Not The Other Fields First

- `finish.finish_target`: clear owner, but still needs backend schema expansion and target naming unification.
- `finish.print_required`: real canonical source should be row-level artwork truth, not root aggregation; doing it first risks encoding the wrong abstraction.
- `finish.lamination_required`: same dependency as print, and should be captured together.
- `support.support_type`: depends on first-class `support_required` and explicit separation from mounting bridge evidence.
- `mounting.mounting_scope`: straightforward field, but there is no existing backend runtime anchor beyond broad mounting hydration; it is less anchored than selected-layer capture.

## Minimal Next Slice Recommendation

Name:
- `FORM_SYSTEM_SELECTED_LAYER_REFS_RUNTIME_CAPTURE_V1`

Expected narrow scope for that slice:
- backend schema alignment only for selected layer refs
- workspace persistence path only
- backbone/adapter state alignment only
- focused tests only
- no endpoint exposure yet

Validation expectation for this planning slice:
- docs only
- `git diff --check`
