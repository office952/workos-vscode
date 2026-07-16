## Research — Snapshot and execution identity audit

Task: `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_RUNTIME_CLOSEOUT`

Research verdict: **PRESERVED_WITH_EXPLICIT_LEGACY_READ_BRIDGE**

---

### Scope & question

Prove whether **canonical root identity** and **linked-child identities** are:

- frozen (captured once into immutable snapshot JSON), then
- consumed later (execution plan + tasks) without mutable live reconstruction (no live template/dossier/intake reads post-freeze).

Templates tracked:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`

---

### Canonical identity + legacy alias bridge

#### Canonical template codes (authoritative constants)

Evidence:

- `backend/services/template_architecture_scope.py`
  - `VOLUMETRIC_V2_TEMPLATE_CODE`
  - `ACM_BOXED_MOUNTING_TEMPLATE_CODE`
  - `STRUCTURE_PREMOUNT_TEMPLATE_CODE`

#### Legacy alias bridge (explicit, bounded)

Evidence:

- `backend/services/template_architecture_scope.py`
  - `resolve_template_identity(template_code)`
  - `RUNTIME_TEMPLATE_CODE_BY_ALIAS`

Contract summary:

- Normalizes (trim + uppercase).
- If alias exists, returns explicit metadata (`resolution_type="legacy_read_bridge"` and `canonical_template_code=<mapped>`).
- Active compilation/freezing flows are not permitted to silently accept legacy aliases (see next section).

#### Active compilation/freeze routes reject legacy aliases (HTTP 422)

Evidence:

- `backend/tests/test_product_system_identity_boundary.py`
  - uses `require_canonical_template_code(...)`
  - compilation-style routes reject legacy alias inputs (template identity must be canonical)

---

### Freeze point #1 — Quote Snapshot V2 (immutable quote truth package)

#### Persistence location (frozen store)

Evidence:

- `backend/models/quote_snapshot_v2.py`
  - `QuoteSnapshotV2Record.snapshot_json` (full frozen payload)

#### Identity fields (schema)

Evidence:

- `backend/schemas/quote_snapshot_v2.py`
  - `QuoteSnapshotV2.template_code` (root identity)
  - `QuoteSnapshotV2.product_definition_snapshot`
  - `QuoteSnapshotV2.product_aggregate_snapshot`
  - `QuoteSnapshotV2.component_instances[]`
    - includes `source_template_code` (linked-child identity origin)
  - `QuoteSnapshotV2.offer_scope_snapshot`

#### Freeze path is the pre-freeze live-read zone (allowed)

Evidence:

- `backend/services/intake_v6_quote_snapshot_v2_service.py`
  - creates/persists the Quote Snapshot V2 payload into `QuoteSnapshotV2Record.snapshot_json`

Boundary note:

- This is the only intended zone where live templates/dossier/intake workspace may be read to assemble a snapshot; downstream execution must not re-read.

---

### Freeze point #2 — Order Snapshot V2 (order-level frozen truth)

#### Persistence location

Evidence:

- `backend/schemas/order_snapshot_v2.py` (schema shape)
- `backend/tests/test_order_snapshot_v2_schema.py` (asserts order columns exist)

Stored on `orders` row:

- `orders.quote_snapshot_v2_id` (FK to quote_snapshots_v2)
- `orders.snapshot_v2_json` (OrderSnapshotV2 JSON)

#### Convert path copies frozen fields verbatim (no live rebuild)

Evidence:

- `backend/services/order_snapshot_v2_convert_service.py`
  - builds `OrderSnapshotV2` from parsed `QuoteSnapshotV2Record.snapshot_json`
  - copies component scope fields without re-running resolvers/builders

---

### ExecutionPlan V2 preview/persist/materialize (consumption without live reconstruction)

#### Preview source contract

Evidence:

- `backend/schemas/execution_plan_v2.py`
  - `ExecutionPlanV2Preview.source = "order_snapshot_v2"`
  - task identity fields include `planned_tasks[].source_module_code`, `.source_component_code`, `.source_operation_code`, `.source_task_rule_code`
  - `IGNORED_PRICING_SOURCES` explicitly excludes pricing sources from task planning inputs

#### Persisted execution plan stores source identity metadata

Evidence:

- `backend/models/execution_plan.py`
  - `source_quote_snapshot_v2_id`
  - `source_snapshot_code`
  - `source_content_hash`
  - `source_order_snapshot_version`

Evidence:

- `backend/services/execution_plan_v2_persist_service.py`
  - `build_tasks_json_envelope(...)` stores identity metadata into `tasks_json` envelope
  - `create_execution_plan_v2_from_order(...)` persists one execution_plan row only

#### Materialization uses persisted envelope, not live reconstruction

Evidence:

- `backend/services/execution_plan_task_parser.py`
  - `materialize_operational_tasks_from_v2_envelope(...)` attaches per-task source identity fields
- `backend/services/execution_plan_v2_materialize_service.py`
  - asserts `planned_tasks[]` are unchanged (mutation guard)
  - does not mutate `orders.snapshot_v2_json`
- `backend/tests/test_execution_plan_v2_materialize.py`
  - covers “planned tasks unchanged” and “snapshot JSON not mutated” invariants

#### “No live reads after freeze” enforcement (guard + tests)

Evidence:

- `backend/services/execution_plan_v2_persist_service.py`
  - `FORBIDDEN_IMPORT_SUBSTRINGS` blocks forbidden dependencies (quote/pricing/cost-engine legacy paths)
- `backend/services/execution_plan_v2_materialize_service.py`
  - `FORBIDDEN_IMPORT_SUBSTRINGS`
- tests:
  - `backend/tests/test_execution_plan_v2_preview.py`
  - `backend/tests/test_execution_plan_v2_persist.py`
  - `backend/tests/test_execution_plan_v2_materialize.py`

---

### Linked-child identity and provenance

Pre-freeze linked-child provenance originates via:

- `ProductAggregateService.build(...)` (reads parent template, dossier, module links, child templates; annotates `source_template_code`/`provenance`)
- frozen into snapshot JSON via Quote Snapshot V2 build and then copied into Order Snapshot V2.

Evidence:

- `backend/services/product_aggregate_service.py`
  - child template mapping includes `TPL-METAL-PREMOUNT-STRUCTURE_v1` and `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
  - materials/operations include `source_template_code` and `provenance`

---

### Risks / bounded behavior

- An explicit legacy alias bridge exists (`resolve_template_identity`) and is permitted only as a **read bridge** with explicit metadata.
- Active compilation/freeze endpoints must reject legacy aliases (HTTP 422).

Evidence:

- `backend/services/template_architecture_scope.py` (bridge)
- `backend/tests/test_product_system_identity_boundary.py` (active-path rejection)

