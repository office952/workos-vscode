# PRODUCT_TRUTH_WRITER_DRY_RUN_HTTP_VERIFICATION_V1

Status: PASS

Scope:
- runtime verification only for the Product Truth writer dry-run HTTP endpoint
- verify planner HTTP contract on a real workspace
- verify dry-run HTTP contract on a real workspace
- prove no mutation of workspace payload, `confirmed_snapshot_v1`, and `return_cant` bridge
- verify controlled failure paths
- no implementation change performed

HEAD before:
- `6bf8a7f`

Endpoint verified:
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/dry-run`

Workspace verified:
- `workspace_id = 668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c`
- `workspace_code = IV6-9C831ADB`

Backend runtime:
- backend was already responding locally on `http://127.0.0.1:8000`
- verification used the live local backend
- no migration run
- no seed run

Request body used:

```json
{
  "dry_run_only": true,
  "expected_workspace_code": "IV6-9C831ADB",
  "expected_root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "expected_product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "planner_version": "v1"
}
```

Planner response summary:
- HTTP `200`
- `read_only = true`
- `workspace_code = IV6-9C831ADB`
- `root_template_code = TPL-VOLUMETRIC-LETTERS_v2`
- `product_binding_template_code = TPL-VOLUMETRIC-LETTERS_v2`
- `planner_version = v1`
- `eligible_entries = 0`
- `blocked_entries = 8`
- all `downstream_write_intent` flags were `false`
- deterministic planner hash before:
  - `sha256:49c7058445ebb2ccf664813217d9929c7c5e9a969ee0f2f72a4579c4c899ae88`

Dry-run response summary:
- HTTP `200`
- `read_only = true`
- `dry_run = true`
- `target_path = payload_json.product_truth.confirmed_snapshot_v1`
- `proposed_mutations = 0`
- `refused_entries = 8`
- `writer_real_atomic_policy = fail_closed_if_request_contains_blocked`
- all `downstream_write_intent` flags were `false`
- `no_mutation_proof` present
- sample refused entry keys observed:
  - `finish.finish_target`
  - `finish.lamination_required:layer_key:logo-dreapta`
  - `finish.lamination_required:layer_key:logo-stanga`
  - `finish.print_required:layer_key:logo-dreapta`
  - `finish.print_required:layer_key:logo-stanga`

No-mutation proof:
- `payload_hash_before = sha256:35dba65902e8e215298ffa2b377d89796dca42c16ee0f9237611afed3f7d8390`
- `payload_hash_after = sha256:35dba65902e8e215298ffa2b377d89796dca42c16ee0f9237611afed3f7d8390`
- `payload_hash_before == payload_hash_after = true`
- `confirmed_snapshot_v1 present before = false`
- `confirmed_snapshot_v1 present after = false`
- `confirmed_snapshot_v1 hash before = sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`
- `confirmed_snapshot_v1 hash after = sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`
- `confirmed_snapshot_v1 unchanged = true`
- `return_cant present before = false`
- `return_cant present after = false`
- `return_cant hash before = sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`
- `return_cant hash after = sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`
- `return_cant unchanged = true`
- `planner_hash_before = sha256:49c7058445ebb2ccf664813217d9929c7c5e9a969ee0f2f72a4579c4c899ae88`
- `planner_hash_after = sha256:49c7058445ebb2ccf664813217d9929c7c5e9a969ee0f2f72a4579c4c899ae88`
- `planner unchanged = true`
- dry-run `no_mutation_proof` fields returned:
  - `payload_hash_unchanged = true`
  - `planner_hash_unchanged = true`
  - `product_truth_target_mutated = false`
  - `return_cant_bridge_mutated = false`
  - `downstream_mutated = false`
  - `db_write_performed = false`

Failure / control checks:

1. Missing workspace
- request:
  - `POST /api/v1/intake-v6/workspaces/00000000-0000-0000-0000-000000000000/product-truth-writer/dry-run`
- result:
  - HTTP `404`
  - controlled body:
    - `detail.error = workspace_not_found`

2. Template mismatch
- request:
  - same workspace
  - `expected_root_template_code = TPL-WRONG-TEMPLATE`
- result:
  - HTTP `422`
  - controlled body:
    - `detail.error = root_template_code_mismatch`

3. `dry_run_only = false`
- request:
  - same workspace
  - `dry_run_only = false`
- result:
  - HTTP `422`
  - controlled validation error:
    - `body.dry_run_only` must be `true`

4. Requested blocked / unknown key
- request body extension:

```json
{
  "dry_run_only": true,
  "expected_workspace_code": "IV6-9C831ADB",
  "expected_root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "expected_product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "planner_version": "v1",
  "requested_entry_keys": [
    "svg.selected_layer_refs[]",
    "unknown.product.truth.key"
  ]
}
```

- result:
  - HTTP `200`
  - `proposed_mutations = []`
  - `refused_entries` included:
    - blocked key `svg.selected_layer_refs[]`
    - unknown key `unknown.product.truth.key`
  - no mutation proof remained all-false / unchanged

Tests run:
- `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
  - `7 passed`
- `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py -q`
  - `13 passed`
- `backend\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py -q`
  - bridge suite executed with no runtime verification blocker observed

Read-only proof:
1. live planner endpoint remained `read_only = true`
2. live dry-run endpoint returned `read_only = true` and `dry_run = true`
3. payload hash before and after matched exactly
4. planner hash before and after matched exactly
5. `confirmed_snapshot_v1` remained absent / unchanged
6. `return_cant` remained absent / unchanged
7. downstream mutation remained false
8. DB write remained false

Forbidden scope confirmation:
- no writer implemented
- no payload mutation
- no `confirmed_snapshot_v1` mutation
- no `return_cant` bridge mutation
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
1. real Product Truth writer
2. Product Truth writer UI trigger
3. ProductDefinition consumer
4. downstream systems

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_BACKEND_V1`
- Goal: implement the real Product Truth writer backend behind owner GO, reusing the verified dry-run contract, enforcing atomic refusal, and mutating only `payload_json.product_truth.confirmed_snapshot_v1`
- Boundary: no frontend CTA unless explicitly requested, no Pricing/Quote/Order/Execution changes, no ProductDefinition consumer wiring unless separately approved, no use of `payload.product_truth.components.return_cant` as generic sink