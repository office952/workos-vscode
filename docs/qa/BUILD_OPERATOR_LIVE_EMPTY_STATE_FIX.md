# BUILD — Operator Live Empty State Fix

**Status:** PASS (code + tests + `/operator` smoke)  
**Date:** 2026-06-11  
**Route:** `/operator`

## 1. Problem

Final Operational Live Smoke failed only on `/operator`:

- Banner **MOCK DATA** and text *„Butoanele sunt dezactivate — nu există conexiune la backend”*
- Meanwhile `GET /api/v1/operator/tasks` → **200**, `tasks: []`
- `useOperatorData` correctly returned `source: "empty"` for API OK + zero tasks
- Tablet had already been fixed in `da57fe7` to treat `empty` as live; OperatorView lagged behind

## 2. Root cause

`OperatorView.tsx` wired UI only when `source === "db"`:

```ts
const isWired = source === "db";
```

Successful empty API (`source: "empty"`) was treated like mock/unwired:

- `!isWired` showed the amber MOCK DATA banner
- Registry / action wiring logic excluded live-empty
- `DataSourceBadge` already had a separate `empty` branch, but banner used `!isWired`

**Not** a backend or DB issue — frontend condition only.

## 3. Fix applied

### `frontend/src/pages/OperatorView.tsx`

| Change | Detail |
|--------|--------|
| `isWired` | `source === "db" \|\| source === "empty"` |
| `isMockSource` | `source === "mock"` — explicit mock fallback only |
| MOCK banner | `isMockSource` instead of `!isWired` |
| Action footnote | „conectați backend-ul” only for `isMockSource` |
| Badge `empty` | **Live DB (gol)** (emerald), aligned with tablet |

Empty hint unchanged (already correct):

*„Nu aveți task-uri asignate momentan. Verificați cu supervizorul sau așteptați alocarea unui task din planul de execuție.”*

Start/Pause/Complete stay disabled when no active task — reason is missing task, not mock/no backend.

### `frontend/src/pages/OperatorView.live.test.tsx` (new)

Covers: `empty` (no mock banner, no disconnect text, live badge + hint), `mock` (alert banner), `db` (Live DB + registry).

## 4. Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/OperatorView.tsx` | Live-empty wiring |
| `frontend/src/pages/OperatorView.live.test.tsx` | Unit tests |
| `docs/qa/BUILD_OPERATOR_LIVE_EMPTY_STATE_FIX.md` | This doc |

## 5. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/OperatorView.live.test.tsx `
  src/pages/OperatorView.eligibility.test.tsx `
  src/hooks/useOperatorData.live.test.ts `
  src/hooks/useTabletStationData.test.ts `
  src/pages/TabletMode.live.test.tsx
# 5 files, 14 passed
```

Employee Payments / Orders / Commercial document tests not re-run (out of scope; no code touched).

## 6. Runtime smoke

**API:** `GET /api/v1/operator/tasks` → `{"tasks":[],"total":0}` (backend :8000)

**`/operator` (frontend :3000):**

- No MOCK DATA banner
- No „nu există conexiune la backend”
- Registry section visible (live wired)
- Empty state: „Niciun task activ”, no mock task names
- No mock task list entries

**`/tablet/asamblare_lipire`:** Vitest regression green; manual re-check recommended after hard refresh if browser showed transient demo during load (demo flash while `operatorSource === "loading"` is pre-existing; stable live-empty state documented in `BUILD_ATELIER_TABLET_LIVE_SOURCE_RECOVERY.md`).

**Regression quick:**

- `/employee-payments` — OK (live roster, paid_total 800 RON, Andrei 500, Vali 300)
- `/orders` — empty / loading state OK (0 orders in DB)
- Commercial document — not touched

## 7. Boundaries confirmed

- No DB changes
- No seed
- No schema/migration changes
- No backend changes
- No TabletMode / useTabletStationData changes (unless future regression)
- No Employee Payments / Orders / Commercial document code changes
- No global CSS / App shell changes
- No commit in this build

## 8. Relation to tablet fix (`da57fe7`)

| Surface | `empty` handling |
|---------|------------------|
| `useOperatorData` | Returns `source: "empty"` on 200 + `tasks: []` |
| `useTabletStationData` | `isLive` for `db` and `empty` (da57fe7) |
| `OperatorView` | **This build** — `isWired` for `db` and `empty` |
