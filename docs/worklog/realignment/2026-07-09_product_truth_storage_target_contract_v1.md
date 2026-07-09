# PRODUCT_TRUTH_STORAGE_TARGET_CONTRACT_V1

Status: PASS

Explicit statement:
- NO CODE IMPLEMENTATION
- no Product Truth writer implemented
- no POST endpoint implemented
- no UI button implemented
- no runtime payload mutation performed by this task
- no DB schema change
- no migration
- no seed

Scope:
- docs-only contract for the future Product Truth storage target
- define where a future writer would be allowed to persist confirmed Product Truth
- define what is canonical Product Truth target data versus runtime evidence, planner output, ProductDefinition inputs, and pricing/downstream data

HEAD before:
- `57ac72b`

Files read:
- `docs/worklog/realignment/2026-07-09_product_truth_writer_readiness_audit_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_ui_consumer_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_endpoint_metadata_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_endpoint_v1.md`
- `backend/services/product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- `backend/models/intake_v6_workspace.py`
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/tests/test_return_cant_product_truth_bridge.py`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_PHASE_3_PRODUCT_TRUTH_CANONICAL_PAYLOAD_DESIGN.md`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`

Current read-only chain:
1. Runtime Capture Read Model is fail-closed and read-only.
2. Product Truth Promotion Planner re-checks explicit confirmation and stable identity.
3. Planner endpoint exposes only read-only diagnostics.
4. Planner UI consumer surfaces the planner in Review without a write flow.
5. Writer readiness audit established eligible-only, blocked-refusal, provenance, and idempotency boundaries.

Storage candidates audit:

Current physical persistence container:
- actual persisted workspace storage today is `intake_v6_workspaces.payload_json`
- current ORM container is `backend/models/intake_v6_workspace.py`
- there is no dedicated DB table or dedicated DB column for Product Truth today

Current payload contract candidate:
- `backend/schemas/intake_v4.py` already includes `product_truth: dict[str, Any] | None = None` in the workspace payload shape used by V6-compatible flows
- this means a payload-root Product Truth zone is already structurally allowed without DB migration

Current runtime Product Truth usage already present:
- `backend/services/return_cant_product_truth_bridge.py` already writes a subtree under `payload.product_truth.components.return_cant`
- `backend/services/intake_v6_workspace_service.py` applies that bridge during SVG and finish-setup save flows
- tests prove this bridge mutates only `payload.product_truth` subtree and is idempotent for its own bridge logic

Current risk revealed by that usage:
- `payload.product_truth` already exists as a runtime bridge landing zone for `return_cant`
- that bridge carries blocked/evidence-oriented values and is not a generic confirmed-truth writer contract
- therefore a future generic Product Truth writer must not dump canonical confirmed truth into `payload.product_truth` root without an internal sub-boundary
- otherwise confirmed Product Truth would be mixed with bridge-derived runtime evidence, blocked placeholders, and component-specific helper data

Current in-memory Product Truth draft candidate:
- frontend has `ProductTruthDraft` and `ProductTruthField` types in `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- frontend builder is explicit preview-only and non-persistent in `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- docs mark this shape as `RUNTIME_PAYLOAD_NOT_IMPLEMENTED` and `BACKEND_SCHEMA_NOT_IMPLEMENTED`
- this is a strong schema inspiration for provenance and field-level state, but it is not real backend storage today

Audit/provenance status today:
- no generic backend Product Truth provenance schema exists yet
- existing return/cant bridge includes partial provenance-like fields such as `instance_key`, `source_kind`, `source_ref`, blockers, and confirmation state
- frontend draft contains a stronger provenance pattern through `sourceRefs`, field states, blockers, warnings, and audit entries

Risk of accidental mixing if no target contract is defined:
1. runtime capture evidence could be mistaken for confirmed Product Truth
2. bridge-generated `return_cant` data could be mistaken for generic Product Truth writer output
3. planner diagnostics could be stored as truth instead of only driving eligibility
4. ProductDefinition-facing values could be mixed into the same branch as confirmation truth
5. Pricing or commercial preview values could leak into Product Truth storage

Chosen / proposed Product Truth target contract:

Physical persistence location:
- stay inside `intake_v6_workspaces.payload_json`
- reason: already real persisted storage, no DB migration required, no new table required, matches current workspace-centric flow

Canonical target zone name:
- `payload_json.product_truth.confirmed_snapshot_v1`

Why this is the correct target:
1. it uses the already allowed `product_truth` payload branch without requiring schema migration
2. it avoids using bare `payload.product_truth` root as an unqualified sink
3. it stays clearly separate from the existing runtime bridge subtree at `payload.product_truth.components.return_cant`
4. the suffix `confirmed_snapshot_v1` makes the semantics explicit: canonical, confirmed, versioned, snapshot-style, writer-owned
5. it can be read later by ProductDefinition consumers without depending on planner internals

Reserved sibling zones under `payload_json.product_truth`:
- `confirmed_snapshot_v1`:
  canonical confirmed Product Truth target for future generic writer
- `runtime_bridges_v1`:
  future explicit namespace for bridge-style runtime helper projections if they are ever migrated out of the current legacy component subtree
- `components`:
  current legacy/runtime bridge subtree already used by `return_cant`; must not be treated as generic canonical writer sink

What enters `confirmed_snapshot_v1`:
1. only promoted eligible entries
2. confirmed values only
3. target metadata and provenance
4. identity-preserving row-level records where required
5. immutable audit trail entries for promotions
6. deterministic writer basis information such as planner version and payload hash basis

What does not enter `confirmed_snapshot_v1`:
1. planner response blobs
2. `blocked_entries`
3. `suggested`, `hydrated`, `fallback`, `partial`, `derived_evidence_only`, or generic runtime evidence
4. ProductDefinition outputs
5. Pricing inputs or preview values
6. Quote, Order, Execution, ProductAggregate, TaskGraph, or ExecutionPlan data
7. current return/cant runtime bridge subtree
8. frontend-only `ProductTruthDraft` preview object as a whole

Required internal shape for `confirmed_snapshot_v1`:

```text
product_truth
  confirmed_snapshot_v1
    metadata
    planner_basis
    entries
      <entry_key>
    audit_trail
```

Meaning of subzones:
- `metadata`:
  snapshot identity and template/workspace context
- `planner_basis`:
  payload hash and planner/idempotency basis used for the promotion decision
- `entries`:
  canonical promoted entries keyed by stable `entry_key`
- `audit_trail`:
  append-only promotion audit records or last-write records, depending on final writer design

Separation rules:

Separation from suggestions / hydrated / fallback:
- only `eligible_entries` may be promoted
- states other than explicit confirmed remain outside `confirmed_snapshot_v1`
- if evidence needs to remain visible, it stays in runtime payload branches or bridge branches, not in confirmed snapshot

Separation from runtime evidence:
- runtime evidence remains in branches like `svg`, `layer_role_setup`, `finish_setup`, `quote_geometry`, and any runtime bridge subtree
- `confirmed_snapshot_v1` contains confirmed canonical truth, not raw evidence
- target entries may reference evidence through provenance, but must not duplicate the entire evidence payload

Separation from ProductDefinition:
- ProductDefinition later consumes Product Truth
- ProductDefinition outputs must not be stored back into `confirmed_snapshot_v1`
- any future ProductDefinition cache or preview must live outside this target zone

Separation from planner:
- planner remains a read-only classifier and contract boundary
- planner output is not persisted as canonical Product Truth
- only the promoted subset and its basis are stored

Mutation granularity:

Write unit:
- deterministic batch of explicitly requested `eligible_entries`
- not a best-effort partial write

Why batch instead of ad hoc single-field mutation only:
1. planner eligibility is computed against a single payload basis
2. allowing partial success in mixed eligible/blocked sets would create hard-to-audit partial truth snapshots
3. atomic batch behavior is simpler to verify and safer against silent drift

Atomicity rule:
- if any requested entry is blocked, missing, stale, ambiguous, duplicate-conflicting, or mismatched against planner basis, the whole write must be refused

Allowed subset behavior:
- a caller may request a strict subset of current `eligible_entries`
- but every requested entry must still be eligible against the same planner basis and payload hash

Mixed eligible + blocked behavior:
- refuse whole batch
- no partial promotion

Duplicate entry handling:
- duplicate `entry_key` with identical normalized content in the same request may be collapsed before hashing
- duplicate `entry_key` with conflicting value, state, target path, or identity key must be refused

Repeat request / idempotency behavior:
- same workspace
- same target zone version
- same planner version
- same template basis
- same payload hash before write
- same normalized promoted entry set
- same target values
  => exact same `promotion_hash`, treated as idempotent no-op

Proposed idempotency basis:
- `workspace_id`
- `root_template_code`
- `product_binding_template_code`
- `planner_version`
- `payload_hash_before`
- sorted normalized promoted entries:
  - `entry_key`
  - `field_key`
  - `target_path`
  - `identity_key`
  - normalized `value`

Proposed deterministic key:
- `promotion_hash = sha256(canonical_json(idempotency_basis))`

Why actor should not be part of `promotion_hash`:
- idempotency is about state-equivalent write replay, not about who retried it
- actor must still be captured in provenance, but should not force duplicate canonical snapshots for the same state

Provenance schema:

Each promoted entry in `confirmed_snapshot_v1.entries.<entry_key>` must contain at minimum:
- `workspace_id`
- `workspace_code`
- `root_template_code`
- `product_binding_template_code`
- `planner_version`
- `source_path`
- `target_path`
- `field_key`
- `value`
- `value_state`
- `source_state`
- `source_type`
- `identity_key`
- `promoted_by`
- `promoted_at`
- `promotion_hash`
- `planner_blocker_status = eligible_only`

Recommended additional provenance fields:
- `entry_key`
- `payload_hash_before`
- `payload_hash_after`
- `writer_contract_version`
- `promotion_reason = eligible_entry_promoted`
- `planner_read_only = true`

Field interpretation:
- `value_state`:
  canonical state of stored Product Truth value, expected to be `confirmed`
- `source_state`:
  source-side classification observed at planner time, expected to match eligible source semantics
- `source_type`:
  scalar, selected_layer_ref, artwork_row_boolean, or future documented type
- `identity_key`:
  required for row-level truth such as `layer_id:*` or `layer_key:*`; null only for scalar entries

Refusal rules:

Future writer must refuse when:
1. any requested entry is in `blocked_entries`
2. any requested entry has missing value
3. any requested entry is `suggested`, `hydrated`, `fallback`, `partial`, `missing`, or `blocked`
4. any row identity is ambiguous or missing where required
5. `payload_hash_before` no longer matches the planner basis
6. any downstream write intent flag is not false
7. workspace is missing
8. `root_template_code` or `product_binding_template_code` mismatches planner basis unexpectedly
9. request attempts to write ProductDefinition, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or ExecutionPlan data
10. request tries to write into `payload.product_truth.components` or any non-canonical target zone
11. request includes planner metadata blob as if it were truth data

Special refusal rule for current return/cant bridge:
- future generic writer must not treat `payload.product_truth.components.return_cant` as already confirmed canonical truth
- if return/cant truth is promoted later, it must still enter `confirmed_snapshot_v1.entries.*` through eligible-entry promotion with provenance, not by copying bridge subtree blindly

Read-after-write expectation:

After a future valid writer call, the following must be true:
1. `payload.product_truth.confirmed_snapshot_v1` contains only promoted eligible entries
2. promoted entries preserve `entry_key`, `field_key`, `target_path`, `value`, and provenance
3. planner remains read-only and unchanged as a service/endpoint contract
4. if payload is the physical target, workspace payload mutation is limited strictly to `product_truth.confirmed_snapshot_v1`
5. no Pricing mutation
6. no Quote mutation
7. no Order mutation
8. no Execution mutation
9. no ProductDefinition mutation
10. audit/provenance is visible in the target itself
11. replaying the same request yields idempotent no-op behavior with the same `promotion_hash`

Future writer test matrix:
1. eligible-only promotion writes expected entries into `confirmed_snapshot_v1`
2. blocked entry request is refused
3. mixed eligible + blocked batch is refused atomically
4. missing workspace returns controlled `404`
5. stale planner hash / payload hash mismatch is refused
6. duplicate request is idempotent
7. conflicting duplicate entry in same request is refused
8. row identity is preserved for `layer_id` and `layer_key` cases
9. source path and source state are preserved
10. planner data itself is not mutated
11. ProductDefinition is not mutated
12. Pricing is not mutated
13. Quote is not mutated
14. Order is not mutated
15. Execution is not mutated
16. no DB migration is required for the payload-target implementation path unless owner GO changes the storage strategy later

Why this contract is safe relative to current code:
1. it reuses the already persisted workspace payload container
2. it avoids DB schema changes
3. it does not overload the current runtime bridge subtree as canonical writer target
4. it aligns with existing Product Truth documentation that keeps Product Truth separate from ProductDefinition, Pricing, and downstream systems
5. it preserves room for later consumer migration without needing planner or UI semantics changes

Forbidden scope confirmation:
- no writer implemented
- no endpoint added
- no UI button added
- no Product Truth mutation
- no workspace payload mutation
- no DB migration
- no seed live
- no Pricing
- no Quote/Order
- no Execution
- no ProductDefinition consumer
- no ProductAggregate/TaskGraph

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_DRY_RUN_CONTRACT_V1`
- Goal: define docs-only the future backend dry-run writer request/response contract that consumes planner basis and returns a proposed `confirmed_snapshot_v1` mutation set without persisting it
- Boundary: no writer implementation, no endpoint, no UI CTA, no DB migration, no ProductDefinition consumer changes