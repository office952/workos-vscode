## Alias / normalization callsite inventory

### Canonical boundary (after change)

- `services/template_architecture_scope.resolve_template_identity(...)`
- `services/template_architecture_scope.require_canonical_template_code(...)`

### Legacy alias map (still present, but no longer allowed for active compilation)

- `services/template_architecture_scope.RUNTIME_TEMPLATE_CODE_BY_ALIAS`
- `services/template_architecture_scope.resolve_runtime_template_code(...)`

### Active consumers of legacy alias resolution (remaining)

As of this slice, `resolve_runtime_template_code(...)` is still referenced by:
- `backend/services/intake_v6_pilot_contract_seed.py` (seed/compat utility; not an active Product System compilation endpoint)
- Tests that validate legacy alias mapping behavior:
  - `backend/tests/test_template_architecture_scope.py`
  - `backend/tests/test_intake_v6_assembly_preview.py` (logo alias checks)

### Active compilation endpoints now using canonical-only identity

These routers now reject legacy alias inputs and require canonical codes:
- `backend/routers/product_system_aggregate.py`
- `backend/routers/product_system_product_definition.py`
- `backend/routers/product_system_cost_bom_preview.py`
- `backend/routers/commercial_price_proposal.py`
- `backend/routers/estimated_internal_cost.py`
- `backend/routers/product_system_mini_modules.py`
- `backend/routers/quote_snapshot_v2.py`

