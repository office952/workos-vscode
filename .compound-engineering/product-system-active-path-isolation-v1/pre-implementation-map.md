## Pre-implementation map — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### Record (isolation + safety)

- **Original workspace path**: `C:\\Users\\offic\\workos_app_vs`
- **Original workspace dirty state preserved**: YES (no reset/stash/stage/delete performed)
- **Isolated worktree path**: `C:\\w\\psiso`
- **Base commit**: `82a713e`
- **Branch**: `feature/product-system-active-path-isolation-v1`

### Current canonical identity boundary (as-is)

Primary alias/normalization utility currently used in backend:
- `backend/services/template_architecture_scope.py`
  - `normalize_template_code(template_code) -> upper/trim`
  - `resolve_runtime_template_code(template_code) -> alias map (silent) + upper`
  - `template_matches_runtime_scope(template_code, allowed_runtime_codes) -> resolve_runtime_template_code + membership`

Observed behavior:
- **Canonical** codes pass through unchanged (aside from upper/trim).
- **Legacy aliases** can silently resolve via `RUNTIME_TEMPLATE_CODE_BY_ALIAS` (no provenance surfaced).
- **Unknown alias** silently falls back to normalized input (not rejected).

### Active alias layers (known from direct reads)

- **Layer A (runtime alias map)**:
  - File: `backend/services/template_architecture_scope.py`
  - Data: `RUNTIME_TEMPLATE_CODE_BY_ALIAS`

- **Layer B (active template scope)**:
  - File: `backend/services/active_template_scope.py` (imported by availability service; not yet inspected in this phase)
  - Used for owner validity / normalization in Product System availability.

### Active write / compilation request paths (initial inventory)

These accept `template_code` and build runtime artifacts (preview/compile). Identity must be canonicalized deterministically here:

- **Template availability (catalog input)**:
  - `backend/services/product_template_availability_service.py` (reads `Product_templates.template_code` from DB; uses `template_matches_runtime_scope` for “experimental” vs owner-valid classification)
  - Writes: none (read-only), but **feeds UI truth** and **readiness/capabilities**.

- **Product readiness/capabilities (derived truth)**:
  - `backend/services/product_system_template_readiness_service.py`
  - Uses `template_usage_mode_policy.normalize_template_code` internally (separate normalization layer).

- **Product Aggregate (read-only builder)**:
  - `backend/services/product_aggregate_service.py` → `ProductAggregateService.build(template_code)`
  - Loads template + dossier + links; read-only but is a **compiler-like** authoritative aggregator.

- **Product Definition preview (read-only builder)**:
  - `backend/services/product_definition_builder_service.py` (build_preview accepts `template_code`)
  - Uses aggregate builder and workspace payload, plus linked-template segment extraction.

Additional active write-like consumers to inspect next (not yet mapped in this phase):
- Quote Snapshot V2 preview/freeze
- Quote pricing orchestration (`/entities/quotes/price`)
- Intake V6 quote-to-order
- Execution plan generation

### Historical read paths (initial)

- Legacy alias resolution appears designed for compatibility across naming variants (e.g. `TPL-VOLUMETRIC-LETTERS` → `TPL-VOLUMETRIC-LETTERS_v2`).
- No explicit “legacy bridge” metadata is exposed today (silent).

### Dossier write paths (as-is, initial)

- CRUD router: `backend/routers/product_blueprint_dossier.py`
  - Auth required for all routes (`Depends(get_current_user)`)
  - Permission system exists (`require_permission` imported), but write routes must be inspected to ensure operator cannot write.
- CRUD service: `backend/services/product_blueprint_dossier_service.py` (not yet read in this phase)

Critical constraint:
- Dossier is consumed by active paths (aggregate + readiness), so dossier writes can influence runtime truth even if the CRUD layer claims “does not calculate cost”.

### Proposed files for change (candidate set — subject to analyst results)

Backend (identity boundary):
- `backend/services/template_architecture_scope.py` (or a consolidation point that replaces/extends it)
- Active consumers: `backend/services/product_template_availability_service.py`, `backend/services/product_aggregate_service.py`, `backend/services/product_definition_builder_service.py`, snapshot-v2 services/routers (to be confirmed)

Backend (dossier hardening):
- `backend/routers/product_blueprint_dossier.py`
- `backend/services/product_blueprint_dossier_service.py`

Tests:
- backend pytest: new targeted tests near `services/template_architecture_scope` and dossier router/service.
- frontend tests (vitest/playwright) only if UI/operator behavior changes are required to meet “operator cannot write dossier”.

### Explicitly NOT changing (scope boundary)

- Intake V6 feature code (anything under `frontend/src/components/workos/intake-v6/` and backend intake_v6 services) unless it directly violates identity boundary rules.
- Pricing formulas, pricing registry data, rates, or any migrations/seeds.
- Product Detail redesign and catalog redesign.
- Dev stack scripts.

### Rollback boundary

All implementation changes are isolated to:
- one feature branch `feature/product-system-active-path-isolation-v1`
- one worktree `C:\\w\\psiso`

Original workspace remains dirty and untouched by git operations beyond read-only inspection.

