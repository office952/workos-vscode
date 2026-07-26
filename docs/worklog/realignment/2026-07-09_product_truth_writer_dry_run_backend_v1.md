# PRODUCT_TRUTH_WRITER_DRY_RUN_BACKEND_V1

Status: PASS

Scope:
- implement first backend Product Truth writer dry-run as read-only backend surface
- consume existing planner output semantics without modifying planner behavior
- compute `proposed_mutations` for eligible planner entries
- compute `refused_entries` for blocked planner entries
- return deterministic hashes plus no-mutation proof
- add focused backend tests for read-only dry-run behavior

HEAD before:
- `9771a74`

Files touched:
- `backend/services/product_truth_writer_dry_run_service.py`
- `backend/schemas/intake_v6.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/tests/test_product_truth_writer_dry_run.py`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_dry_run_backend_v1.md`

Endpoint added:
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/dry-run`
- semantic mode: read-only
- persistence behavior: none
- writer behavior: none

Service / schema added:
- new service:
  - `backend/services/product_truth_writer_dry_run_service.py`
- responsibilities:
  - deterministic payload hash
  - deterministic planner hash
  - deterministic planner-entry hash
  - target-path mapping into `payload_json.product_truth.confirmed_snapshot_v1`
  - `proposed_mutations` builder
  - `refused_entries` builder
  - `idempotency_basis` + `promotion_hash`
  - no-mutation proof bundle
- schema addition:
  - `IntakeV6ProductTruthWriterDryRunRequest`
  - required guard fields:
    - `dry_run_only: true`
    - `expected_root_template_code`
    - `expected_product_binding_template_code`
    - `planner_version`
  - optional basis / guard fields:
    - `expected_workspace_code`
    - `planner_hash`
    - `payload_hash_basis`
    - `actor`
    - `requested_entry_keys`

Implementation notes:
1. workspace orchestration stays in `intake_v6_workspace_service.py`
2. planner remains read-only classifier only
3. dry-run computes response from payload + planner output only
4. `_persist_payload(...)` is not called by this path
5. `payload.product_truth.components.return_cant` is never used as the generic sink

Response shape summary:
- `read_only = true`
- `dry_run = true`
- workspace metadata
- `planner_version`
- `target_path = payload_json.product_truth.confirmed_snapshot_v1`
- `proposed_mutations[]`
- `refused_entries[]`
- `blockers[]`
- `idempotency_basis`
- `promotion_hash`
- `downstream_write_intent`
- `no_mutation_proof`
- `notes[]`
- `writer_real_atomic_policy = fail_closed_if_request_contains_blocked`

Proposed mutations behavior:
- only planner `eligible_entries` become `proposed_mutations`
- every proposed mutation returns:
  - `action = would_write`
  - `entry_key`
  - `field_key`
  - `source_path`
  - `target_path`
  - `value`
  - `value_state = confirmed`
  - `source_state`
  - `source_type`
  - `identity_key` when present
  - `planner_entry_hash`
  - `promotion_hash`
  - `provenance`
  - `conflict_status`
- current mapped families:
  - `svg.selected_layer_refs[]`
  - `finish.finish_target`
  - `finish.print_required`
  - `finish.lamination_required`
  - `mounting.mounting_scope`
  - `support.support_type`

Refused entries behavior:
- planner `blocked_entries` never become `proposed_mutations`
- blocked entries are emitted as `refused_entries`
- every refusal returns:
  - `action = refused`
  - `refusal_is_blocking = true`
  - `entry_key`
  - `field_key`
  - `source_path`
  - deterministic `target_path` when inferable
  - `reason`
  - `blockers[]`
- requested unknown entry keys are refused explicitly

Fail-closed behavior:
- missing workspace -> controlled `404`
- `dry_run_only` must be true
- `planner read_only` must remain true
- all downstream write-intent flags must remain false
- expected workspace-code mismatch -> `422`
- expected root-template mismatch -> `422`
- expected product-binding-template mismatch -> `422`
- planner-version mismatch -> `422`
- payload-hash-basis mismatch -> `422`
- planner-hash mismatch -> `422`
- requested blocked entry keys stay refused and never become proposed

No-mutation proof:
- response includes `no_mutation_proof`
- proof currently exposes:
  - payload hash before / after
  - planner hash before / after
  - payload hash unchanged flag
  - planner hash unchanged flag
  - product-truth target hash before / after
  - return-cant bridge hash before / after
  - `product_truth_target_mutated = false`
  - `return_cant_bridge_mutated = false`
  - `downstream_mutated = false`
  - `db_write_performed = false`

Read-only proof:
1. endpoint returns only computed response data
2. workspace payload before/after remains byte-stable in tests
3. planner regressions remain green after wiring
4. dry-run never writes into `confirmed_snapshot_v1`
5. dry-run never touches `payload.product_truth.components.return_cant`

Test summary:
- new focused dry-run tests:
  - success eligible entries -> proposed mutations
  - zero eligible / many blocked -> refusals only
  - blocked requested entries never produce proposals
  - mixed visibility shows both lists
  - missing workspace `404`
  - template mismatch controlled failure
  - repeated dry-run deterministic
- regression expectation:
  - planner service and planner endpoint remain green

Forbidden scope confirmation:
- no Product Truth writer implemented
- no Product Truth mutation performed
- no workspace payload mutation performed
- no DB migration
- no seed live
- no UI button
- no frontend consumer
- no Pricing
- no Quote/Order
- no Execution
- no ProductDefinition consumer
- no ProductAggregate/TaskGraph

What remains later:
1. real Product Truth writer endpoint
2. actual persistence into `payload_json.product_truth.confirmed_snapshot_v1`
3. stronger conflict semantics against persisted snapshot history
4. optional response schema formalization if the contract grows
5. frontend trigger / CTA only after backend writer proof
6. ProductDefinition consumer later, only after owner GO
7. downstream system integration later

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_BACKEND_V1`
- Goal: implement the real Product Truth writer backend behind explicit owner GO, reusing the dry-run basis, enforcing atomic refusal, and mutating only `payload_json.product_truth.confirmed_snapshot_v1`
- Boundary: no frontend CTA unless explicitly requested, no Pricing/Quote/Order/Execution changes, no ProductDefinition consumer wiring unless separately approved