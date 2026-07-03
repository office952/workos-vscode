# BUILD — Quotes Live Source Guard Fix

**Status:** PASS (code + tests + read-only smoke)  
**Date:** 2026-06-12  
**Route:** `/quotes`, `/quotes/:quoteId`

## 1. Problem

E2E audit Work Intake → Quote → Order → Execuție found:

- DB: 4 quotes (all `priced`), 0 orders — valid live-empty orders state
- Backend: convert endpoint exists (`POST /api/v1/entities/orders/from-quote/{id}`)
- UI: quote detail showed live data but **all commercial actions disabled** with:
  *„Acțiunile comerciale sunt blocate: necesită contract backend live.”*

## 2. Root cause

`Quotes.tsx` used aggregate `useBackendData().source`:

```ts
const canMutateQuotes = source === "db";
```

When quotes/intakes load from DB but **orders list is empty**, `deriveAggregateSource` returns **`mixed`** (`db` + `empty`). Quotes are live, but `canMutateQuotes` was false.

`WorkIntake.tsx` already used per-entity source: `sourcesDetail.intakes`.

## 3. Fix applied

### `frontend/src/pages/Quotes.tsx`

```ts
const { source, sourcesDetail, ... } = useBackendData();
const quotesSource = sourcesDetail?.quotes ?? source;
const canMutateQuotes = quotesSource === "db";
```

### UX (Fix 3 minimal)

`NextStepPanel` for `priced` status — description mentions convert from Acțiuni section.

## 4. Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/Quotes.tsx` | Per-entity quotes source guard + priced NextStep text |
| `frontend/src/pages/Quotes.liveSourceGuard.test.tsx` | New tests: mixed aggregate + quotes db |
| `docs/qa/BUILD_QUOTES_LIVE_SOURCE_GUARD_FIX.md` | This doc |

## 5. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/Quotes.liveSourceGuard.test.tsx `
  src/pages/Quotes.readiness.test.tsx `
  src/pages/Quotes.commercialActions.test.tsx
# 3 files, 13 passed
```

## 6. Runtime smoke (read-only)

`/quotes/QT-E2E-COMMERCIAL-001`:

- Status `priced`
- Commercial document OK
- „Creează comandă din oferta activă” **enabled** (not blocked by live-contract message)
- No „necesită contract backend live” when `sourcesDetail.quotes === db`
- **Convert not clicked** — no DB mutation

## 7. Boundaries confirmed

- No DB changes
- No seed
- No schema/migrations
- No backend changes
- No Orders / Employee Payments / Commercial document / ProductSystem changes

## 8. Optional follow-ups (out of scope)

| Item | Notes |
|------|-------|
| Orders empty CTA listing convertible priced quotes | Fix 2 |
| Accept button on `priced` | Fix 4 — backend allows `priced→accepted` |
| E2E convert → order → execution plan | Requires owner-approved DB mutation smoke |
