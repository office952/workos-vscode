# BUILD — ShopFloor Source Badge Pilot (Label Parity Cleanup)

## Status

**Implementation: EXECUTED** — `ShopFloor.tsx` only.

## Purpose

Replace local `DataSourceBadge` in `ShopFloor.tsx` with design-system `SourceBadge`, using owner-approved canonical labels for the restricted secondary-source pilot.

## Owner label decision (this build)

| State | Canonical label | DS `source` key |
|-------|-----------------|-----------------|
| live / db | Live DB | `db` |
| empty (live backend, no rows) | Live DB (gol) | `empty` |
| error | Source Error | `error` |
| loading | Loading | `loading` |
| mock / demo fallback | Demo | `demo` (presentation map from hook `mock`) |

Hook `source` derivation in `useShopFloorData` is unchanged. Only badge presentation maps `mock` → `demo` for canonical Demo label without DS token edits.

## Audit — ShopFloor.tsx (pre-edit)

### Local states

`useShopFloorData` exposes: `db` | `mock` | `empty` | `error` | `loading`.

### Labels before

| State | Local label | Tone |
|-------|-------------|------|
| `db` | Live DB | emerald |
| `empty` | **Empty** | slate (non-canonical) |
| `error` | Source Error | red |
| `mock` | Mock Data | amber |
| `loading` | hidden (`return null`) | — |

### Semantic check — `empty`

From `useShopFloorData.ts` lines 239–245:

- API responds OK; machines list length is 0; mock disabled.
- Sets `source: "empty"`, clears arrays, `error: null`, `connectionStatus: "connected"`.

**Conclusion:** `empty` = live backend reachable, no operational data. **Not** a disconnected/error state.

### Warnings / guards unaffected

- Amber banner for `(source === "empty" || source === "error")` unchanged.
- Red error banner for `error && source !== "mock"` unchanged.
- `runtimeAlerts = source === "mock" ? productionAlerts : alerts` unchanged.

## Verdict

**CLEAN NOW** — owner approved canonical empty label; error already aligned; mock mapped to Demo at presentation layer only.

## Scope

### In scope

- `frontend/src/pages/ShopFloor.tsx` — DS `SourceBadge` adoption
- `frontend/src/pages/ShopFloor.badges.test.tsx` — minimal badge coverage
- This QA doc

### Out of scope (boundaries)

- Colaboratori, Personal, Utilaje (deferred)
- Quotes, Work Intake, Pricing, ProductSystem, Tablet, Payments, Execution
- No backend / DB / API / business logic changes
- No App shell / `index.css` / `tailwind.config`
- No design-system token changes
- No status lifecycle / warning hiding

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/ShopFloor.tsx` | Remove local `DataSourceBadge`; add `mapShopFloorSourceToBadge`; render `SourceBadge` |
| `frontend/src/pages/ShopFloor.badges.test.tsx` | **New** — badge mapping + live/empty/error/mock fixtures |
| `docs/qa/BUILD_WORKOS_SHOPFLOOR_SOURCE_BADGE_PILOT.md` | **New** — this record |

## Dead code removed

- Local `DataSourceBadge` function (~35 lines)
- Unused `Database` icon import from `lucide-react`

## Tests

Commands:

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/ShopFloor.badges.test.tsx
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

Results:

| Suite | Result |
|-------|--------|
| `SourceBadge.test.tsx` | 8 passed |
| `StatusBadge.test.tsx` | 36 passed |
| `ShopFloor.badges.test.tsx` | 5 passed |
| **Total** | **49 passed** |

`tsc -b --noEmit`: **FAIL** — pre-existing repo TS debt (unrelated files: `QuoteCommercialActionPanel.badges.test.tsx`, `EmployeePayments.tsx`, `Pricing.badges.test.tsx`). No new errors in `ShopFloor.tsx` / `ShopFloor.badges.test.tsx`.

## Runtime smoke

Route: `/shop-floor` — read-only load.

Checks:

- Page loads
- Source badge shows canonical label for current fixture
- Empty/error warning banners remain visible when applicable
- No console errors

Result: **PASS** (read-only, `http://127.0.0.1:3000/shop-floor`)

| Check | Result |
|-------|--------|
| Page loads | ✅ |
| Source badge | ✅ `Live DB` (`data-source="db"`, emerald tone) |
| Warning banners | ✅ none on live-db fixture (expected) |
| Console errors | ✅ none observed via CDP snapshot |

## Deferred modules

| Module | Blocker |
|--------|---------|
| `Colaboratori.tsx` | `empty`/`error` → `"No Data"` |
| `Personal.tsx` | same |
| `Utilaje.tsx` | `empty`/`error` → `"No Data"`; local fn shadows DS |

## Recommended commit message

```text
feat(design-system): consolidate ShopFloor source badge
```

## Next step

After manual commit-tree: owner may approve same canonical labels for Utilaje, then Colaboratori/Personal.
