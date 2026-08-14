# Route inventory refresh — 2026-08-13

| Field | Value |
|-------|--------|
| Source | [`frontend/src/App.tsx`](../../../frontend/src/App.tsx) |
| Prior baseline | [`docs/qa/workos-full-route-uiux-baseline-v1/route-inventory.md`](../workos-full-route-uiux-baseline-v1/route-inventory.md) (2026-08-02, 79 Route elements, 38 captured) |
| This count | **85** `<Route>` elements in `App.tsx` |
| Wave 1 audited | AppShell chrome + `/dashboard` + `/quotes` + `/shop-floor` only |
| Other routes | Inventoried, **not** audited |

This file is an inventory. It does **not** make a route “audited”.

## 1. Counts

| Metric | 2026-08-02 | 2026-08-13 |
|--------|-----------:|-----------:|
| `<Route>` elements in `App.tsx` | 79 | **85** |
| Named `path=` routes (approx.) | 78 | 69 + nested PS + standalone |
| Standalone app roots | 3 | 3 (`employee-app`, `employee-app-v2`, `intake-v6-app`) |
| Redirect-only aliases | 10 | 10 |
| Unique U1∪U2 captures | 38 | — (stale) |

Delta vs baseline is growth in Product System nested structure routes and machine-run / intake-v6 paths. Recount from current `App.tsx`, not from the 2026-08-02 JSON.

## 2. Canonical role homes (U7, still in code)

| Role | Home | Nav label |
|------|------|-----------|
| admin | `/dashboard` | Control producție |
| viewer | `/dashboard` | Control producție |
| sales | `/quotes` | Oferte |
| operator | `/shop-floor` | Atelier |
| manager | `/shop-floor` | Atelier |

Source: `getRoleHomePath` in [`frontend/src/lib/shellNavigation.ts`](../../../frontend/src/lib/shellNavigation.ts).

## 3. Named routes (operator-relevant)

### Shell / homes

| Path | Component | Wave 1 |
|------|-----------|--------|
| `/` | `RoleHomeRedirect` | Follow only |
| `/dashboard` | `Dashboard` | **Full traverse** |
| `/shop-floor` | `ShopFloor` | **Full traverse** |
| `/quotes` | `Quotes` | **Full traverse** |

### Intake

| Path | Component |
|------|-----------|
| `/intake` | `WorkIntake` |
| `/intake/:id` | `IntakeLegacyRoute` |
| `/intake-v6/operator` | `IntakeV6OperatorWorkspaceApp` |
| `/intake-v6/:workspaceId/operator` | `IntakeV6OperatorWorkspaceApp` |
| `/intake-v6-app/*` | standalone dark shell |

### Commercial

| Path | Component |
|------|-----------|
| `/quotes/:quoteId` | `Quotes` |
| `/orders` · `/orders/:orderId` | `Orders` |
| `/clients` · `/clients/:clientName` | `Clients` / `ClientWorkspace` |
| `/documents` | `DocumentCenter` |

### Production

| Path | Component |
|------|-----------|
| `/operator` | `OperatorView` (compat) |
| `/tablet` · `/tablet/:stationId` · `/tablet/:stationId/:taskId` | Tablet |
| `/execution` | `ExecutionDashboard` |
| `/execution/:order_id` | `ExecutionDetail` |
| `/execution/ops-graph` | `MaterializedOpsGraph` |
| `/execution/reality-review` | `OperationalRealityReview` |
| `/execution/machine-runs` · `/:machineRunId` | Machine runs |

### Product System (nested under `/product-system`)

`products`, `products/:templateCode`, six named structure steps + `:stepId`, planned sections (`components`…`advanced`), plus `/product-system/blueprint-dossier` and `/product-system/output-blocks-preview`.

### Registries / people / admin

`/inventory`, `/inventory/pricing`, `/utilaje`, `/colaboratori`, `/employees`, `/employees-records`, `/employees-records/:employeeId`, `/attendance`, `/attendance/effects`, `/employee-payments`, `/employee-advances`, `/reports`, `/reports/operational`, `/modules`, `/governance`, `/settings`.

### Demos / standalone / auth / redirects

Demos: `/demo/commercial-spine`, `/demo/volumetric-letter-preview`.  
Standalone: `/employee-app/*`, `/employee-app-v2/*`.  
Auth: `/auth/callback`, `/auth/error`, `/auth/logout`, `/logout-callback`.  
Redirects: `/pricing`, `/products`, `/templates`, `/personal`, three `/inventory/*` aliases, `/product-system/dossier-completion`.

## 4. Sidebar IA (not the same as route table)

See `SHELL_NAV_SECTIONS` in `shellNavigation.ts`. Wave 1 follows each **visible** item per role. Destination pages are not fully audited in Wave 1.

Wave 4 audited (read-only): `/product-system/products` (+ Letters v2, ACM boxed), planned `components`/`operations`, `/product-system/blueprint-dossier`, `/product-system/output-blocks-preview`, `/modules`, `/governance`. See [`wave-4/WAVE_4_REPORT.md`](./wave-4/WAVE_4_REPORT.md).

Wave 5 audited (read-only): `/employees`, `/attendance`, `/employees-records`, `/employees-records/:employeeId` (row `<button>` + deep-link `/employees-records/7`), `/employee-payments`, `/employee-advances`, `/utilaje`, `/inventory`, `/inventory/pricing`, `/settings`, `/documents`, `/colaboratori`, `/reports`, `/reports/operational`. See [`wave-5/WAVE_5_REPORT.md`](./wave-5/WAVE_5_REPORT.md) · [`wave-5/WAVE_5_GAP_CLOSURE_REPORT.md`](./wave-5/WAVE_5_GAP_CLOSURE_REPORT.md).
