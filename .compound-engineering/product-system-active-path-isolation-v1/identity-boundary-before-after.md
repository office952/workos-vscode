## Identity boundary — before/after

### Before (82a713e)

Primary boundary:
- `services/template_architecture_scope.resolve_runtime_template_code(...)`
  - Harmless normalization: trim + uppercase
  - **Silent** alias resolution via `RUNTIME_TEMPLATE_CODE_BY_ALIAS`
  - Unknown alias falls back to normalized input (not rejected, no provenance)

Observed impact:
- Active compilation endpoints did not enforce canonical template identity; behavior depended on exact DB codes or downstream lookups.
- No explicit metadata existed to trace requested → canonical identity at the boundary.

### After (PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1)

Canonical boundary (single):
- `services/template_architecture_scope.resolve_template_identity(...)` returns explicit metadata:
  - `requested_template_code`
  - `canonical_template_code`
  - `resolution_type`: `canonical | legacy_read_bridge | rejected_alias`
  - `legacy_alias_used`
  - `resolution_source`

Strict active compilation gate:
- `services/template_architecture_scope.require_canonical_template_code(...)`
  - Allows harmless formatting normalization (trim/case)
  - Rejects legacy alias resolution for active compilation/write-like flows

Enforcement points (active compilation routes now reject legacy aliases with HTTP 422):
- `GET /api/v1/product-system/aggregate/{template_code}`
- `GET /api/v1/product-system/product-definition/{template_code}`
- `GET /api/v1/product-system/cost-bom-preview/{template_code}`
- `POST /api/v1/product-system/commercial-price-preview/{template_code}`
- `POST /api/v1/product-system/estimated-internal-cost-preview/{template_code}`
- `GET /api/v1/product-system/mini-modules/by-template/{template_code}`
- `POST /api/v1/product-system/quote-snapshot-v2/preview/{template_code}`
- `POST /api/v1/product-system/quote-snapshot-v2/freeze/{template_code}`

Traceability:
- ProductDefinition preview adds a `provenance[]` entry `key=template_identity` with requested/canonical/type/source.
- ProductAggregate adds bounded `warnings[]` entries indicating template identity trace and dossier consumption.

