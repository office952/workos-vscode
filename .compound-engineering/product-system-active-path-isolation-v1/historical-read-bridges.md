## Historical read bridges (retained)

### Bridge: runtime template alias resolution

- Location: `services/template_architecture_scope.py`
- Mechanism: `RUNTIME_TEMPLATE_CODE_BY_ALIAS` + `resolve_runtime_template_code(...)`
- Purpose: accept historical aliases (e.g. `TPL-VOLUMETRIC-LETTERS`) and resolve to canonical runtime codes.

### Policy (after this slice)

- **Allowed**: read-only compatibility utilities and explicit migration-style reads where the caller surfaces canonicalization results.
- **Forbidden**: active compilation/write-like flows silently accepting aliases.

### Active compilation enforcement

The following endpoints now reject legacy aliases with HTTP 422 and return explicit canonicalization metadata:
- Product Aggregate
- Product Definition preview
- Cost BOM preview
- CPP preview
- EIC preview
- Quote Snapshot V2 preview/freeze
- Mini-module registry by-template

