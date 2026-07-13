## Final report — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### Verdict

**FAIL_RUNTIME**

Reason: runtime verification and UI screenshot evidence could not be produced due to a **port 8000 ghost listener** that prevented starting the backend for this slice on required ports `8000/3000`.

### Original workspace state

- Path: `C:\\Users\\offic\\workos_app_vs`
- Dirty state preserved: **YES** (no reset/stash/stage/delete)

### Isolated worktree/branch

- Worktree: `C:\\w\\psiso`
- Base HEAD: `82a713e`
- Branch: `feature/product-system-active-path-isolation-v1`
- Worktree was clean at creation: **YES**

### Multitasking report

Read-only analysts were launched (identity / dossier / snapshot-execution / tests). Runtime work proceeded without parallel dev servers or parallel Playwright runs.

### Canonical identity boundary (before)

- Silent alias map: `services/template_architecture_scope.resolve_runtime_template_code(...)`

### Canonical identity boundary (after)

- Explicit resolution contract:
  - `services/template_architecture_scope.resolve_template_identity(...)`
  - `services/template_architecture_scope.require_canonical_template_code(...)`
- Active compilation routes reject legacy aliases with HTTP 422 and return explicit canonicalization metadata.

See: `.compound-engineering/product-system-active-path-isolation-v1/identity-boundary-before-after.md`

### Alias layers removed from active path

- Legacy alias resolution is no longer accepted by Product System compilation endpoints.
- Historical bridge retained only as explicit read bridge.

See: `.compound-engineering/product-system-active-path-isolation-v1/alias-callsite-inventory.md`

### Dossier role before/after

- Backend already enforced dossier writes via `dossier.create/update/delete` permissions (admin/manager only).
- This slice added **traceability** to aggregate output when dossier is consumed, but did not fully de-authoritize dossier for canonical templates.

See: `.compound-engineering/product-system-active-path-isolation-v1/dossier-write-path-before-after.md`

### Premount + ACM capability truth

- ACM policy already correct.
- Premount policy was incorrect (component-only); corrected via code policy (no DB migration).

See: `.compound-engineering/product-system-active-path-isolation-v1/premount-acm-capability-truth.md`

### Tests

Targeted pytest:
- `backend/tests/test_template_architecture_scope.py` (updated)
- `backend/tests/test_product_system_identity_boundary.py` (new)

Result: **PASS (8 tests)**

### Runtime verification

Blocked. See: `.compound-engineering/product-system-active-path-isolation-v1/runtime-verification.md`

### Files changed (worktree)

Backend:
- `backend/services/template_architecture_scope.py`
- `backend/services/template_usage_mode_policy.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/routers/product_system_aggregate.py`
- `backend/routers/product_system_product_definition.py`
- `backend/routers/product_system_cost_bom_preview.py`
- `backend/routers/product_system_mini_modules.py`
- `backend/routers/commercial_price_proposal.py`
- `backend/routers/estimated_internal_cost.py`
- `backend/routers/quote_snapshot_v2.py`

Tests:
- `backend/tests/test_template_architecture_scope.py`
- `backend/tests/test_product_system_identity_boundary.py`

Docs/artifacts:
- `.compound-engineering/product-system-active-path-isolation-v1/*`

### Remaining debt

- Complete runtime verification + screenshots once port 8000 is freed.\n- Consider next slice to **version-pin or de-authoritize dossier** for canonical templates to fully satisfy “dossier cannot act as parallel truth”.

