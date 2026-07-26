## Research — Identity boundary audit (template codes)

Task: `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_RUNTIME_CLOSEOUT`

Purpose: Audit canonical identity resolution across Product System / ProductDefinition / ProductAggregate / mini-modules / commercial previews / Quote Snapshot V2, with explicit handling for trim normalization, case normalization, legacy read bridge, and alias rejection.

Research mode: read-only analyst (no code changes).

---

## Canonical identity resolver contract (authoritative)

**Resolver + gate** live in `backend/services/template_architecture_scope.py`:

- `normalize_template_code(template_code)`:
  - canonicalization: `strip()` + `upper()`
- `resolve_template_identity(template_code)`:
  - returns metadata:
    - `requested_template_code`
    - `canonical_template_code`
    - `resolution_type`: `canonical` | `legacy_read_bridge` | `rejected_alias`
    - `legacy_alias_used`
    - `resolution_source`
- `require_canonical_template_code(template_code)`:
  - strict gate for “active compilation / write-like flows”
  - returns a `TemplateIdentityResolution` with `resolution_type="rejected_alias"` when legacy alias was used

Known legacy aliases (explicit map): `RUNTIME_TEMPLATE_CODE_BY_ALIAS` includes the focus templates’ legacy forms, mapping to:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`

---

## Where `template_code` is accepted and how it is validated

### Product System compilation-style endpoints (strict gate, reject legacy aliases with 422)

All of the following accept `template_code` via path and enforce `require_canonical_template_code(template_code)`:

- ProductDefinition: `backend/routers/product_system_product_definition.py`
- ProductAggregate: `backend/routers/product_system_aggregate.py`
- Mini-modules by template: `backend/routers/product_system_mini_modules.py`
- Cost BOM preview: `backend/routers/product_system_cost_bom_preview.py`
- Commercial price preview: `backend/routers/commercial_price_proposal.py`
- Estimated internal cost preview: `backend/routers/estimated_internal_cost.py`
- Quote Snapshot V2 preview/freeze: `backend/routers/quote_snapshot_v2.py`

Expected behavior:

- trim normalization and case normalization should be accepted as canonical formatting normalization
- known legacy aliases should be explicitly recognized by `resolve_template_identity` but **rejected** by the strict gate
- unknown aliases should be rejected (see defect note below)
- no silent alias write is permitted on freeze/persist endpoints

### Intake acceptance surface (not governed by Product System identity gate)

`/api/v1/intake-v6/form-contract/{template_code}` in `backend/routers/intake_v6_modular_form.py` does **not** enforce `require_canonical_template_code` and does not normalize/canonicalize template codes.

This is a separate acceptance surface and is a potential source of identity-boundary inconsistency (Product System strict vs Intake contract permissive).

---

## “No silent alias write” audit points

Quote Snapshot V2 persistence:

- `backend/services/quote_snapshot_v2_service.py` persists `template_code` into the snapshot record on freeze.
- Product System `freeze` route is strict-gated, so legacy aliases should not reach persistence through that path.

---

## Tests that cover the identity boundary

- `backend/tests/test_product_system_identity_boundary.py`:
  - resolver behavior for normalization
  - explicit legacy read bridge
  - strict gate rejection on compilation routes (422 envelope includes resolution metadata)
- `backend/tests/test_template_architecture_scope.py`:
  - runtime scope acceptance behavior (alias bridge) and related helpers

---

## High-signal suspected defects / contradictions (requires coordinator decision gate)

### 1) Uppercasing canonical template codes may break DB + registry lookups

Resolver canonicalizes to uppercase (e.g. `TPL-VOLUMETRIC-LETTERS_V2`), while:

- seeds and registry keys use mixed case with lowercase suffixes (e.g. `TPL-VOLUMETRIC-LETTERS_v2`)
- DB lookups for templates and dict lookups for registry indices appear exact-match in several places

Risk: Product System endpoints can become self-inconsistent:

- strict gate accepts normalized uppercase as canonical, but downstream lookups (DB and registry) may fail or return empty because stored keys are mixed-case.

### 2) Unknown alias rejection is not clearly enforced by resolver implementation

If `resolve_template_identity` treats unknown inputs as `canonical` after normalization, it can allow “unknown alias” strings to appear canonical unless a downstream existence check rejects them later.

### 3) Boundary mismatch between scope checks (alias-accepting) and compilation flows (alias-rejecting)

This may be intentional, but any write-like flow must be audited to ensure it uses the strict gate rather than scope-only checks.

---

## Runtime identity matrix schema (for the runtime proof phase)

Recommended capture fields per request:

- `endpoint`
- `requested_template_code_raw`
- `normalized_template_code`
- `canonical_template_code`
- `resolution_type`
- `legacy_alias_used`
- `resolution_source`
- `accepted_by_gate`
- `db_template_lookup_key`, `db_template_found`, `db_template_code_stored`
- `registry_index_lookup_key`, `registry_modules_count`
- `write_intent`, `persisted_template_code`, `silent_alias_write_detected`
- `warnings[]`

---

## Workstream conclusion (for plan gate)

Identity boundary status: **BLOCKED_PENDING_RUNTIME_PROOF**

Rationale:

- The strict gate + envelope tests exist and appear correct, but the casing/lookup contradictions must be proven at runtime (or fixed minimally) before declaring identity isolation PASS.

