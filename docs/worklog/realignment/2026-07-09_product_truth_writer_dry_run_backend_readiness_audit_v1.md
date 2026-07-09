# PRODUCT_TRUTH_WRITER_DRY_RUN_BACKEND_READINESS_AUDIT_V1

Status: PASS

Explicit statement:
- NO CODE IMPLEMENTATION
- no Product Truth writer implemented
- no dry-run endpoint implemented
- no POST endpoint implemented
- no router added
- no service added
- no schema added
- no UI button implemented
- no workspace payload mutation performed by this task
- no Product Truth storage mutation performed by this task
- no DB schema change
- no migration
- no seed

Scope:
- docs-only backend readiness audit for a future Product Truth Writer Dry-Run implementation
- identify the future insertion points, helper boundaries, hash sources, test seams, and implementation risks
- preserve the canonical target path `payload_json.product_truth.confirmed_snapshot_v1`
- preserve the rule that `payload.product_truth.components.return_cant` is not the generic sink for Product Truth dry-run or writer behavior

HEAD before:
- `635c73f`

Files read:
- `docs/worklog/realignment/2026-07-09_product_truth_writer_dry_run_response_fixture_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_dry_run_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_storage_target_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_readiness_audit_v1.md`
- `backend/services/product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/models/intake_v6_workspace.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/tests/test_return_cant_product_truth_bridge.py`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`

Backend insertion point audit:

Observed repo pattern today:
1. HTTP surfaces live in `backend/routers/intake_v6_workspaces.py`
2. workspace-oriented orchestration lives in `backend/services/intake_v6_workspace_service.py`
3. specialized read-only or dry-run builders are delegated to dedicated services such as:
   - `services.intake_v6_production_task_dry_run_service`
   - `services.intake_v6_task_generation_dry_run_service`
   - `services.intake_v6_priced_quote_dry_run_service`
4. payload persistence remains centralized through `_persist_payload(...)` in the workspace service

Recommended future insertion point:
- router:
  keep the future dry-run route inside `backend/routers/intake_v6_workspaces.py`, not a new router
- workspace service:
  add a new orchestration function in `backend/services/intake_v6_workspace_service.py` that:
  - resolves workspace
  - reads payload only
  - invokes planner or its exact backend decision basis
  - delegates mutation planning to a dedicated dry-run builder service
  - returns response only
- dedicated service:
  future dry-run computation should live in a new dedicated service, not inside `product_truth_promotion_planner_service.py`

Recommended future files that would likely be touched when implementation is approved:
1. `backend/routers/intake_v6_workspaces.py`
2. `backend/services/intake_v6_workspace_service.py`
3. new dedicated service, likely:
   - `backend/services/product_truth_writer_dry_run_service.py`
4. existing schema surface file, likely:
   - `backend/schemas/intake_v6.py`
5. new focused tests, likely:
   - `backend/tests/test_product_truth_writer_dry_run_service.py`
   - `backend/tests/test_product_truth_writer_dry_run_endpoint.py`

Why this insertion point is the safest match for the repo:
1. it follows the existing router -> workspace service -> builder service pattern already used for dry-run and preview surfaces
2. it keeps planner semantics isolated in `product_truth_promotion_planner_service.py`
3. it keeps persistence centralized and therefore easier to prove absent
4. it allows the dry-run to consume planner output without turning planner itself into a writer-adjacent service

Recommendation on service boundary:
- planner service remains read-only classifier only
- future dry-run service consumes planner output and computes:
  - proposed mutations
  - refused entries
  - no-mutation proof
  - deterministic hashes
- workspace service remains the orchestration and workspace lookup boundary
- no future dry-run helper should call `_persist_payload(...)`

Recommendation on schema placement:
- if implementation is later approved, request/response types should most likely be added into `backend/schemas/intake_v6.py` to match the existing route shape convention
- do not create a schema file now
- do not create runtime types now

Hash sources audit:

1. `payload_hash_before`
- input should include:
  - canonical JSON of the current workspace payload as loaded from `payload_json`
- input should exclude:
  - request actor metadata
  - response notes
  - any computed timestamps
  - any unordered incidental Python object formatting
- why stable:
  - same payload bytes or canonical serialized payload produce the same hash
- false mismatch risk:
  - non-canonical key ordering
  - normalization differences between dict and model representations
  - including read-only computed fields not actually present in payload

2. `planner_hash`
- input should include:
  - planner version
  - workspace identity basis
  - template basis
  - normalized `eligible_entries`
  - normalized `blocked_entries`
  - normalized `blockers`
  - normalized `downstream_write_intent`
- input should exclude:
  - notes text ordering if not normalized
  - actor
  - endpoint-level transport metadata
- why stable:
  - planner output is deterministic for the same payload and template basis
- false mismatch risk:
  - non-deterministic ordering of entries or blockers
  - textual notes changing without semantic change
  - including response-only wrappers like `read_only`

3. `planner_entry_hash`
- input should include:
  - `entry_key`
  - `field_key`
  - normalized runtime source path
  - normalized Product Truth path from planner
  - state
  - value status
  - identity key if present
  - normalized value for eligible entries or normalized blocker bundle for refused entries
- input should exclude:
  - actor
  - promotion hash
  - batch-level response notes
- why stable:
  - it isolates the exact planner decision for one entry
- false mismatch risk:
  - serializing booleans or nulls inconsistently
  - hashing human reason text instead of normalized decision fields

4. `promotion_hash`
- input should include:
  - `idempotency_basis`
- input should exclude:
  - actor
  - response notes
  - refusal-only entries when contract defines basis only on proposed writes
- why stable:
  - batch identity becomes deterministic for the same workspace, planner basis, and normalized proposed mutation set
- false mismatch risk:
  - entry ordering not sorted
  - accidental inclusion of non-semantic text fields
  - including generated timestamps

5. `idempotency_basis`
- input should include:
  - `workspace_id`
  - `workspace_code`
  - `root_template_code`
  - `product_binding_template_code`
  - `planner_version`
  - `planner_hash`
  - `payload_hash_before`
  - sorted normalized proposed entries
- input should exclude:
  - actor
  - request UUIDs
  - notes
  - response hash
- why stable:
  - it represents state-equivalent dry-run computation rather than caller identity
- false mismatch risk:
  - including optional request fields that do not change the mutation set
  - using raw dicts without canonical serialization

6. `response_hash` optional
- input should include:
  - canonical JSON of final dry-run response after all deterministic fields are set
- input should exclude:
  - fields intentionally allowed to vary such as human formatting or non-canonical timestamps, if any exist
- why stable:
  - useful as a fixture/test-only integrity signal, not required for core contract
- false mismatch risk:
  - if notes or debug-only metadata change order
  - if response embeds non-deterministic diagnostic text

Hash source recommendation:
- canonical serializer must be one shared helper
- hash sources must be built from normalized data structures, not ad hoc string concatenation
- reason text should not be part of core identity hashes unless normalized as contract data

Proposed mutation builder audit:

Future helper boundaries recommended:
1. `build_dry_run_response(...)`
   - orchestrates final read-only response assembly
   - consumes planner output, request expectations, mutation planning, and proof fields
2. `build_proposed_mutations(...)`
   - transforms only `eligible_entries` into deterministic `would_write` mutation objects
3. `build_refused_entries(...)`
   - transforms blocked or mismatched requested entries into deterministic `refused` objects
4. `build_no_mutation_proof(...)`
   - computes before/after equality proof fields without performing any write
5. `build_downstream_write_intent_false(...)`
   - central helper for explicit all-false write intent contract
6. `compute_promotion_hash(...)`
   - hashes the finalized `idempotency_basis`
7. `compute_planner_hash(...)`
   - hashes normalized planner output
8. `compute_planner_entry_hash(...)`
   - hashes one normalized entry decision
9. `map_entry_to_confirmed_snapshot_target(...)`
   - central deterministic target path resolver for current planner families

Recommended helper ownership:
- dry-run response builder helpers belong in the future dedicated dry-run service
- planner hash helpers may live there too unless reused later by real writer
- target path mapping must not live inside the return/cant bridge
- no helper should mutate `payload_raw`

Builder design rules:
1. proposed mutation builder must accept normalized planner data, not re-read workspace arbitrarily
2. refused entry builder must preserve blocker codes and state semantics exactly
3. no-mutation proof helper must compare canonical payload/planner basis before and after builder execution
4. downstream intent helper must not infer or derive any true flag from unrelated services

Target path mapping audit:

Canonical target root:
- every future dry-run proposed mutation must map under:
  `payload_json.product_truth.confirmed_snapshot_v1`

Current family mapping recommendation:
1. `svg.selected_layer_refs[]`
   - source basis: stable `layer_id`
   - recommended target pattern:
     `payload_json.product_truth.confirmed_snapshot_v1.entries.svg.selected_layer_refs[layer_id:<id>]`
2. `finish.finish_target`
   - source basis: scalar
   - recommended target pattern:
     `payload_json.product_truth.confirmed_snapshot_v1.entries.finish.finish_target`
3. `finish.print_required`
   - source basis: stable `layer_key`
   - recommended target pattern:
     `payload_json.product_truth.confirmed_snapshot_v1.entries.finish.print_required[layer_key:<key>]`
4. `finish.lamination_required`
   - source basis: stable `layer_key`
   - recommended target pattern:
     `payload_json.product_truth.confirmed_snapshot_v1.entries.finish.lamination_required[layer_key:<key>]`
5. `mounting.mounting_scope`
   - source basis: scalar
   - recommended target pattern:
     `payload_json.product_truth.confirmed_snapshot_v1.entries.mounting.mounting_scope`
6. `support.support_type`
   - source basis: scalar
   - recommended target pattern:
     `payload_json.product_truth.confirmed_snapshot_v1.entries.support.support_type`

Mapping rules:
1. target path must be deterministic from `field_key` plus row identity when applicable
2. blocked entries do not receive `proposed_mutations`
3. refused entries may still carry the determinable future target path
4. row identity must stay explicit and never degrade to array-position identity

Critical boundary:
- `payload.product_truth.components.return_cant` is not a generic target mapping destination
- no target mapper may route generic Product Truth dry-run output into `payload.product_truth.components.*`
- if return/cant later gains canonical promotion eligibility, it must still map into `confirmed_snapshot_v1`

Fail-closed checks:

Required future dry-run checks:
1. missing workspace -> controlled `404`
2. planner `read_only` must be `true`
3. all `downstream_write_intent` flags must be `false`
4. `planner_version` must match expected input
5. `root_template_code` must match expected input
6. `product_binding_template_code` must match expected input
7. stale `planner_hash` must refuse dry-run
8. changed `payload_hash_before` basis must refuse dry-run
9. `requested_entry_keys` must not promote any blocked entry
10. blocked entries must be refused, never promoted
11. no ProductDefinition mutation
12. no Pricing mutation
13. no Quote mutation
14. no Order mutation
15. no Execution mutation

Additional recommended checks:
1. if `expected_workspace_code` is provided, mismatch refuses dry-run
2. duplicate `requested_entry_keys` with conflicting interpretations must refuse dry-run
3. response must explicitly keep `read_only = true` and `dry_run = true`
4. if any future helper attempts persistence, tests must fail

Test seams:

Future tests that should exist before any real dry-run rollout:
1. success eligible entries -> `proposed_mutations`
2. blocked entries -> `refused_entries`
3. zero eligible / many blocked -> `proposed_mutations` empty
4. mixed dry-run visibility -> both lists present, writer policy still fail-closed
5. stale planner hash refused
6. stale payload hash refused
7. template mismatch refused
8. missing workspace `404`
9. deterministic repeated dry-run
10. no payload mutation
11. no planner mutation
12. target path exact `confirmed_snapshot_v1`
13. return_cant bridge not used as generic sink
14. no downstream mutation

Recommended seam locations:
- service-level tests for deterministic dry-run builder output
- endpoint-level tests for request/response boundary and `404` behavior
- payload-before/payload-after assertions at service and endpoint levels
- planner-before/planner-after assertions when the dry-run consumes planner output

Recommended fixture seam reuse:
- reuse planner fixture patterns from:
  - `backend/tests/test_product_truth_promotion_planner_service.py`
  - `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- reuse no-unintended-mutation discipline from:
  - `backend/tests/test_return_cant_product_truth_bridge.py`

Endpoint proposal:

Proposal only, not implemented in this task:
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/dry-run`

Why POST is still acceptable for read-only semantics:
1. dry-run request needs structured request body fields such as expected template basis, planner hash, actor placeholder, and requested entry subset
2. operation remains semantically read-only despite POST transport
3. tests must prove no mutation despite POST

Endpoint contract rules:
- proposal only
- not implemented in this task
- POST dry-run remains read-only semantic
- it is not the real writer
- there is no UI button yet

Recommended future route placement:
- same router file: `backend/routers/intake_v6_workspaces.py`
- keep it adjacent to existing product-truth and dry-run routes, not in a new router

Implementation risks:

Primary risks before implementation:
1. accidental payload mutation through shared dict references or helper reuse
2. accidental reuse of `payload.product_truth.components.return_cant` as generic target
3. stale planner accepted because planner hash or payload hash is computed from the wrong basis
4. frontend or downstream code treating dry-run output as canonical Product Truth
5. blocked entries silently downgraded into warnings or omitted refusals
6. dry-run response being copied later as if it were persisted Product Truth
7. downstream systems consuming dry-run output directly
8. non-deterministic hashing due to unordered serialization
9. planner semantics drifting because dry-run starts reinterpreting blocked or suggested states

Risk mitigation direction:
1. use dedicated pure builders and never call `_persist_payload(...)`
2. use canonical serialization helpers for all hashes
3. keep target mapping centralized and explicitly ban `payload.product_truth.components.*`
4. keep `read_only`, `dry_run`, and no-mutation proof fields mandatory
5. keep blocked-to-refused logic explicit and test-covered
6. keep the future real writer atomic even if dry-run shows mixed visibility

Roadmap awareness checkpoint:
- roadmap alignment score: `10/10`
- current spine position:
  `Product System -> Form System -> Intake V6 runtime payload -> Runtime Capture Read Model -> Product Truth Promotion Planner -> Planner Endpoint -> Planner UI Consumer -> Product Truth Writer Readiness Audit -> Product Truth Storage Target Contract -> Product Truth Writer Dry-Run Contract -> Product Truth Writer Dry-Run Response Fixtures -> Product Truth Writer Dry-Run Backend Readiness Audit`
- direction alignment: `99/100%`
- dead pieces check:
  - no runtime code introduced
  - no endpoint introduced
  - no router introduced
  - no service introduced
  - no schema introduced
  - no payload branch introduced
  - no DB or migration artifact introduced
- forbidden scope confirmation:
  - no writer
  - no endpoint
  - no router
  - no service
  - no schema
  - no UI CTA
  - no payload mutation
  - no DB migration
  - no seed live
  - no Pricing / Quote / Order / Execution
  - no ProductDefinition consumer
  - no ProductAggregate / TaskGraph / ExecutionPlan

Forbidden scope confirmation:
- no writer implemented
- no dry-run endpoint added
- no POST endpoint added
- no router added
- no service added
- no schema added
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
- `TASK — PRODUCT_TRUTH_WRITER_DRY_RUN_BACKEND_REQUEST_RESPONSE_SCHEMA_AUDIT_V1`
- Goal: define docs-only the exact future request/response schema fields, types, field optionality, and validation rules for the dry-run backend surface before implementation begins
- Boundary: no backend implementation, no endpoint, no router, no service, no payload mutation, no DB migration, no ProductDefinition consumer changes