# Worklog — Product System Scope and Deep-Link Alignment V1

**Date:** 2026-07-13  
**Task:** PRODUCT_SYSTEM_SCOPE_DEEPLINK_ALIGNMENT_V1  
**HEAD before:** 9219610  
**Verdict:** PASS

## Multitasking

| Role | Outcome |
|------|---------|
| Scope contract analyst | FE scope aligned to BE ROOT_OFFERABLE (letters + ACM) |
| Deep-link routing analyst | Single owner: ProductSystem URL + UnifiedCatalog selection |
| Intake link analyst | IntakeV6ReviewStep links verified; no Intake code change needed |
| Test analyst | Vitest + Playwright + backend parity test |
| Runtime QA planner | 4-screenshot flow executed |
| Implementation owner | Code changes below |
| Integration owner | Playwright pass, evidence, commit |

## State ownership before

| Concern | Owner | Problem |
|---------|-------|---------|
| URL `?template=` | None | Ignored |
| Catalog selection | `ProductSystemUnifiedCatalog.selectedEntryId` | Default letters override |
| FE owner-valid scope | `activeTemplateScope.ts` | Letters only |

## Root cause

`ProductSystemUnifiedCatalog` useEffect auto-selected `TPL-VOLUMETRIC-LETTERS_v2` when `selectedEntryId` was null. Without URL parsing, ACM deep links appeared to open a panel but showed letters.

## Files touched

- `frontend/src/lib/activeTemplateScope.ts` — ACM in OWNER_VALID; BE parity helper
- `frontend/src/features/product-system/productSystemTemplateQuerySync.ts` — query resolution (new)
- `frontend/src/features/product-system/ProductSystemUnifiedCatalog.tsx` — query sync + unavailable UI
- `frontend/src/pages/ProductSystem.tsx` — useSearchParams bridge
- Tests: activeTemplateScope, productSystemNavigation, e2e spec, backend parity

## Commands

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/activeTemplateScope.test.ts src/features/product-system/productSystemNavigation.test.ts
$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/product-system-scope-deeplink-alignment-v1.spec.ts
cd ..\backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_template_availability.py::test_root_offerable_policy_includes_acm_excludes_logo -q
```

## Remaining (not this slice)

- Catalog bucket visibility collapse (Slice 2)
- Readiness API dimensions (Slice 1B)
- Compoziție/Componente tab merge

## Cat sunt in directia stabilita

**92/100%**
