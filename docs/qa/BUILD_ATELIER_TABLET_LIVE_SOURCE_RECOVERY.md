# BUILD — Atelier Tablet Live Source Recovery

**Status:** PASS (code + tests + UI smoke)  
**Date:** 2026-06-11  
**Route:** `/tablet/asamblare_lipire`

## 1. Problem observed

After fresh `dev.db` + reseed, Atelier Tablet showed:

- Badge **Demo fallback** (amber)
- Text: *Fallback demo — operatori fictivi, non-canonic*
- Fictional operators: Ion Popescu, Mihai Ionescu, etc.
- Demo queue task: *Asamblare finală totem*

Meanwhile backend was healthy (`GET /api/v1/operator/tasks` → 200, 0 tasks) and Operational Registry returned 8 real employees.

## 2. Root cause

**Frontend wiring bug — not missing DB seed for operators.**

| Layer | Finding |
|-------|---------|
| `useOperatorData` | On successful API with `tasks: []`, if `VITE_ENABLE_MOCK_DATA=true`, substituted `mockOperatorTasks` and set `source: "mock"` |
| `useTabletStationData` | `isLive` only when `operatorSource === "db"` — ignored successful empty live response (`source: "empty"`) |
| `TabletMode` | `source: "empty"` fell through `TabletSourceBadge` to **Demo fallback**; `!isLive` rendered `DEMO_OPERATORS` from `workstationRouting.ts` |

**DB state (read-only audit):**

| Entity | Count | Notes |
|--------|-------|-------|
| `asamblare_lipire` station | ✅ | Frontend routing + `STATION_WORKCENTER_CODES` → `WC_ASSEMBLY` |
| Real employees | 8 | Registry API active |
| WC_ASSEMBLY authorizations | 4 | Putaru, Vali, Costi, Andrei (ids 4–7) |
| Orders | 0 | No execution pipeline |
| `execution_plan` | 0 | No live queue tasks (expected empty queue) |

**Strategy:** **Option B** — live API existed; frontend incorrectly fell back to demo on empty success.

No new execution-task seed (no orders). Empty queue + real station operators is the correct live state.

## 3. Fix applied

### `useOperatorData.ts`

- Successful API with zero tasks → `source: "empty"`, `tasks: []`
- Mock substitution **only** on API failure when `VITE_ENABLE_MOCK_DATA=true`

### `useTabletStationData.ts`

- `isLive` when `operatorSource === "db" || operatorSource === "empty"`
- `source: "empty"` when live API has no tasks for station (not `"demo"`)
- Filter `registryEmployees` by station workcenters when no task context (e.g. `WC_ASSEMBLY` for `asamblare_lipire`)

### `TabletMode.tsx`

- Badge **Live DB (gol)** for `source === "empty"` (not Demo fallback)
- Live + registry OK + zero station operators → explicit empty message
- `DEMO_OPERATORS` only when `!isLive` (explicit mock/error dev path)

## 4. Files changed

| File | Change |
|------|--------|
| `frontend/src/hooks/useOperatorData.ts` | Empty live API ≠ mock |
| `frontend/src/hooks/useTabletStationData.ts` | Live empty + station operator filter |
| `frontend/src/pages/TabletMode.tsx` | Badge + operator empty states |
| `frontend/src/hooks/useTabletStationData.test.ts` | Empty live test |
| `frontend/src/hooks/useOperatorData.live.test.ts` | No mock on empty API |
| `frontend/src/pages/TabletMode.live.test.tsx` | asamblare_lipire empty live smoke |
| `docs/qa/BUILD_ATELIER_TABLET_LIVE_SOURCE_RECOVERY.md` | This doc |

## 5. Tests

```powershell
cd frontend
npx pnpm@8.10.0 exec vitest run src/hooks/useTabletStationData.test.ts src/hooks/useOperatorData.live.test.ts src/pages/TabletMode.live.test.tsx
# 10 passed

cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_quote_commercial_document.py tests/test_employee_payments_live.py -q
# 48 passed
```

## 6. Runtime smoke

`/tablet/asamblare_lipire` after fix:

- Badge: **Live DB (gol)** — not Demo fallback
- Operators: Putaru Sandu, Vali Colantator, Costi Modelator, Andrei Goghi (WC_ASSEMBLY)
- No Ion Popescu / fictional roster
- Queue: *Nu există taskuri în coadă pentru această stație*

## 7. Boundaries confirmed

- No schema/migration changes
- No DB restore / bulk seed
- No CostEngine / pricing / ProductSystem changes
- No Employee Payments / Orders / Commercial document code changes
- No hardcoded fake operators on live path
- Demo data remains in `workstationRouting.ts` for explicit non-live dev only

## 8. Remaining notes

- Live **tasks** require orders + execution plans — empty queue is correct until production orders exist
- Optional future build: canonical execution fixture for tablet E2E (not in scope here)
