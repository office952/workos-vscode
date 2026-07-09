# PRODUCT_TRUTH_WRITER_DRY_RUN_CONTRACT_V1

Status: PASS

Explicit statement:
- NO CODE IMPLEMENTATION
- no Product Truth writer implemented
- no dry-run endpoint implemented
- no POST endpoint implemented
- no UI button implemented
- no workspace payload mutation performed by this task
- no Product Truth storage mutation performed by this task
- no DB schema change
- no migration
- no seed

Scope:
- docs-only contract for a future Product Truth Writer Dry-Run
- define the read-only request/response boundary that sits between the Product Truth Promotion Planner and a later real writer
- define how a dry-run would calculate the proposed mutation set for `payload_json.product_truth.confirmed_snapshot_v1` without persisting anything

HEAD before:
- `4afe6cc`

Files read:
- `docs/worklog/realignment/2026-07-09_product_truth_storage_target_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_readiness_audit_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_ui_consumer_v1.md`
- `backend/services/product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/models/intake_v6_workspace.py`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`

Current read-only chain:
1. Product System provides upstream vocabulary and module structure.
2. Form System and Intake V6 runtime payload capture explicit runtime evidence.
3. Runtime Capture Read Model stays fail-closed and read-only.
4. Product Truth Promotion Planner classifies `eligible_entries` and `blocked_entries` from confirmed runtime evidence.
5. Planner endpoint exposes the planner contract as read-only.
6. Planner UI consumer surfaces the planner diagnostically without a mutation action.
7. Writer readiness audit defines the writer boundary but does not implement a writer.
8. Storage target contract reserves `payload_json.product_truth.confirmed_snapshot_v1` as the future canonical sink.
9. This dry-run contract defines the last read-only verification step before a later writer implementation.

Dry-run purpose:
- future dry-run consumes planner output or reproduces the exact planner basis server-side
- future dry-run calculates what the writer would write into `payload_json.product_truth.confirmed_snapshot_v1`
- future dry-run returns a proposed mutation set only
- future dry-run persists nothing
- future dry-run does not modify `payload_json`
- future dry-run does not modify planner state or planner semantics
- future dry-run does not modify ProductDefinition, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or ExecutionPlan state
- future dry-run exists only as a read-only verification boundary between planner verdict and real writer

Why a dry-run is needed:
1. planner eligibility alone does not prove the future writer request shape, target path, provenance bundle, or idempotency basis
2. the current runtime bridge `payload.product_truth.components.return_cant` proves that `payload.product_truth` already contains non-canonical helper content
3. a dry-run allows exact mutation planning against `confirmed_snapshot_v1` without risking accidental writes into runtime evidence zones
4. a dry-run creates a stable contract for later backend tests before any write path or UI CTA exists

Dry-run input contract:

Purpose of input:
- identify the workspace and planner basis
- constrain target template context
- optionally narrow the requested mutation set to a subset of `eligible_entries`
- force explicit dry-run intent so the same contract cannot be confused with a real writer call

Minimum request fields:
- `workspace_id: string`
- `expected_workspace_code?: string`
- `expected_root_template_code: string`
- `expected_product_binding_template_code: string`
- `planner_version: string`
- `planner_hash?: string`
- `payload_hash_basis?: string`
- `actor: { actor_id?: string, actor_email?: string, actor_role?: string, actor_label?: string }`
- `requested_entry_keys?: string[]`
- `dry_run_only: true`

Input rules:
1. `workspace_id` is mandatory
2. `expected_root_template_code` is mandatory
3. `expected_product_binding_template_code` is mandatory
4. `planner_version` is mandatory and must match the planner contract known by the server
5. at least one planner basis field must be present:
   - `planner_hash`, or
   - `payload_hash_basis`
6. `dry_run_only` must be exactly `true`
7. `requested_entry_keys` may be omitted to mean all current `eligible_entries`
8. if `requested_entry_keys` is provided, every key must map to a current planner entry under the exact same planner basis
9. `actor` is required as provenance placeholder even though no write occurs

Input semantics:
- `expected_workspace_code`:
  optional extra guard against stale or wrong workspace selection
- `planner_hash`:
  preferred deterministic hash of the planner basis and normalized planner output if a future implementation exposes it
- `payload_hash_basis`:
  acceptable fallback basis when planner hash is not separately exposed
- `requested_entry_keys`:
  optional strict subset selector for dry-run planning only; it does not allow blocked entries

Recommended request shape:

```json
{
  "workspace_id": "668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c",
  "expected_workspace_code": "IV6-9C831ADB",
  "expected_root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "expected_product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "planner_version": "v1",
  "payload_hash_basis": "sha256:...",
  "actor": {
    "actor_id": "user-123",
    "actor_email": "operator@example.com",
    "actor_role": "operator",
    "actor_label": "Operator Review"
  },
  "requested_entry_keys": [
    "finish.finish_target",
    "finish.print_required:layer_key:logo-left"
  ],
  "dry_run_only": true
}
```

Dry-run output contract:

Top-level response shape:
- `read_only: true`
- `dry_run: true`
- `workspace_id: string`
- `workspace_record_id: string`
- `workspace_code: string | null`
- `root_template_code: string`
- `product_binding_template_code: string`
- `planner_version: string`
- `target_path: "payload_json.product_truth.confirmed_snapshot_v1"`
- `proposed_mutations: []`
- `refused_entries: []`
- `blockers: []`
- `idempotency_basis: object`
- `promotion_hash: string | null`
- `downstream_write_intent: object`
- `notes: string[]`

Output rules:
1. `read_only` and `dry_run` must both be `true`
2. `target_path` must always be exactly `payload_json.product_truth.confirmed_snapshot_v1`
3. `downstream_write_intent` must keep every flag false
4. `promotion_hash` may be null only when the dry-run is fully refused before mutation planning
5. `proposed_mutations` contains only `action = would_write`
6. `refused_entries` contains only `action = refused`
7. `blockers` is the contract-level summary, not a replacement for per-entry refusal details

Recommended response shape:

```text
read_only = true
dry_run = true
workspace metadata
planner_version
target_path = payload_json.product_truth.confirmed_snapshot_v1
proposed_mutations[]
refused_entries[]
blockers[]
idempotency_basis
promotion_hash
downstream_write_intent
notes[]
```

Proposed mutations schema:

Each `proposed_mutations[]` item must contain:
- `entry_key`
- `field_key`
- `source_path`
- `target_path`
- `value`
- `value_state`
- `source_state`
- `source_type`
- `identity_key`
- `planner_entry_hash`
- `promotion_hash`
- `provenance`
- `conflict_status`
- `action = "would_write"`

Field meaning:
- `entry_key`:
  planner-stable entry identifier such as `finish.finish_target` or `finish.print_required:layer_key:logo-left`
- `field_key`:
  field family from planner contract
- `source_path`:
  runtime payload source path that justified the eligible entry
- `target_path`:
  exact leaf destination inside `payload_json.product_truth.confirmed_snapshot_v1.entries.*`
- `value`:
  normalized value that the future writer would persist
- `value_state`:
  expected to be `confirmed`
- `source_state`:
  planner-side entry state that justified eligibility, expected to be `confirmed`
- `source_type`:
  one of `scalar`, `selected_layer_ref`, `artwork_row_boolean`, or future documented planner source type
- `identity_key`:
  row identity such as `layer_id:face-1` or `layer_key:logo-left`; null only for pure scalar entries
- `planner_entry_hash`:
  deterministic hash for the normalized planner entry payload
- `promotion_hash`:
  deterministic batch-level hash computed from the idempotency basis
- `provenance`:
  structured proof bundle for source, template basis, actor placeholder, and planner basis
- `conflict_status`:
  expected values:
  - `no_conflict`
  - `would_overwrite_same_value`
  - `would_conflict_existing_snapshot`
  - `target_path_ambiguous`
- `action`:
  always `would_write` for dry-run proposals

Recommended provenance object:
- `workspace_id`
- `workspace_code`
- `root_template_code`
- `product_binding_template_code`
- `planner_version`
- `planner_hash`
- `payload_hash_basis`
- `source_path`
- `source_state`
- `source_type`
- `identity_key`
- `actor`
- `writer_contract_version`
- `target_contract_version`
- `planner_read_only = true`
- `promotion_reason = eligible_entry_would_be_promoted`

Recommended target path pattern:
- scalar entry:
  `payload_json.product_truth.confirmed_snapshot_v1.entries.<field_key>`
- row identity entry:
  `payload_json.product_truth.confirmed_snapshot_v1.entries.<field_key>.<identity_key>`

Refused entries schema:

Each `refused_entries[]` item must contain:
- `entry_key`
- `field_key`
- `source_path`
- `target_path`
- `reason`
- `blockers`
- `action = "refused"`
- `refusal_is_blocking = true`

Recommended optional refusal fields:
- `identity_key`
- `source_state`
- `source_type`
- `planner_entry_hash`
- `planner_basis_mismatch`
- `payload_hash_changed`
- `template_mismatch`
- `requested_but_not_eligible`

Refusal semantics:
- `target_path` should be included when it can be deterministically inferred
- `reason` is the human-readable explanation
- `blockers[]` is the machine-readable code list
- `refusal_is_blocking` is always `true` because refused dry-run entries must not be silently downgraded to warnings

Fail-closed behavior:

General rule:
- dry-run is read-only, but still fail-closed on basis mismatches and forbidden write intent

Entry-level rule:
- `blocked_entries` never produce `proposed_mutations`
- blocked, missing, suggested, hydrated, fallback, partial, derived-evidence-only, or ambiguous identity entries must appear under `refused_entries`

Mixed eligible + blocked policy:
- dry-run may still report `proposed_mutations` for the eligible subset
- dry-run must also report every refused entry explicitly
- dry-run must include a contract-level note that a later real writer must refuse the full request atomically when blocked entries are included

Why this split is correct:
1. dry-run is diagnostic and should expose the exact eligible mutation set
2. real writer remains stricter and atomic
3. this preserves visibility without weakening the later writer safety bar

Basis mismatch refusal rules:
1. stale `planner_hash` refuses dry-run
2. changed `payload_hash_basis` refuses dry-run
3. `expected_root_template_code` mismatch refuses dry-run
4. `expected_product_binding_template_code` mismatch refuses dry-run
5. `expected_workspace_code` mismatch, when supplied, refuses dry-run
6. any `downstream_write_intent` flag not false refuses dry-run
7. missing workspace returns controlled `404`

Special rule for return/cant runtime bridge:
- dry-run must never use `payload.product_truth.components.return_cant` as the generic sink
- dry-run must never propose a write into `payload.product_truth.components.*`
- if a future planner later makes return/cant entries eligible, dry-run must still route them into `payload_json.product_truth.confirmed_snapshot_v1`

No-mutation proof:

Future dry-run must prove all of the following:
1. workspace payload hash is unchanged before and after dry-run execution
2. planner output is unchanged before and after dry-run execution
3. no `product_truth.confirmed_snapshot_v1` mutation is persisted
4. no mutation occurs under `payload.product_truth.components.return_cant`
5. no ProductDefinition mutation occurs
6. no Pricing mutation occurs
7. no Quote mutation occurs
8. no Order mutation occurs
9. no Execution mutation occurs
10. no ProductAggregate, TaskGraph, or ExecutionPlan mutation occurs
11. no DB write occurs; dry-run remains pure read-only

Recommended proof fields in response notes:
- `payload_hash_before`
- `payload_hash_after`
- `payload_hash_unchanged = true`
- `planner_hash_before`
- `planner_hash_after`
- `planner_hash_unchanged = true`
- `db_write_performed = false`

Idempotency basis:

Dry-run should expose the same basis the real writer would later use:
- `workspace_id`
- `workspace_code`
- `root_template_code`
- `product_binding_template_code`
- `planner_version`
- `planner_hash`
- `payload_hash_basis`
- sorted normalized proposed entries:
  - `entry_key`
  - `field_key`
  - `target_path`
  - `identity_key`
  - normalized `value`

Deterministic hash rule:
- `promotion_hash = sha256(canonical_json(idempotency_basis))`

Repeat dry-run rule:
- repeated dry-run on the same workspace and same unchanged basis must return the same `promotion_hash`
- repeated dry-run on the same basis must return the same normalized `proposed_mutations` and `refused_entries` ordering

Conflict status guidance:
- `no_conflict`:
  no existing canonical entry would be contradicted
- `would_overwrite_same_value`:
  existing canonical target already holds identical normalized confirmed value
- `would_conflict_existing_snapshot`:
  existing canonical target already holds a different confirmed value on the same target path
- `target_path_ambiguous`:
  dry-run cannot establish an exact canonical target path safely

Future tests:
1. eligible entries produce `would_write` mutations
2. blocked entries produce `refused` entries
3. zero eligible and many blocked yields empty `proposed_mutations`
4. stale planner hash is refused
5. changed payload hash basis is refused
6. template mismatch is refused
7. missing workspace returns controlled `404`
8. repeated dry-run is deterministic
9. target path is exactly `payload_json.product_truth.confirmed_snapshot_v1`
10. `payload.product_truth.components.return_cant` is never used as generic sink
11. all `downstream_write_intent` flags remain false
12. no payload mutation occurs
13. planner output is unchanged
14. no ProductDefinition mutation occurs
15. no Pricing, Quote, Order, or Execution mutation occurs
16. no DB write occurs
17. mixed eligible plus blocked request yields visible proposed eligible mutations plus refused blocked entries in dry-run
18. later real writer acceptance tests must still enforce atomic refusal for the same mixed request

Recommended future implementation sequence:
1. keep this dry-run contract docs-only until owner GO
2. add backend dry-run computation server-side with no persistence
3. add targeted tests proving no payload mutation and deterministic output
4. only after dry-run proof is stable, implement the real writer with stricter atomic refusal semantics
5. only after backend writer proof exists, consider any frontend CTA

Roadmap awareness checkpoint:
- roadmap alignment score: `10/10`
- current spine position:
  `Product System -> Form System -> Intake V6 runtime payload -> Runtime Capture Read Model -> Product Truth Promotion Planner -> Planner Endpoint -> Planner UI Consumer -> Product Truth Writer Readiness Audit -> Product Truth Storage Target Contract -> Product Truth Writer Dry-Run Contract`
- direction alignment: `97/100%`
- dead pieces check:
  - no dead runtime code introduced
  - no dead endpoint introduced
  - no dead UI surface introduced
  - no dead schema introduced
  - no dead persistence branch introduced
- forbidden scope confirmation:
  - no writer
  - no endpoint
  - no UI CTA
  - no payload mutation
  - no DB migration
  - no seed live
  - no Pricing / Quote / Order / Execution
  - no ProductDefinition consumer
  - no ProductAggregate / TaskGraph / ExecutionPlan

Why this step matches the roadmap:
1. it stays strictly between planner visibility and real writer implementation
2. it clarifies exactly what a later backend writer would calculate before any mutation exists
3. it keeps `confirmed_snapshot_v1` as the only canonical target and avoids the current runtime bridge subtree
4. it improves implementation readiness without weakening planner semantics or touching downstream systems

Forbidden scope confirmation:
- no Product Truth writer implemented
- no dry-run endpoint added
- no POST endpoint added
- no UI button added
- no Product Truth mutation
- no workspace payload mutation
- no Product Truth storage real mutation
- no DB migration
- no seed live
- no Pricing
- no Quote/Order
- no Execution
- no ProductDefinition consumer
- no ProductAggregate/TaskGraph

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_DRY_RUN_RESPONSE_FIXTURE_V1`
- Goal: define docs-only example success and refusal JSON fixtures for the dry-run contract using current planner field families and exact `confirmed_snapshot_v1` target paths
- Boundary: no backend implementation, no endpoint, no UI CTA, no payload mutation, no DB migration, no ProductDefinition consumer changes