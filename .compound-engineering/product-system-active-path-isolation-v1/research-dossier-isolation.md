## Research — Dossier authority and write-path audit

Task: `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_RUNTIME_CLOSEOUT`

Research verdict: **UNSAFE_PARALLEL_TRUTH**

---

### Scope & question

Determine whether Dossier is merely an Advanced/Admin technical view or remains a parallel source of product truth.

This research is strictly read-only and based on active code inspection.

---

## Where is Dossier persisted?

- **DB table**: `product_blueprint_dossier`
- **ORM model**: `backend/models/product_blueprint_dossier.py` → `ProductBlueprintDossier`
  - FK `template_id` → `product_templates.id` (`ondelete="RESTRICT"`)
  - `template_id` is **unique** (one dossier per template)
- **Migration**: `backend/alembic/versions/s23_product_blueprint_dossier_hardening.py`

---

## Who can write? Who can read?

### Write (backend enforced)

Write routes are permission-gated:

- `backend/routers/product_blueprint_dossier.py`
  - `POST /api/v1/entities/product-blueprint-dossiers` → `require_permission("dossier.create")`
  - `PUT /api/v1/entities/product-blueprint-dossiers/{id}` → `require_permission("dossier.update")`
  - `DELETE /api/v1/entities/product-blueprint-dossiers/{id}` → `require_permission("dossier.delete")`

Permission matrix:

- `backend/dependencies/permissions.py` → `PERMISSION_MATRIX`
  - `dossier.create/update/delete`: **admin, manager only**

### Read (broad)

Read routes require auth (`Depends(get_current_user)`) but do **not** call `require_permission(...)`:

- `GET /api/v1/entities/product-blueprint-dossiers`
- `GET /api/v1/entities/product-blueprint-dossiers/by-template/{template_id}`
- `GET /api/v1/entities/product-blueprint-dossiers/{id}`

Implication:

- **Any authenticated user** can read dossiers (subject to auth admission), while only admin/manager can write.

---

## What backend check prevents operator writes?

Primary enforcement:

- `backend/dependencies/permissions.py` → `require_permission(...)` + `PERMISSION_MATRIX` excludes operator from `dossier.*` writes.

Secondary enforcement (service-side “owner” rule):

- `backend/services/product_blueprint_dossier_service.py` → `check_owner_permission(...)`
  - If `owner_role` is set, only that role (or admin) can write.
  - **Permissive fallback** if role is missing in auth context (`user_role` falsy): enforcement is skipped.

Operator write prevention relies on the router-level permission gate.

---

## Is Dossier consumed by ProductDefinition?

**Yes, indirectly**.

Evidence:

- `backend/services/product_definition_builder_service.py` calls `ProductAggregateService.build(...)`
- `backend/services/product_aggregate_service.py` consumes dossier JSON (see next section)

So any ProductDefinition preview that uses the aggregate inherits dossier-derived structure/contract elements.

---

## Is Dossier consumed by ProductAggregate?

**Yes, directly** (multiple dossier fields become aggregate structure and contracts).

Evidence:

- `backend/services/product_aggregate_service.py` → `ProductAggregateService.build(...)`
  - loads dossier via `_load_dossier(template.id)`
  - consumes:
    - `sections_json` → `_build_dossier_components(...)` → **aggregate.components provenance="dossier"**
    - `costengine_mapping_json` → adds `material_keys` / `operation_keys` as **mapping_only** aggregate rows
    - `inputs.required/optional` → aggregate `form_contract`
    - `task_rules_json` → `_build_task_contract(...)` → aggregate task contract rules (`provenance="dossier"`)

High-signal “parallel truth” indicator:

- When parent template has no direct components, aggregate warns it is using dossier + linked modules as authoritative structure:
  - code: `PARENT_COMPONENTS_EMPTY` warning in `backend/services/product_aggregate_service.py`

---

## Can Dossier alter components/materials/operations/formulas/dependencies/task rules?

- **Components**: **Yes** (aggregate components derived from dossier `sections_json`).
- **Materials**: **Partially** (dossier can contribute `mapping_only` materials via `costengine_mapping_json.material_keys`).
- **Operations**: **Partially** (dossier can contribute `mapping_only` operations via `costengine_mapping_json.operation_keys`).
- **Task rules**: **Yes** (aggregate task contract derived from dossier `task_rules_json`).
- **Formulas / dependencies**: no direct evidence dossier rewrites formula execution or dependency graphs, but dossier-derived task rules and mappings influence “truth builders” upstream of snapshotting.

---

## Can Dossier bypass canonical Product Template/component contracts?

**Yes, in the aggregate read model**:

- Aggregate can contain components sourced from dossier even when `product_templates.components_json` is empty, which bypasses “template row is sole structure source” for downstream consumers using the aggregate.

Evidence:

- `backend/services/product_aggregate_service.py` (`PARENT_COMPONENTS_EMPTY` + dossier component build)

---

## Is Dossier consumed live after snapshot freeze?

### Execution (post-freeze)

No evidence execution plan v2 preview/persist/materialize re-read live dossier after freeze; they consume frozen snapshot payloads.

Evidence pointers:

- `backend/services/execution_plan_v2_preview_service.py` (snapshot-driven)
- `backend/services/execution_plan_v2_persist_service.py` / `..._materialize_service.py` (envelope-driven; forbidden import guards)

### Quote output preview

Live preview can read dossier output blocks, but saved snapshots persist rendered output.

Evidence pointers:

- `backend/services/output_blocks_renderer_service.py` (render preview reads dossier output blocks)
- `backend/services/quote_output_snapshot_service.py` (persists rendered snapshot, references source dossier id)

---

## Can Dossier independently influence pricing?

No direct evidence dossier is a cost-engine/pricing input that computes totals; however it can influence **readiness gating** and downstream flows.

Evidence:

- `backend/services/product_readiness_service.py` → `ProductReadinessService.evaluate(...)`
  - quote readiness requires dossier presence and dossier lifecycle status (must be approved for `ready_for_quote`)

So dossier can be a **workflow gate** even if not an arithmetic price source.

---

## Explicit answers checklist

- **Where is Dossier persisted?** `product_blueprint_dossier` (`backend/models/product_blueprint_dossier.py` + alembic `s23_...`).
- **Who can write?** admin/manager via backend permission gating (`backend/dependencies/permissions.py`).
- **Who can read?** any authenticated user (reads are not permission-gated).
- **What backend check prevents operator writes?** router dependencies `require_permission("dossier.*")` and RBAC matrix excluding operator.
- **Does ProductDefinition consume it?** yes indirectly via `ProductAggregateService`.
- **Does ProductAggregate consume it?** yes directly (components, mapping keys, form contract, task contract).
- **Can it alter components/materials/operations/formulas/dependencies/task rules?**
  - components: yes
  - materials/operations: mapping-only signals yes
  - task rules: yes
  - formulas/dependencies: no direct evidence of direct rewrite, but dossier shapes “truth builders”.
- **Can it bypass canonical Product Template/component contracts?** yes in aggregate view when parent components are empty.
- **Is it consumed live after snapshot freeze?** execution flows appear snapshot-only post-freeze; quote output preview can read live dossier for preview.
- **Can it independently influence pricing?** not as direct price calculator; yes as readiness/gating authority.

---

## Workstream A supplemental findings (2026-07-13)

### Additional runtime consumption surfaces (parallel truth amplification)

- **Intake option contract**: dossier `variants_json` is consumed to produce template option contract allowed-values, without consistent `status == approved` gating.
  - Evidence:
    - `backend/services/intake_v6_template_option_contract_service.py`
    - `backend/services/intake_v4_template_option_contract_service.py` (including finish validation helpers)
- **Quote output composition / preview**: dossier `output_blocks_json` is used to render client-facing output blocks for preview/composition.
  - Evidence:
    - `backend/services/output_blocks_renderer_service.py`
    - `backend/services/quote_output_composition_service.py`
- **Aggregate → BOM → pricing-structure influence**: aggregate pricing context preparation builds the aggregate (which consumes dossier), meaning dossier can influence what is priced (structure/mapping), even if it is not a direct rate source.
  - Evidence:
    - `backend/services/aggregate_cost_bom_price_bridge.py`
    - `backend/services/quote_orchestrator.py` (imports aggregate-price-context utilities)

### Required conclusion (closeout gate)

Research verdict remains: **UNSAFE_PARALLEL_TRUTH**.

Rationale:

- Dossier is not only an Advanced/Admin technical view; it is actively consumed as an input to:
  - ProductAggregate structure + task contract
  - Intake option contract allowed-values
  - Quote output block composition/preview
- These consumers do not consistently enforce **approved-only** consumption, so unapproved dossier content can shape runtime behavior.

### Minimal backend enforcement direction (plan input; no code here)

- Introduce a single **DossierConsumptionPolicy** (or equivalent helper) that returns `(is_allowed, reason)` based on:
  - `dossier.status` (approved-only for behavior-bearing fields)
  - template canonical identity match (template_code consistency)
  - caller surface (aggregate vs intake-contract vs output-blocks)
- Apply the policy consistently in:
  - `ProductAggregateService` dossier consumption
  - Intake option contract services dossier consumption
  - Output blocks renderer / quote output composition dossier consumption (for client-facing surfaces)

