# Worklog — Product System Readiness API Truth V1

**Task:** `PRODUCT_SYSTEM_READINESS_API_TRUTH_V1`  
**HEAD before:** `5c6b4e4`  
**Verdict:** `PASS_WITH_LEGACY_STATUS_DEBT`

## Summary

Added canonical `readiness` + `capabilities` objects to `GET /api/v1/product-system/template-availability` via `ProductSystemTemplateReadinessService`.

## Derivation

- **Technical:** composition/link integrity, inactive state, JSON contract validity
- **Pricing:** material + operation rates from Pricing Registry truth (no EIC/internal cost)
- **Execution:** operations + dossier task rules for offerable roots
- **Commercial:** `template_usage_mode_policy` + existing `quote_offerable` (not frontend allowlists)
- **Rollup:** deterministic READY / BLOCKED / INTERNAL / DEPRECATED / PARTIALLY_READY (linked-child bounded only)

## Legacy debt

Existing fields (`status`, `status_reason`, `readiness_reason`, etc.) preserved for current consumers.

## Tests

- 21 backend pytest (readiness + availability regression)
- 2 frontend contract vitest
- Shell Playwright smoke pass

## Next

**PRODUCT_SYSTEM_CATALOG_COLLAPSE_V1** — single catalog on real readiness metadata.
