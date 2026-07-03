# BUILD — Unified Commercial Runtime Spine

**Status:** PASS (navigation + URL spine; full quote→order→execution E2E partial by backend policy)  
**Branch:** `master`  
**Target template:** `TPL-VOLUMETRIC-LETTERS` (unchanged; unsupported templates remain on fallback)

## Summary

Unified commercial navigation so runtime objects are addressable by URL and traceable from Client → Intake → Quote → Order → Execution. No CostEngine, pricing, status lifecycle, or schema changes.

## Routes changed

| Route | Behavior |
|-------|----------|
| `/quotes` | List + wizard (unchanged) |
| `/quotes/:quoteId` | **New** — auto-selects quote; refresh preserves selection |
| `/orders` | List (unchanged) |
| `/orders/:orderId` | **New** — auto-selects order; refresh preserves selection |
| `/execution/:order_id` | Unchanged (already deep-linkable) |

## Files changed

- `frontend/src/App.tsx` — parameterized quote/order routes
- `frontend/src/lib/commercialSpineNavigation.ts` — shared nav state + URL helpers
- `frontend/src/lib/commercialSpineNavigation.test.ts`
- `frontend/src/pages/Quotes.tsx` — URL selection, not-found, terminal UI, order deep-link on convert
- `frontend/src/pages/Orders.tsx` — URL selection, not-found
- `frontend/src/pages/IntakeDetail.tsx` — shared wizard nav state helper
- `frontend/src/pages/WorkIntake.tsx` — draft quote → `/quotes/:quoteId`
- `frontend/src/pages/ClientWorkspace.tsx` — deep links for quote/order/execution
- `frontend/src/pages/Quotes.route.test.tsx`
- `frontend/playwright.config.ts`
- `frontend/e2e/commercial-spine.spec.ts`
- `frontend/package.json` — `test:e2e` script

## Navigation changes

| Source | Before | After |
|--------|--------|-------|
| WorkIntake draft quote | `/quotes` (blind) | `/quotes/{quote_code}` |
| IntakeDetail preliminary | `/quotes` + rich state | Same state via `buildQuoteWizardNavStateFromIntake` |
| ClientWorkspace quotes | `/quotes` | `/quotes/{id}` |
| ClientWorkspace orders | `/orders` | `/orders/{id}` |
| Quote convert → order | `/orders` | `/orders/{order_code}` |
| Recent activity | list roots | entity-specific paths |

## Quote URL behavior

- `useParams().quoteId` drives selection after data load
- Unknown ID → `quote-not-found` banner (non-blocking)
- Card click syncs URL via `replace: true`
- Wizard close returns to `/quotes/{id}` when a quote was selected

## Terminal quote UI policy

- `rejected` / `expired` → `quote-terminal-policy` panel + NextStepPanel
- Mutating actions hidden (send, accept, reject, convert, resend)
- `accepted` unchanged — convert still available
- `canMutateQuotes = source === "db"` **preserved**

## WorkIntake / IntakeDetail state

- **IntakeDetail:** `navigateToQuotesList` + `buildQuoteWizardNavStateFromIntake` (full prefill: productSpec, siteAudit, template, delivery)
- **WorkIntake:** Backend `POST /from-intake/{id}` returns `quote_code`; navigates to detail URL. Wizard prefill not duplicated (draft is backend-created entity).

## ClientWorkspace deep links

- Overview, Cereri, Oferte, Comenzi tabs use `quoteDetailPath`, `orderDetailPath`, `executionDetailPath`
- No fake IDs — links only when entity `id` exists

## Mock mode / E2E

- `canMutateQuotes` guard retained for mock/demo safety
- Vitest: route selection, terminal policy, navigation helpers
- Playwright (`npm run test:e2e`): **3/3 passed**
  - Direct quote URL + refresh
  - Unknown quote not-found
  - WI-SMOKE-P001 embedded volumetric quote panel
- Full quote→order→execution chain **not** automated end-to-end (requires writable backend + accepted quote fixture); documented as remaining gap

## FigJam board

Not updated — Figma MCP plugin not invoked in this build session.

## Remaining gaps

1. Full E2E: accept quote → convert → execution plan/reality (needs dedicated test fixture + live-db write path)
2. WorkIntake could offer volumetric wizard handoff in addition to backend draft (out of scope — draft path uses quote ID)
3. Orders list secondary actions still use generic `/orders` in a few non-ClientWorkspace surfaces (Dashboard — intentional list entry)

## PASS checklist

- [x] `/quotes` works
- [x] `/quotes/:quoteId` works
- [x] Refresh on `/quotes/:quoteId` preserves selected quote
- [x] WorkIntake navigates to specific quote after draft creation
- [x] IntakeDetail rich QuoteWizard state preserved
- [x] ClientWorkspace deep-links quote/order/execution
- [x] Terminal quotes show explicit UI policy
- [x] TPL-VOLUMETRIC-LETTERS path unchanged
- [x] Unsupported templates unchanged
- [x] Readiness guards intact
- [x] `canMutateQuotes` not removed
- [x] Tests added
- [x] No CostEngine/status/inventory regression

## Test commands

```bash
cd frontend
npm run test -- src/lib/commercialSpineNavigation.test.ts src/pages/Quotes.route.test.tsx src/pages/Quotes.visibility.test.tsx
npm run lint
npm run test:e2e   # requires :3000 + :8000 live DB
```
