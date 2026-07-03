# BUILD-COMMERCIAL-E2E-FIXTURE

**Date:** 2026-06-07  
**Build status:** **PASS** (with BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE follow-up)  
**Prior build:** `c019ddc` — unified commercial runtime spine navigation  

## Summary

Deterministic dev-db fixture and Playwright live-db coverage for the commercial spine on **TPL-VOLUMETRIC-LETTERS**:

`/quotes/QT-E2E-COMMERCIAL-001` → convert → `/orders/{orderCode}` → `/execution/{orderDbId}`.

Quote→order→execution navigation and conversion are automated on live-db. **Follow-up (2026-06-07):** `BUILD-EXECUTION-SNAPSHOT-FROM-VOLUMETRIC-QUOTE` fixes execution snapshot mapping — commercial-live E2E now asserts plan **201**. Production `/price` volumetric gate remains stricter than the fixture overlay.

## Relationship to c019ddc

- Reuses URL routing, auto-selection, and `canMutateQuotes = source === "db"` from c019ddc.
- Adds **mutation** E2E separate from navigation-only `commercial-spine.spec.ts`.
- Does not change CostEngine, status lifecycle, or inventory semantics.

## Fixture strategy

| Property | Value |
|----------|--------|
| Intake code | `WI-E2E-COMMERCIAL-001` |
| Quote code | `QT-E2E-COMMERCIAL-001` |
| Template | `TPL-VOLUMETRIC-LETTERS` |
| Source | DB (`priced`, mutable) |
| Grand total (dev run) | 1256.06 RON (CostEngine real) |
| Idempotency | Re-run deletes orders linked to fixture quote only; re-prices quote |

**Setup command** (from repo root, with dev DB env):

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd backend
.\.venv\Scripts\python.exe scripts\seed_commercial_e2e_fixture.py
```

Writes manifest: `frontend/e2e/.commercial-fixture.json` (gitignored).

**Readiness (updated 2026-06-07):** `BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE` removed the E2E overlay. Fixture now persists **live** `readiness_result` + `quote_gate`; `live_gate_can_create_commercial_quote: true` for deterministic input. Warnings remain visible; acknowledgement only when unsatisfied warnings exist.

**WI-SMOKE-P001:** Untouched — separate intake; not used as commercial-chain fixture.

## Files changed

| File | Change |
|------|--------|
| `backend/scripts/seed_commercial_e2e_fixture.py` | New deterministic fixture seed |
| `frontend/e2e/helpers/commercialFixture.ts` | Live-db probe + manifest |
| `frontend/e2e/commercial-chain-live.spec.ts` | Mutation E2E spec |
| `frontend/e2e/commercial-spine.spec.ts` | Unchanged (navigation only) |
| `frontend/src/pages/Quotes.tsx` | `quote-readiness-state`, `quote-accept-action`, `quote-convert-action` test IDs |
| `frontend/src/pages/Orders.tsx` | `order-detail-selected` test ID |
| `frontend/src/pages/ExecutionDetail.tsx` | `execution-plan-generate-action` test ID |
| `frontend/package.json` | `test:e2e:commercial-live` script |
| `.gitignore` | Ignore `.commercial-fixture.json` |

## E2E flow automated

1. Probe backend `/health` + fixture quote `QT-E2E-COMMERCIAL-001` — skip with message if missing.
2. `/quotes/:quoteId` — Live DB badge, no not-found/terminal banners, priced readiness visible.
3. Convert via UI (`quote-convert-action`) — real `POST /orders/from-quote/{id}`.
4. `/orders/:orderId` — auto-select, `order-detail-selected`.
5. `/execution/:order_id` (numeric db id) — page loads.
6. Plan generate click — **201** with tasks (fixed in `BUILD-EXECUTION-SNAPSHOT-FROM-VOLUMETRIC-QUOTE`).

**Not automated in this build:**

- Send → accept UI path (send opens `QuoteSendDialog` without status transition; priced→convert is the supported fast lane).
- Reality start-end smoke (deferred).
- FigJam board update (Figma MCP not invoked this session).

**Follow-up doc:** `docs/qa/BUILD_EXECUTION_SNAPSHOT_FROM_VOLUMETRIC_QUOTE.md`

## Test commands and results

```text
# Unit / route
npm run test -- --run src/lib/commercialSpineNavigation.test.ts src/pages/Quotes.route.test.tsx
→ 8 passed

# Lint
npm run lint
→ pass

# Playwright navigation (no fixture required for 2/3 tests)
PW_SKIP_WEB_SERVER=1 npm run test:e2e
→ 4 tests: 3 passed, 1 skipped (before fixture) OR 4 passed after fixture seeded

# Playwright commercial mutation (requires seed + backend + frontend)
# After seed:
PW_SKIP_WEB_SERVER=1 npm run test:e2e:commercial-live
→ 1 passed (2026-06-07 local dev.db)
```

## PASS / PARTIAL / FAIL checklist

| Item | Status |
|------|--------|
| `/quotes` URL tests | PASS |
| `/orders` URL behavior | PASS |
| Deterministic fixture | PASS |
| DB source, not mock | PASS |
| Quote detail by URL | PASS |
| Readiness/priced asserted | PASS |
| Real conversion | PASS |
| Order detail by URL | PASS |
| Execution detail opens | PASS |
| Plan generation 201 | PASS (follow-up build) — see BUILD_EXECUTION_SNAPSHOT_FROM_VOLUMETRIC_QUOTE |
| Reality smoke | DEFERRED — needs canonical locked snapshot |
| canMutateQuotes preserved | PASS |
| TPL-VOLUMETRIC-LETTERS scope | PASS |
| QA doc | PASS |

## Risks and gaps

1. **Live `/price` gate** still blocks new volumetric commercial quotes without fixture overlay — product policy, not bypassed in runtime.
2. **Fixture readiness overlay** is test-only; operators must not treat it as production readiness truth.
3. **Execution plan contract** — fixed in BUILD-EXECUTION-SNAPSHOT-FROM-VOLUMETRIC-QUOTE; formula ops may still have zero-minute tasks until costing emits durations.
4. **CI** without dev DB + seed will skip commercial-live (honest skip, not false PASS).

## Suggested next substantial build

**BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE** — resolve live `/price` `needs_review` without E2E readiness overlay, or document owner acceptance policy.
