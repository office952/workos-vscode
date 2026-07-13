# Worklog — PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_STANDALONE_OFFER_FLOW_V1

**Date:** 2026-07-13  
**Template:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`

## Summary

Closed the standalone Product System offer path for boxed ACM mounting. Primary blockers were PD root (no form contract), payload context (linked-child-only ACM detection), catalog role (internal module), and quote snapshot template allowlist.

## Implementation

- Standalone PD preview from aggregate + `structura_suport` module (no Intake form contract)
- Standalone quote_input merges via existing `derive_acm_casetted_quote_input`
- ACM-only commercial/internal rule template entries
- Catalog availability treats `root_offerable` templates as offerable products
- Targeted pytest + vitest + Playwright evidence

## Out of scope

- Intake V6 standalone operator form
- 4 mm thickness pricing
- Metal premount / lighting changes
