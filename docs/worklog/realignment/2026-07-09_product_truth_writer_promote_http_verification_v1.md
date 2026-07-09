# PRODUCT_TRUTH_WRITER_PROMOTE_HTTP_VERIFICATION_V1

Status: BLOCKED

Scope:
- runtime / HTTP verification only for Product Truth writer promote
- verify blocked real workspace behavior on the accepted real workspace
- verify eligible-only success and idempotent replay on a safe isolated control fixture
- verify failure / control checks
- verify no `return_cant` mutation and no downstream write intent
- no feature work
- no UI
- no ProductDefinition / Pricing / Quote / Order / Execution / ProductAggregate / TaskGraph work
- no DB migration
- no seed live

HEAD before:
- `b59bd08`

Endpoints verified:
1. `GET /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-promotion-planner`
2. `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/dry-run`
3. `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/promote`

Verification environments used:
1. real known workspace via runtime HTTP/TestClient against the local dev DB with auth override only
   - workspace_id: `668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c`
   - workspace_code: `IV6-9C831ADB`
   - no live seed
   - no migration

2. eligible-only safe control fixture via isolated test DB and existing backend test fixture machinery
   - reused the existing safe test/runtime control path from `backend/tests/conftest.py`, `backend/tests/_db_fixture.py`, and `backend/tests/test_product_truth_writer.py`
   - no live seed
   - no migration

Real workspace blocked verification:
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
  - `idempotent_replay = false`
  - `target_path = payload_json.product_truth.confirmed_snapshot_v1`
  - `promoted_entries = []`
  - `refused_entries = 8`
  - payload remained unchanged before/after the request

Blocked real workspace hashes:
- workspace payload before hash:
  - `sha256:35dba65902e8e215298ffa2b377d89796dca42c16ee0f9237611afed3f7d8390`
- workspace payload after hash:
  - `sha256:35dba65902e8e215298ffa2b377d89796dca42c16ee0f9237611afed3f7d8390`
- payload unchanged:
  - `true`
- refusal response hashes:
  - `payload_hash_before == payload_hash_after`
  - `confirmed_snapshot_hash_before == confirmed_snapshot_hash_after`
  - `return_cant_bridge_hash_before == return_cant_bridge_hash_after`
  - downstream flags all `false`

Eligible-only success verification:
- safe control fixture promote response:
  - HTTP `200`
  - `write_performed = true`
  - `idempotent_replay = false`
  - `target_path = payload_json.product_truth.confirmed_snapshot_v1`
  - `promoted_entries` populated with 3 entries:
    - `finish.finish_target`
    - `finish.print_required:layer_key:logo-left`
    - `svg.selected_layer_refs[]:layer_id:face-1`
  - `confirmed_snapshot_hash_before != confirmed_snapshot_hash_after`
  - `return_cant_bridge_hash_before == return_cant_bridge_hash_after`
  - `downstream_write_intent` all `false`

Idempotency verification:
- repeated eligible-only promote response:
  - HTTP `200`
  - `write_performed = false`
  - `idempotent_replay = true`
  - `payload_hash_before == payload_hash_after`
  - `confirmed_snapshot_hash_before == confirmed_snapshot_hash_after`
  - `return_cant_bridge_hash_before == return_cant_bridge_hash_after`
  - payload unchanged after replay
  - `return_cant` unchanged after replay
  - `audit_trail` length remained `1`

Failure / control checks:
1. missing workspace
   - promote request returned HTTP `404`
   - controlled body with `detail.error = workspace_not_found`

2. template mismatch
   - promote request returned HTTP `422`
   - controlled body with `detail.error = root_template_code_mismatch`

3. `promotion_confirmed = false`
   - promote request returned HTTP `422`
   - controlled validation / contract rejection

4. missing `promotion_confirmed`
   - promote request returned HTTP `422`
   - controlled validation / contract rejection

5. unknown requested entry key
   - promote request returned HTTP `422`
   - `detail.error = product_truth_promotion_refused`
   - refused key included `unknown.product.truth.key`
   - payload unchanged
   - downstream flags all `false`

6. mixed eligible + blocked requested scope
   - promote request returned HTTP `422`
   - `detail.error = product_truth_promotion_refused`
   - refused key included `support.support_type`
   - payload unchanged

Confirmed blocker:
- expected verification target:
  - success promote should mutate strictly only `payload_json.product_truth.confirmed_snapshot_v1`
- observed runtime result on the safe control fixture:
  - success promote also rewrote payload fields outside `confirmed_snapshot_v1`
- focused discriminator check showed `16` changed paths outside `product_truth.confirmed_snapshot_v1`
- representative changed paths outside the allowed writer target:
  - `schema_version`
  - `finish_setup.artwork_finishes`
  - `finish_setup.backing_mode`
  - `finish_setup.emblem_lighting_mode`
  - `finish_setup.illuminated`
  - `finish_setup.internal_draft_quote_confirmed`
  - `finish_setup.led_module_power_w`
  - `finish_setup.led_strip_power_w_per_ml`
  - `finish_setup.letter_group_finishes`
  - `finish_setup.light_color`
  - `finish_setup.lighting_system_type`
  - `finish_setup.psu_configuration`
  - `finish_setup.support_required`
  - `layer_role_setup.layer_bindings`
  - `layer_role_setup.layers`
- meaning:
  - blocked / refusal behavior is correct
  - idempotent replay is correct after the first write
  - `return_cant` remains unchanged
  - downstream flags remain false
  - but the strict mutation-boundary proof for success promote currently fails

Likely cause of blocker:
- `promote_product_truth_for_workspace()` persists the mutated payload by re-parsing it into `IntakeV6WorkspacePayload` and then calling `_persist_payload()`
- `_persist_payload()` serializes `payload.model_dump(mode="json")`
- this normalizes / fills defaults across the broader payload surface, not just `product_truth.confirmed_snapshot_v1`

Tests run:
1. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q`
   - result: `3 passed`

2. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
   - result: `7 passed`

3. `backend\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py -q`
   - result: `11 passed`

4. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py -q`
   - result: `13 passed`

5. combined lane:
   - `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`
   - result: `31 passed`

Combined lane result:
- PASS
- the combined adjacent lane remains green even though the promote HTTP verification found the boundary defect above

No downstream proof:
- planner `downstream_write_intent` all `false`
- dry-run `downstream_write_intent` all `false`
- blocked promote refusal `downstream_write_intent` all `false`
- success control promote `downstream_write_intent` all `false`
- replay `downstream_write_intent` remained unchanged and all `false`

Forbidden scope confirmation:
- no UI added
- no ProductDefinition added
- no Pricing change
- no Quote/Order change
- no Execution change
- no ProductAggregate / TaskGraph change
- no DB migration
- no live seed
- no `return_cant` generic sink
- no worktree cleanup

Verdict:
- `PRODUCT_TRUTH_WRITER_PROMOTE_HTTP_VERIFICATION_BLOCKED`
- blocker reason:
  - the success promote path does not currently prove strict mutation containment to `payload_json.product_truth.confirmed_snapshot_v1`

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_PROMOTE_TARGET_BOUNDARY_FIX_V1`
- Goal: fix the promote persistence path so a successful Product Truth writer promote mutates only `payload_json.product_truth.confirmed_snapshot_v1` and does not normalize or rewrite unrelated payload fields, then rerun this HTTP verification slice
- Boundary: backend writer persistence fix only; no UI, no ProductDefinition consumer, no Pricing/Quote/Order/Execution/ProductAggregate/TaskGraph work, no DB migration, no live seed