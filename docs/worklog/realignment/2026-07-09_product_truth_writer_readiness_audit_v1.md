# PRODUCT_TRUTH_WRITER_READINESS_AUDIT_V1

Status: PASS

Explicit statement:
- NO CODE IMPLEMENTATION
- no Product Truth writer implemented
- no writer endpoint implemented
- no UI button implemented
- no payload, DB, Pricing, Quote, Order, Execution, ProductDefinition consumer, ProductAggregate, TaskGraph, or migration changes

Scope:
- docs and boundary audit only for a future Product Truth writer
- anchored on the accepted read-only chain:
  - runtime capture read model
  - Product Truth promotion planner service
  - planner endpoint
  - endpoint metadata alignment
  - planner UI consumer

HEAD before:
- `90e834a`

Files read:
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_ui_consumer_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_endpoint_metadata_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_promotion_planner_endpoint_v1.md`
- `backend/services/product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- `frontend/src/components/workos/intake-v6/ProductTruthPromotionPlannerPanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`

Current read-only chain:
1. Runtime Capture Read Model classifies six current Product Truth-related field families in a fail-closed way.
2. Product Truth Promotion Planner wraps that read model and re-checks stable identity plus explicit confirmation from workspace payload evidence.
3. Planner endpoint exposes the planner response as read-only.
4. Planner endpoint metadata aligns workspace and template context through:
   - `workspace.template_code -> root_template_code`
   - `workspace.payload.product_binding.template_code -> product_binding_template_code`
5. Planner UI consumer exposes the result in Intake V6 Review without any mutate, promote, or confirm CTA.

Planner output audit:

Planner metadata currently exposed:
- `read_only`
- `workspace_id`
- `workspace_record_id`
- `workspace_code`
- `root_template_code`
- `product_binding_template_code`
- `planner_version`
- `eligible_entries[]`
- `blocked_entries[]`
- `blockers[]`
- `downstream_write_intent`
- `notes[]`

Metadata provenance:
- `root_template_code` comes from `workspace.template_code`
- `product_binding_template_code` comes from `workspace.payload.product_binding.template_code`

Current planner field families:
1. `svg.selected_layer_refs[]`
   - runtime source: `svg.selected_layer_refs[]`
   - Product Truth path: `svg.selected_layer_refs[]`
   - canonical identity rule: stable `layer_id`
2. `finish.finish_target`
   - runtime source: `finish_setup.finish_target`
   - Product Truth path: `components.finish.target`
3. `finish.print_required`
   - runtime source: `finish_setup.artwork_finishes[].print_required`
   - Product Truth path: `components.artwork.items[].printRequired`
   - canonical identity rule: stable `layer_key`
4. `finish.lamination_required`
   - runtime source: `finish_setup.artwork_finishes[].lamination_required`
   - Product Truth path: `components.artwork.items[].laminationRequired`
   - canonical identity rule: stable `layer_key`
5. `mounting.mounting_scope`
   - runtime source: `finish_setup.mounting_scope`
   - Product Truth path: `components.mounting.mountingScope`
6. `support.support_type`
   - runtime source: `finish_setup.support_type`
   - Product Truth path: `components.support.supportType`

What enters `eligible_entries` now:
- only confirmed runtime capture fields with explicit value and stable canonical identity
- for scalars: value present and `finish_setup.confirmed = true`
- for selected layer refs: persisted ref exists, `confirmed = true`, stable `layer_id`, no ambiguity
- for artwork booleans: row has stable `layer_key`, explicit boolean, and row/setup confirmation

What enters `blocked_entries` now:
- missing fields
- present but unconfirmed fields
- suggested evidence only
- hydrated values without confirmation
- partial selected-layer evidence
- ambiguous or invalid row identity
- artwork rows with derived `execution_type` evidence but no explicit boolean

Observed and code-defined blocker families:
- `SELECTED_LAYER_REFS_MISSING`
- `SELECTED_LAYER_REF_INVALID`
- `SELECTED_LAYER_ID_MISSING`
- `SELECTED_LAYER_REFS_AMBIGUOUS`
- `SELECTED_LAYER_REFS_UNCONFIRMED`
- `FINISH_TARGET_MISSING`
- `MOUNTING_SCOPE_MISSING`
- `SUPPORT_TYPE_MISSING`
- `ARTWORK_ROW_INVALID`
- `ARTWORK_ROW_IDENTITY_MISSING`
- `ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING`
- `ARTWORK_ROW_CONFIRMATION_MISSING`
- plus runtime-capture-sourced boolean blockers such as `PRINT_REQUIRED_UNKNOWN` and `LAMINATION_REQUIRED_UNKNOWN`
- fallback scalar blocker path may also produce `CONFIRMATION_REQUIRED` when a value exists but has no explicit confirmation blocker from upstream

Observed planner states across service logic and tests:
- `confirmed`
- `missing`
- `blocked`
- `suggested`
- `hydrated`
- `partial`

Observed value status shapes across service logic:
- `explicit_confirmed`
- `invalid_ref_shape`
- `missing_identity`
- `ambiguous_identity`
- `present_unconfirmed`
- `persisted_but_unconfirmed`
- `layer_role_evidence_only`
- `evidence_only`
- `missing_rows`
- `invalid_row_shape`
- `derived_evidence_only`
- `missing_boolean`
- `missing`

Live verified planner summary on workspace `668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c`:
- `0 eligible`
- `8 blocked`
- `read_only = true`
- all `10/10` downstream write flags false

Proposed writer boundary:

A future Product Truth writer would be allowed to:
1. consume the planner response or reproduce its exact backend decision boundary server-side
2. promote only entries that are currently in `eligible_entries`
3. preserve provenance for every write:
   - source runtime path
   - Product Truth target path
   - planner state at promotion time
   - canonical identity key where applicable
   - actor and timestamp
4. write only into an explicitly approved Product Truth target zone
5. be idempotent for the same workspace plus same eligible entry set plus same payload/planner basis
6. refuse any entry not present in `eligible_entries`
7. refuse any entry with state `suggested`, `hydrated`, `fallback`, `partial`, `blocked`, or `missing`
8. preserve row-level identity boundaries:
   - `layer_id` for selected-layer truth
   - `layer_key` for artwork row truth
9. leave planner semantics untouched; writer consumes planner verdicts, it does not reinterpret them
10. stop at Product Truth promotion only and not chain into ProductDefinition, Pricing, Quote, Order, Execution, ProductAggregate, or TaskGraph

Writer target shape guidance:
- target must remain a Product Truth zone, not a commercial or downstream zone
- target must keep field-level and row-level truth separated
- target must preserve whether truth came from scalar confirmation, row confirmation, or selected-layer confirmation
- target must not collapse multiple artwork rows into a lossy aggregate

Forbidden writer behavior:
1. must not write any `blocked_entries`
2. must not invent values missing from payload or planner
3. must not auto-confirm SVG analyzer suggestions
4. must not convert `hydrated`, `fallback`, `suggested`, `partial`, or `derived_evidence_only` into confirmed truth
5. must not repair missing truth by consulting ProductDefinition, Pricing, Quote, Order, Execution, ProductAggregate, or TaskGraph
6. must not write ProductDefinition
7. must not write Pricing, Quote, Order, or Execution state
8. must not create ProductAggregate, TaskGraph, or ExecutionPlan
9. must not move canonical truth responsibility into frontend state or browser memory
10. must not change planner semantics to make writes easier
11. must not mutate the workspace payload outside the explicitly approved Product Truth target zone
12. must not silently merge ambiguous row identities or duplicate `layer_id` values

Writer preconditions for a future implementation task:
1. planner endpoint and planner service remain green before writer work starts
2. planner still proves no payload mutation before writer work
3. writer task has explicit owner GO
4. explicit confirmation model exists for who is allowed to promote and under what operator/owner boundary
5. Product Truth target zone is named and approved before implementation
6. backend must enforce the same fail-closed planner guard server-side; frontend UI is not sufficient
7. payload hash or equivalent deterministic workspace basis must be captured before promotion and compared after dry-run planning
8. audit trail and provenance are mandatory for every promoted entry
9. idempotency key or deterministic promotion hash is mandatory
10. writer request must assert no downstream write intent and must not continue if any downstream write flag changes unexpectedly
11. tests must exist for blocked refusal and no planner payload mutation regression
12. tests must prove writer mutates only the Product Truth target zone

Minimum future writer test boundary:
- planner endpoint still returns read-only response
- blocked entries are refused
- missing workspace returns controlled `404`
- same request is idempotent
- payload mutation is intentional only in Product Truth target
- no Pricing mutation
- no Quote mutation
- no Order mutation
- no Execution mutation
- source and state provenance preserved
- duplicate identity or ambiguous identity refused

Future writer acceptance criteria:
1. POST writer endpoint is allowed only after owner GO
2. no frontend promote button before backend writer is implemented and tested
3. writer must accept eligible entries only
4. writer must refuse blocked entries deterministically
5. writer must return controlled `404` for missing workspace
6. writer must mutate only Product Truth target data and nothing else in workspace payload
7. writer must preserve source path, Product Truth path, planner state, and identity key provenance
8. writer must be idempotent for repeated requests on the same planner basis
9. writer must not trigger ProductDefinition, Pricing, Quote, Order, Execution, ProductAggregate, or TaskGraph behavior
10. writer tests must include payload-before/payload-after assertions scoped to the approved Product Truth target

Recommended future implementation sequence:
1. define approved Product Truth storage target and provenance schema in docs first
2. add backend dry-run writer contract that returns proposed mutation set without writing
3. add backend writer tests for eligible-only and blocked refusal
4. only then add real writer endpoint behind owner GO
5. only after backend proof exists, consider a frontend CTA gated by explicit permissions

Why writer is still not ready today:
- live verified workspace still has `0 eligible` and `8 blocked`
- planner proves the current path is diagnostic-only, not promotion-ready
- Product Truth target zone is not yet explicitly approved in the documents read here
- owner/operator confirmation semantics for a real promotion action are not yet formalized as a write contract

Forbidden scope confirmation:
- no Product Truth writer
- no endpoint added
- no UI button added
- no Product Truth mutation
- no Pricing
- no Quote/Order
- no Execution
- no ProductDefinition consumer
- no ProductAggregate/TaskGraph
- no DB migration
- no seed live

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_STORAGE_TARGET_CONTRACT_V1`
- Goal: define, docs-only, the exact approved backend Product Truth target zone, mutation granularity, provenance schema, and idempotency basis required before any writer implementation can start
- Boundary: no writer implementation, no endpoint, no UI CTA, no DB migration, no ProductDefinition consumer changes