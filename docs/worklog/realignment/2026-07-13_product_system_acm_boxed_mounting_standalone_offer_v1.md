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

## Runtime QA closeout (2026-07-13)

### Initial closeout (backend/API)

- Cleared orphaned `:8000` listeners; single fresh backend via `scripts/dev-backend.ps1`
- Backend pytest: **16 passed** (standalone offer + owner rates/cpp)
- Frontend vitest: **15 passed** (`acmQuoteInput`, `mountingSolution`)
- Live API: ACM `quote_offerable=true`, `product_system_role=offerable_product` after cleanup
- Playwright spec: **2 attempts FAIL** (stale backend on attempt 1; auth/URL on attempt 2)
- Evidence: `docs/qa/product-system-acm-boxed-mounting-standalone-offer-v1/evidence_report.json`
- No application code edits in closeout pass

### Playwright auth/baseURL closeout (PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_STANDALONE_PLAYWRIGHT_AUTH_BASEURL_CLOSEOUT_V1)

**HEAD before:** `15cc291`

Preflight (no restart — healthy stack):

- `:3000` listening (PID 4300)
- `:8000` listening (PID 12012)
- Live API gate: ACM `quote_offerable=true`, `product_system_role=offerable_product`, `display_group=active_products`

Spec-only fixes (`frontend/e2e/product-system-acm-boxed-mounting-standalone-offer-v1.spec.ts`):

| Concern | Before | After |
|---------|--------|-------|
| baseURL | hardcoded `http://127.0.0.1:3000/product-system` | relative `page.goto("/product-system")` via `PW_BASE_URL ?? http://localhost:3000` |
| origin | `127.0.0.1` | `localhost` only |
| auth | none | `page.addInitScript` → `sessionStorage WORKOS_DEV_GUARD_BYPASS=1` |
| openapi fetch | `127.0.0.1:8000` | `PW_BACKEND_URL ?? http://localhost:8000` |
| bucket | assumed expanded | `expandBucketIfNeeded` from readonly-smoke |
| detail assertion | `/Suport ACM casetat/i` (not in UI) | family name + template code + offerable label |

Validation:

| Gate | Result |
|------|--------|
| Backend pytest (standalone + owner rates) | **16 passed** |
| Frontend vitest (`acmQuoteInput`, `mountingSolution`) | **15 passed** |
| Playwright attempt 1 | **FAIL** — detail panel shows family name, not product label |
| Playwright attempt 2 | **PASS** — 3 screenshots, verdict PASS |

Evidence metadata updated: `base_url`, `origin`, `auth_method`, `playwright_attempts`, `backend_url`.

No application code edits.
