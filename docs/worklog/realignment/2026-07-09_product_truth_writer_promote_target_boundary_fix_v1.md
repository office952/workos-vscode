# PRODUCT_TRUTH_WRITER_PROMOTE_TARGET_BOUNDARY_FIX_V1

Status: PASS

Scope:
- backend boundary fix only for Product Truth writer promote persistence
- preserve existing planner semantics, dry-run semantics, refusal semantics, replay semantics, and `return_cant` bridge behavior
- ensure successful promote mutates strictly only `payload_json.product_truth.confirmed_snapshot_v1`
- no UI
- no frontend consumer
- no ProductDefinition / Pricing / Quote / Order / Execution / ProductAggregate / TaskGraph work
- no DB migration
- no live seed

HEAD before:
- `a9f2294`

Blocker reproduced before fix:
- controlled eligible fixture promote returned HTTP `200`
- changed paths outside `product_truth.confirmed_snapshot_v1` count:
  - `16`
- reproduced changed paths:
  - `finish_setup.artwork_complexity_decisions`
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
  - `schema_version`

Root cause:
- `promote_product_truth_for_workspace()` called `promote_product_truth_snapshot()` on the raw dict, but then reparsed the full payload via `IntakeV6WorkspacePayload`
- the writer path then persisted through `_persist_payload()`
- `_persist_payload()` serializes `payload.model_dump(mode="json")`
- that full-model serialization normalized unrelated fields outside the writer target, causing successful promote to rewrite untouched payload surface

Files touched:
- `backend/services/intake_v6_workspace_service.py`
- `backend/tests/test_product_truth_writer.py`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_promote_target_boundary_fix_v1.md`

Fix summary:
1. added a dedicated raw-payload persistence helper for the Product Truth writer path
2. the helper still validates the raw payload with `IntakeV6WorkspacePayload` for readiness/status derivation
3. the helper persists `record.payload_json` from the raw dict instead of from `payload.model_dump(mode="json")`
4. `promote_product_truth_for_workspace()` now uses this dedicated writer persistence path after a successful promote write
5. existing shared `_persist_payload()` remains unchanged for other update paths
6. writer tests now assert that successful promote changes only `product_truth.confirmed_snapshot_v1`, replay changes nothing, and unknown refusal mutates nothing

Changed paths outside snapshot before:
- count: `16`
- representative examples:
  - `schema_version`
  - `finish_setup.artwork_finishes`
  - `finish_setup.backing_mode`
  - `finish_setup.illuminated`
  - `finish_setup.support_required`
  - `layer_role_setup.layer_bindings`
  - `layer_role_setup.layers`

Changed paths outside snapshot after:
- count: `0`
- controlled eligible fixture promote now changes no payload path outside `product_truth.confirmed_snapshot_v1`

HTTP/control verification result:
1. eligible-only success on isolated control fixture
   - HTTP `200`
   - `write_performed = true`
   - `target_path = payload_json.product_truth.confirmed_snapshot_v1`
   - `promoted_entries` populated with 3 entries
   - changed paths outside `product_truth.confirmed_snapshot_v1`:
     - `0`
   - `return_cant` unchanged
   - downstream flags all `false`

2. replay on isolated control fixture
   - HTTP `200`
   - `write_performed = false`
   - `idempotent_replay = true`
   - payload unchanged after replay
   - `return_cant` unchanged after replay

3. mixed refusal on isolated control fixture
   - HTTP `422`
   - `detail.error = product_truth_promotion_refused`
   - payload unchanged

4. unknown requested entry refusal on isolated control fixture
   - HTTP `422`
   - `detail.error = product_truth_promotion_refused`
   - payload unchanged

5. real known blocked workspace recheck
   - promote refusal remained atomic and non-mutating
   - payload hash before/after remained unchanged
   - `return_cant` hash before/after remained unchanged
   - downstream flags remained all `false`

No downstream proof:
- success control promote returned downstream flags all `false`
- replay remained unchanged
- mixed refusal returned downstream unchanged / non-writing semantics
- unknown refusal returned downstream unchanged / non-writing semantics
- real blocked workspace refusal remained non-mutating with downstream flags all `false`

Tests run:
1. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q`
   - result: `4 passed`

2. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
   - result: `7 passed`

3. `backend\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py -q`
   - result: `11 passed`

4. `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py -q`
   - result: `13 passed`

5. combined lane
   - `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`
   - result: `31 passed`

Forbidden scope confirmation:
- no UI
- no frontend consumer
- no ProductDefinition
- no Pricing
- no Quote/Order
- no Execution
- no ProductAggregate / TaskGraph
- no DB migration
- no live seed
- no `return_cant` generic sink
- no worktree cleanup

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_PROMOTE_HTTP_VERIFICATION_V1_RERUN`
- Goal: rerun the full runtime / HTTP verification record for Product Truth writer promote and replace the prior blocked verification status with a PASS closeout if the real and controlled checks remain green
- Boundary: verification only unless a new defect is found; no UI, no ProductDefinition consumer, no Pricing/Quote/Order/Execution/ProductAggregate/TaskGraph work