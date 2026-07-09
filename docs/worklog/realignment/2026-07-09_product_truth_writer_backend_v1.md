# PRODUCT_TRUTH_WRITER_BACKEND_V1

Status: PASS

Scope:
- implement the real backend Product Truth writer
- reuse the existing dry-run contract as the only mutation basis
- enforce atomic refusal when the requested scope contains blocked or unknown entries
- persist only into `payload_json.product_truth.confirmed_snapshot_v1`
- keep `payload.product_truth.components.return_cant` untouched
- add focused backend tests for write, refusal, and idempotent replay

HEAD before:
- `06b5752`

Files touched:
- `backend/services/product_truth_writer_service.py`
- `backend/services/product_truth_writer_dry_run_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/schemas/intake_v6.py`
- `backend/tests/test_product_truth_writer.py`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_backend_v1.md`

Endpoint added:
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/promote`

Request contract:
- `promotion_confirmed = true`
- `expected_workspace_code`
- `expected_root_template_code`
- `expected_product_binding_template_code`
- `planner_version`
- optional `planner_hash`
- optional `payload_hash_basis`
- optional `actor`
- optional `requested_entry_keys`

Writer behavior:
1. orchestration rebuilds the dry-run request from the promote request
2. writer reuses dry-run output as the sole proposed/refused decision basis
3. if the requested scope produces any `refused_entries`, the writer fails closed with HTTP `422`
4. no partial promotion is allowed
5. if all requested values already match the stored confirmed snapshot, the response is an idempotent replay with no write
6. otherwise the writer persists only inside `payload_json.product_truth.confirmed_snapshot_v1`

Persisted target shape:
- `metadata`
- `planner_basis`
- `entries`
- `audit_trail`

Entry persistence rules:
- every promoted entry is stored under its deterministic field path inside `entries`
- scalar and identity-scoped rows keep their value plus provenance bundle
- stored records preserve `entry_key`, `field_key`, `source_path`, `target_path`, `planner_entry_hash`, `promotion_hash`, and provenance
- replay comparison reads the stored `value` field so a second identical request is recognized as idempotent

Atomic refusal rules:
- requested blocked entry -> whole request refused
- requested unknown entry -> whole request refused
- no requested success entries are written when any refusal exists in the same request scope
- refusal response includes hashes proving payload, confirmed snapshot, and `return_cant` remained unchanged

Bridge boundary confirmation:
- `payload.product_truth.components.return_cant` is never used as the generic sink
- writer responses include before/after hashes for the `return_cant` subtree
- focused tests prove the subtree is unchanged on successful promotion and on refusal

Validations run:
- `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
- `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q`
- `backend\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`

Focused test coverage:
- successful promotion into `confirmed_snapshot_v1`
- atomic refusal when requested scope includes a blocked entry
- idempotent replay performs no second write and does not append audit trail

Forbidden scope confirmation:
- no UI button
- no frontend consumer
- no ProductDefinition consumer
- no Pricing / Quote / Order / Execution mutation
- no ProductAggregate / TaskGraph / ExecutionPlan mutation
- no DB schema change
- no migration
- no seed live

Commit message:
- `Add product truth writer backend`