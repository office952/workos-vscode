# PRODUCT_TRUTH_PROMOTION_PATH_V1

Status: PRODUCT_TRUTH_PROMOTION_PATH_BLOCKED

Scope: audit + contract alignment + minimum safe implementation slice only.

Boundary:
- no Product Truth writer
- no UI changes
- no Pricing / Quote / Order / Execution work
- no DB / migration / seed work
- no ProductAggregate / TaskGraph work
- no endpoint work

Repo state:
- accepted base HEAD: `81eec9d`
- task started from dirty worktree with unrelated untracked files; ignored per boundary

## Verdict

The canonical promotion path is not safe to implement as a writer yet.

The controlling reason is not missing UI. The controlling reason is that the current surfaces do not share one promotion unit or one canonical path vocabulary:
- the runtime capture read model is fail-closed and path-explicit
- the frontend draft builder still carries `suggested`, `hydrated`, `fallback`, and bridge-derived values in the same object graph as candidate truth
- the ProductDefinition preview builder still reads payload/binding values directly instead of consuming a confirmed Product Truth promotion result
- at least one important component family already demonstrates path-shape drift: backend `product_truth.components.return_cant...` vs draft `components.returnCant...` vs older contract references like `components.return.depth_mm`

Because of that, a direct writer would either:
- over-promote evidence that is not confirmed truth, or
- freeze current path mismatches into persisted Product Truth.

The safe next slice is therefore a read-only promotion planner, not a writer.

## Canonical Promotion Model

Canonical promotion unit:
- write boundary: one workspace-scoped Product Truth Promotion Snapshot
- truth boundary inside the snapshot: one canonical field or row entry at a stable Product Truth path

Rules:
1. Runtime capture and Review state are evidence inputs only. They never become Product Truth by existence alone.
2. Promotion is allowed only for entries whose canonical state is `confirmed`.
3. Row-scoped truth stays row-scoped. No global boolean may replace canonical row booleans for artwork print/lamination.
4. Identity must be stable:
   - selected SVG refs use stable `layer_id` or equivalent confirmed identity
   - artwork rows use stable `layer_key` or a persisted row key
   - letter-group rows use stable `group_key`
5. Missing, blocked, suggested, hydrated, fallback, manual, unknown, or warning states do not enter Product Truth.
6. Computed truth is only promotable later when it is owner-scoped, path-stable, validation-backed, and itself explicitly confirmed by policy.
7. ProductDefinition must consume confirmed Product Truth entries, not reconstruct truth from draft payload fallback logic.

Canonical promotion flow:
1. Intake V6 payload and layer-role evidence are read.
2. Contract mapping resolves owner, source, canonical Product Truth path, and blockers.
3. A promotion planner emits:
   - `eligible_entries[]`
   - `blocked_entries[]`
   - `path_conflicts[]`
   - `identity_conflicts[]`
   - `snapshot_ready`
4. Only a later writer may persist `eligible_entries[]` atomically as a Product Truth snapshot.
5. ProductDefinition and downstream surfaces later read that persisted confirmed snapshot.

## State Matrix

| State | Can enter Product Truth? | Why |
| --- | --- | --- |
| `confirmed` | Yes | Only safe default state for accepted truth. |
| `computed` | Not in current slice | Allowed only later with owner/path/validation/confirmation policy, not present as a safe promotion source now. |
| `suggested` | No | Analyzer evidence only. |
| `hydrated` | No | Persisted or loaded draft input is not confirmed truth. |
| `fallback` | No | Owner default is not operator-confirmed truth. |
| `manual` | No | Manual entry without explicit confirmation remains draft evidence. |
| `blocked` | No | Explicitly missing or invalid. |
| `warning` | No | Warning is diagnostic metadata, not truth state. |
| `unknown` | No | No canonical value. |
| `not_applicable` | No | Gate metadata only. |

## Path Alignment Matrix

| Concern | Contract / runtime capture canonical path | Current draft surface | Current ProductDefinition input | Result |
| --- | --- | --- | --- | --- |
| Selected SVG refs | `svg.selected_layer_refs[]` | `layers[]` with `confirmedRole`, `confirmationState`, `layerKey`; no explicit confirmed selected-ref collection | reads field bindings from payload, not Product Truth | blocked: identity and surface mismatch |
| Finish target | `components.finish.target` | `components.finish.finishTarget` sourced from `finish_setup.finish_target` and blocked when absent | payload/binding driven, not Product Truth driven | partial: same concept, different owning route |
| Artwork print flag | `components.artwork.items[].printRequired` | `components.artwork.items[].printRequired`, but may be derived from `execution_type` when explicit boolean is absent | not consumed from Product Truth | blocked: derivation is not canonical confirmation |
| Artwork lamination flag | `components.artwork.items[].laminationRequired` | `components.artwork.items[].laminationRequired`, but may be derived from `execution_type` when explicit boolean is absent | not consumed from Product Truth | blocked: derivation is not canonical confirmation |
| Mounting scope | `components.mounting.mountingScope` | `components.mounting.mountingScope`, defaulting to `to_be_decided` when missing | payload/binding driven, not Product Truth driven | blocked: fallback/default is not promotable |
| Support type | `components.support.supportType` | `components.support.supportType`, but may be bridge-suggested from mounting or SVG evidence | payload/binding driven, not Product Truth driven | blocked: bridge evidence is explicitly non-canonical |
| Return depth family | contract docs mention `components.return.depth_mm`; draft uses `components.returnCant.depthMm`; backend bridge writes `product_truth.components.return_cant.instances[*].material_profile.width_mm` | path families diverge across snake/camel/object shape | ProductDefinition preview does not read backend Product Truth subtree | blocked: existing path drift proves writer risk |

## Six-Field Promotion Matrix

| Field | Current evidence source | Current states seen in code | Can promote now? | Blocking reason | Safe canonical entry |
| --- | --- | --- | --- | --- | --- |
| `svg.selected_layer_refs[]` | layer role setup / operator layer confirmation evidence | `suggested`, `blocked`, runtime `confirmed` only when explicit layer confirmation is complete | Conditionally yes | needs stable confirmed ref collection, not inferred role rows | confirmed ref entries keyed by stable `layer_id` |
| `finish.finish_target` | `finish_setup.finish_target` | `blocked`, runtime `confirmed` when explicit + `finish_setup.confirmed=true` | Conditionally yes | missing explicit confirmed field in many flows | single confirmed field at `components.finish.target` |
| `finish.print_required` | artwork finish rows | `blocked`, `unknown`, `hydrated`, `manual`; runtime ready only when every row is explicit/confirmed | No, except explicit confirmed row mode | current draft derives from `execution_type` | row entries at `components.artwork.items[].printRequired` |
| `finish.lamination_required` | artwork finish rows | `blocked`, `unknown`, `hydrated`, `manual`; runtime ready only when every row is explicit/confirmed | No, except explicit confirmed row mode | current draft derives from `execution_type` | row entries at `components.artwork.items[].laminationRequired` |
| `mounting.mounting_scope` | `finish_setup.mounting_scope` | `blocked`, defaulted `to_be_decided`, runtime `confirmed` only when explicit + `finish_setup.confirmed=true` | Conditionally yes | fallback/default path is not truth | single confirmed field at `components.mounting.mountingScope` |
| `support.support_type` | `finish_setup.support_type` | `blocked`, bridge-suggested, warning, runtime `confirmed` only when explicit + `finish_setup.confirmed=true` | Conditionally yes | current bridge from mounting/SVG is explicitly non-canonical | single confirmed field at `components.support.supportType` |

## Current Code Findings

Observed controlling surfaces:
- `backend/services/form_system_contract_mapping_adapter_service.py`
  - correctly fail-closes missing owner/source/path
  - already marks the six fields as blocked unless explicit confirmation exists
- `backend/services/form_system_runtime_capture_read_model_service.py`
  - exposes the six-field runtime capture slice as read-only and `ready_for_product_truth` only when state is `confirmed` with no blockers
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
  - intentionally builds a diagnostic draft, but still mixes fallback, suggested, hydrated, manual, and derived values into candidate truth shapes
  - derives artwork print/lamination booleans from `execution_type` when explicit booleans are absent
  - derives support hints from mounting/SVG evidence and marks them warning/suggested
- `frontend/src/lib/intakeV6/productTruth/productTruthReadiness.ts`
  - readiness remains preview-only and does not unlock downstream behavior
- `backend/services/product_definition_builder_service.py`
  - reads field bindings and payload directly into `canonical_values`
  - does not consume a confirmed Product Truth snapshot or promotion plan
- `backend/services/return_cant_product_truth_bridge.py`
  - shows an isolated bridge writing into `product_truth.components.return_cant.instances`
  - demonstrates that Product Truth subtree shape already differs from draft shape and older contract naming

## Minimum Safe Next Slice

Implement exactly one new read-only planner service.

Recommended slice:
- backend service: `product_truth_promotion_planner_service.py`
- pure function or service input: workspace payload + template code
- outputs:
  - `snapshot_version`
  - `snapshot_ready`
  - `eligible_entries[]`
  - `blocked_entries[]`
  - `path_conflicts[]`
  - `identity_conflicts[]`
  - `downstream_write_intent` all false

Planner entry contract:
- `entry_key`
- `owner_component`
- `canonical_path`
- `stable_identity` or `row_identity`
- `state`
- `value`
- `source_refs[]`
- `blockers[]`
- `ready_for_product_truth`

Planner rules:
1. consume the same fail-closed semantics already used by the runtime capture mapping
2. never derive product truth from fallback or bridge evidence
3. keep artwork fields row-scoped
4. emit conflicts when one conceptual field has multiple competing paths
5. emit conflicts when stable identity is missing
6. do not write `product_truth`
7. do not change ProductDefinition consumption yet

Focused tests for that slice:
1. complete explicit six-field payload -> only confirmed entries become eligible
2. derived artwork execution without explicit booleans -> row entries blocked
3. support inferred from mounting/SVG bridge -> blocked with conflict/warning, not eligible
4. missing stable layer ids -> selected SVG refs blocked
5. path-drift cases like return/cant -> planner emits `path_conflicts[]`

## What Must Not Be Implemented Yet

Do not implement yet:
- Product Truth persistence writer
- ProductDefinition consumption rewrite
- CTA unlock or UI promotion action
- commercial/quote/order/execution consumers
- any normalization that silently rewrites existing path families during write

## Strict Next Implementation Prompt

If the next task is approved, use this boundary:

`TASK — PRODUCT_TRUTH_PROMOTION_PLANNER_V1`

Implement a backend read-only Product Truth promotion planner for Intake V6 volumetric letters. Do not write Product Truth, do not change UI, do not touch Pricing/Quote/Order/Execution/ProductAggregate/TaskGraph/DB. Consume existing workspace payload plus current fail-closed runtime capture semantics. Return eligible vs blocked promotion entries for the six confirmed runtime-capture fields, preserve stable identity, preserve canonical Product Truth paths, detect path conflicts, and keep all downstream write-intent flags false. Add focused pytest coverage only for this planner.