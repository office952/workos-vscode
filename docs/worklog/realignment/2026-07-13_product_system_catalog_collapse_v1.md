# Product System Catalog Collapse V1 — Worklog

**Date:** 2026-07-13  
**Task:** PRODUCT_SYSTEM_CATALOG_COLLAPSE_V1  
**Base HEAD:** b94ec48

## Agents / roles

| Role | Agent |
|------|-------|
| Read-only analysts | Catalog data, Figma 7:6, visibility, readiness UX, search/filter, legacy bucket, test, runtime QA (conversation synthesis) |
| Implementation owner | Single agent (canonical model + catalog UI + ProductSystem mount) |
| Integration owner | Same agent (Vitest, Playwright, evidence, commit) |

## Canonical catalog contract

- Single operator list driven by `capabilities` + `readiness` on `ProductTemplateAvailabilityItem`
- Operator scope gated by `OWNER_VALID_ACTIVE_TEMPLATE_CODES` when readiness fields absent
- Advanced section for internal/deprecated/experimental parents (`view:governance`)

## Files changed

- `frontend/src/features/product-system/productSystemCanonicalCatalogModel.ts` (new)
- `frontend/src/features/product-system/ProductSystemCanonicalCatalog.tsx` (new)
- `frontend/src/features/product-system/productSystemCanonicalCatalog.test.ts` (new)
- `frontend/src/pages/ProductSystem.tsx` (mount canonical catalog)
- `frontend/e2e/product-system-catalog-collapse-v1.spec.ts` (new)
- `docs/qa/product-system-catalog-collapse-v1/*`

## Tests

- Vitest: `productSystemCanonicalCatalog.test.ts` — 8 passed
- Playwright: `product-system-catalog-collapse-v1.spec.ts` — 1 passed

## Runtime

- Backend :8000, frontend :3000 (dev auth admin)
- Operator catalog: letters + ACM; logo/component-first/archived buckets absent
- Advanced list: premount + logo separated

## Verdict

**PASS_WITH_LEGACY_BUCKET_API_DEBT** — unified bucket builder retained for detail-panel compatibility; readiness fields null on live API during QA (UI fallback used).

## Next safe slice

Product Detail Overview + readiness breakdown (not lateral bucket cleanup).
