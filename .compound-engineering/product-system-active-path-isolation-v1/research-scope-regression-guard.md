## Research — Scope and regression guard audit

Task: `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_RUNTIME_CLOSEOUT`

Purpose: Identify unrelated files, protected-area risks (Intake V3/V6, pricing, DB, migrations, tooling), duplicate/stale Compound artifacts, and the expected minimal test surface.

Research mode: read-only (no file changes).

---

## Current git state (authoritative, captured live)

Modified:

- `.compound-engineering/product-system-active-path-isolation-v1/decision-log.md`
- `.compound-engineering/product-system-active-path-isolation-v1/risk-register.md`
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-verification.md`
- `docs/worklog/realignment/2026-07-13_product_system_active_path_isolation_v1.md`

Untracked (expected closeout artifacts + evidence bundles):

- `.compound-engineering/product-system-active-path-isolation-v1/compound-knowledge.md`
- `.compound-engineering/product-system-active-path-isolation-v1/plan.md`
- `.compound-engineering/product-system-active-path-isolation-v1/research-dossier-isolation.md`
- `.compound-engineering/product-system-active-path-isolation-v1/research-runtime-surface-map.md`
- `.compound-engineering/product-system-active-path-isolation-v1/research-snapshot-execution-identity.md`
- `.compound-engineering/product-system-active-path-isolation-v1/review-findings.md`
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-attempt-analysis.md`
- `.compound-engineering/product-system-active-path-isolation-v1/runtime-root-cause-review.md`
- `.compound-engineering/windows-ghost-listener-8000-clear-v1/`

No backend/router/service/test modifications are present **at this stage**.

---

## Primary scope risks (must remain untouched)

- **Pricing / CostEngine**: any move from “preview/read-only” into authoritative pricing, pricing rules, or rate registries.
- **DB schema / alembic**: avoid any changes under `backend/alembic/**` unless explicitly authorized (hard forbidden here).
- **Seeds / scripts**: avoid changes under `backend/scripts/**` and any seed/migration coupling.
- **Intake V3 / Intake V6**: do not modify; also ensure runtime gating does not require missing Intake V3 routes unless explicitly intended.
- **Dev-stack tooling**: treat `scripts/*.ps1` as read-only unless runtime root cause proves a tooling defect and an explicit decision-log approval is recorded.

---

## Unrelated/noisy artifacts (do not commit)

Do not commit local DB or runtime logs:

- `backend/dev.db`
- `backend/logs/**`

---

## Minimal allowed file-scope (for later implementation owner)

Default allowed change set (only if proven necessary by plan gates):

- Product System routers: `backend/routers/product_system_*.py`
- Quote Snapshot V2 router/service strictly for identity/freeze correctness: `backend/routers/quote_snapshot_v2.py`, `backend/services/quote_snapshot_v2_service.py`
- Identity scope: `backend/services/template_architecture_scope.py`
- Usage mode / capability truth: `backend/services/template_usage_mode_policy.py`
- Aggregate/definition builders: `backend/services/product_aggregate_service.py`, `backend/services/product_definition_builder_service.py`
- Dossier consumption enforcement (if required): the specific consuming services only (not CRUD router)
- Targeted tests only in `backend/tests/` directly tied to changes (see below)

Explicitly disallow for this closeout:

- `backend/alembic/**`
- `backend/scripts/**`
- `backend/dev.db`, `backend/logs/**`
- Intake V3 / V6 routers/services (unless a proven bug requires a minimal enforcement fix and is explicitly approved)
- Any pricing registry / rates / commercial pricing rules

---

## Targeted test surface (for the later dedicated test owner)

Required base commands (owner-specified):

- `C:\\Users\\offic\\workos_app_vs\\backend\\.venv\\Scripts\\python.exe -m pytest tests/test_template_architecture_scope.py tests/test_product_system_identity_boundary.py -q`

Likely next-most-related (only if changes touch these areas):

- Quote Snapshot V2: `backend/tests/test_quote_snapshot_v2.py`
- OrderSnapshotV2 convert: `backend/tests/test_order_snapshot_v2_convert.py` (or nearest equivalent)
- ExecutionPlan V2: `backend/tests/test_execution_plan_v2_preview.py`, `backend/tests/test_execution_plan_v2_persist.py`, `backend/tests/test_execution_plan_v2_materialize.py`
- Dossier consumption boundary tests (to be added if enforcement changes are made)

---

## Workstream conclusion (for plan gate)

Scope guard status: **OK_TO_PROCEED_TO_PLANNING_SYNTHESIS**.

Note: implementation must remain minimal and proven; do not absorb unrelated local artifacts (DB/logs) into the closeout commit.

