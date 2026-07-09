# Product System Playwright Readonly Smoke V1

**Date:** 2026-07-09  
**HEAD before:** `62d6449` — Clarify Product System operator-facing guard labels  
**Task:** PRODUCT_SYSTEM_PLAYWRIGHT_READONLY_SMOKE_V1  
**Scope:** E2E test-only (no UI/backend/DB changes)

## Playwright setup found

| Item | Path / command |
|---|---|
| Config | `frontend/playwright.config.ts` |
| Test dir | `frontend/e2e/` |
| Spec added | `frontend/e2e/product-system-readonly-smoke.spec.ts` |
| Run (stack live) | `PW_SKIP_WEB_SERVER=1 PW_BASE_URL=http://127.0.0.1:3000 npx playwright test e2e/product-system-readonly-smoke.spec.ts` |

## Spec assertions

1. `/product-system` loads unified catalog without crash
2. Lifecycle buckets present (active, candidate, component-first, legacy; archived if rendered)
3. **TPL-VOLUMETRIC-LETTERS_v2** — active root, used today, offerable, Work Intake yes
4. **TPL-VOLUMETRIC-LOGO_v1** — candidate, not Work Intake, owner GO; no dangerous CTAs
5. **TPL-LETTERS-COMPOSER_v1** — readonly component-first, 0/7 live rows, dossier contract 7/7, six TPL-COMP-* rows
6. Guards — blocked exposure labels; no `WI=true` / `Pricing=true` / `PD=true`
7. Legacy modules collapsed by default; TPL-VOLUMETRIC-FACE_v1 labeled legacy; no TPL-COMP-* in catalog list
8. Global absence of activate/promote/create quote / seed / write Product Truth buttons

## Test results

```powershell
cd frontend
$env:PW_SKIP_WEB_SERVER='1'
$env:PW_BASE_URL='http://127.0.0.1:3000'
npx playwright test e2e/product-system-readonly-smoke.spec.ts

npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

- Playwright: **1/1 passed**
- Unit: **100/100 passed**

## Screenshots (generated during spec)

`docs/qa/product-system-playwright-readonly-smoke-v1/screenshots/`

## Boundaries

- No backend, seed, migration, activation, or Product System UI changes (selectors use existing testIds only).

## Residual gaps

- Does not cover 100-product / 600-module scale or archived bucket when empty
- Does not assert Blueprint Studio editor paths opened via row actions
- Requires live stack (:3000 + :8000) for real catalog data
