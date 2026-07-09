# PRODUCT_TRUTH_WRITER_PROMOTE_HTTP_VERIFICATION_RERUN_V1

Status: PASS

Scope:
- runtime / HTTP verification rerun only for Product Truth writer promote after accepted boundary fix `183d44d`
- verify real blocked workspace refusal and no-mutation proof
- verify eligible-only success, replay idempotency, and control failures on isolated fixture/runtime path
- no feature work
- no UI
- no frontend consumer
- no ProductDefinition / Pricing / Quote / Order / Execution / ProductAggregate / TaskGraph work
- no DB migration
- no live seed

HEAD before:
- `183d44d`

Endpoints verified:
1. `GET /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-promotion-planner`
2. `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/dry-run`
3. `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/promote`

Verification environments used:
1. real known blocked workspace on local `backend/dev.db`
   - workspace_id: `668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c`
   - workspace_code: `IV6-9C831ADB`
   - verified through HTTP/TestClient with auth override and explicit `get_db` override pointed at the same local `dev.db`
   - no live seed
   - no migration

2. eligible-only safe control fixture via isolated backend test DB
   - reused the existing fixture/runtime path from `tests/_db_fixture.py`, `tests/conftest.py`, and `tests/test_product_truth_writer.py`
   - no live seed
   - no migration

Real workspace blocked / no-mutation result:
- planner response:
  - HTTP `200`
  - `read_only = true`
  - `workspace_code = IV6-9C831ADB`
  - `eligible_entries = 0`
  - `blocked_entries = 8`
  - `downstream_write_intent` all `false`

- dry-run response:
  - HTTP `200`
  - `proposed_mutations = 0`
  - `refused_entries = 8`
  - `no_mutation_proof.payload_hash_unchanged = true`
  - `no_mutation_proof.planner_hash_unchanged = true`
  - `no_mutation_proof.product_truth_target_mutated = false`
  - `no_mutation_proof.return_cant_bridge_mutated = false`
  - `no_mutation_proof.downstream_mutated = false`
  - `no_mutation_proof.db_write_performed = false`

- blocked promote response:
  - HTTP `422`
  - `detail.error = product_truth_promotion_refused`
  - `write_performed = false`
  - `promoted_entries = 0`
  - payload unchanged before/after request
  - `payload_hash_before == payload_hash_after`
  - `confirmed_snapshot_hash_before == confirmed_snapshot_hash_after`
  - `return_cant_bridge_hash_before == return_cant_bridge_hash_after`
  - `downstream_write_intent` all `false`

Eligible-only success result:
- safe control fixture promote response:
  - HTTP `200`
  - `write_performed = true`
  - `target_path = payload_json.product_truth.confirmed_snapshot_v1`
  - `promoted_entries = 3`
  - `return_cant` unchanged
  - `downstream_write_intent` all `false`

Target boundary proof:
- changed paths outside `product_truth.confirmed_snapshot_v1` after success promote:
  - `0`
- changed path list outside target:
  - `[]`

Replay / idempotency result:
- repeated eligible-only promote response:
  - HTTP `200`
  - `write_performed = false`
  - `idempotent_replay = true`
  - payload unchanged after replay
  - `confirmed_snapshot_v1` unchanged after replay
  - `return_cant` unchanged after replay
  - downstream unchanged and all `false`

Failure / control checks:
1. missing workspace
   - HTTP `404`
   - `detail.error = workspace_not_found`

2. template mismatch
   - HTTP `422`
   - `detail.error = root_template_code_mismatch`

3. `promotion_confirmed = false`
   - HTTP `422`
   - controlled request-body validation rejection

4. missing `promotion_confirmed`
   - HTTP `422`
   - controlled request-body validation rejection

5. unknown requested key
   - HTTP `422`
   - `detail.error = product_truth_promotion_refused`
   - payload unchanged

6. mixed eligible + blocked requested scope
   - HTTP `422`
   - `detail.error = product_truth_promotion_refused`
   - payload unchanged

Tests run:
1. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q`
   - result: `4 passed`

2. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
   - result: `7 passed`

3. `backend\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py -q`
   - result: `11 passed`

4. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py -q`
   - result: `13 passed`

Combined lane result:
1. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`
   - result: `31 passed`

No downstream proof:
- planner `downstream_write_intent` all `false`
- dry-run `downstream_write_intent` all `false`
- blocked promote refusal `downstream_write_intent` all `false`
- success control promote `downstream_write_intent` all `false`
- replay left downstream unchanged and all `false`
- mixed refusal and unknown refusal remained non-mutating and downstream-false

Forbidden scope confirmation:
- no UI added
- no frontend consumer
- no ProductDefinition added
- no Pricing
- no Quote/Order
- no Execution
- no ProductAggregate / TaskGraph
- no DB migration
- no live seed
- no `return_cant` generic sink
- no worktree cleanup
- no code change

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_UI_TRIGGER_V1`
- Goal: add the first explicit operator/UI trigger for Product Truth writer promote while preserving the confirmed-snapshot-only backend boundary and existing refusal/idempotency guarantees
- Boundary: UI trigger only; no ProductDefinition consumer, no downstream Pricing/Quote/Order/Execution wiring unless explicitly expanded