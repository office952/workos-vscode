# Wave 3 — action surface classification (current truth)

No Owner design decision. Current shipped truth only.

## Atelier `/shop-floor`

**ATELIER_ROLE = CANONICAL_MONITOR_HOME**

| Signal | Evidence |
|--------|----------|
| Nav | `CANONICAL_PRODUCTION_HOME = "/shop-floor"`; U7 operator/manager home |
| Copy | “Intrare canonică producție — monitorizare”; next-step: “Atelierul este monitorizare” |
| CTAs | **Acțiune task** → `/operator`; **Stații** → `/tablet` |
| Mutations | none on machine cards |
| Poll | `useShopFloorData` 10 s — watch, not act |

Not CANONICAL_ACTION_HOME (cannot start). Not HYBRID_HOME (actions are explicitly off-page). TRANSITIONAL is a future-reading; present governance already names it the canonical monitor.

## `/operator`

**OPERATOR_ROUTE_ROLE = COMPAT_ACTIVE**

| Signal | Evidence |
|--------|----------|
| Nav | label “Acțiune task (legacy)”; `status: "compat"` |
| Runtime | live `GET /operator/tasks` + `POST /operator/task-action` |
| Flow helper | `operatorCompatibilityHint` — “Compatibilitate Operator / Tablet” |
| RBAC | `view:operator` + `action:task_*` for operator/manager/admin |

Not ACTION_CANONICAL (Atelier is the named home). Not dead. Specialized only in the sense that it is the **compat action** surface.

## `/tablet`

**TABLET_ROUTE_ROLE = COMPAT_ACTIVE**

| Signal | Evidence |
|--------|----------|
| Nav | “Stații (legacy)”; `status: "compat"` |
| Routes | `/tablet`, `/tablet/:stationId`, `/tablet/:stationId/:taskId` — implemented |
| Data | same operator-task API via `useTabletStationData` / `tabletLiveBridge` |
| Gap-closure | `/tablet/print` **REACHABLE**: live “T06 Claim Probe” / `ORD-92400` / Putaru; queue visible |
| UX shape | station grid + queue (specialized presentation on a compat route) |

`SPECIALIZED_STATION` describes the layout. Governance/nav class is **COMPAT_ACTIVE**.

## `/employee-app-v2`

**EMPLOYEE_APP_ACTION_SURFACE = SPECIALIZED_EMPLOYEE_UI**

| Signal | Evidence |
|--------|----------|
| Shell | **not** in `shellNavigation` |
| Route | standalone `/employee-app-v2/*` (`EmployeeMobileV2StandaloneRoot`) |
| Actions | own start / claim / helper-session bars (`EmployeeMobileV2WorkRoomActionBar`) |
| vs `/employee-app` | older standalone sibling; v2 is the observed mobile surface |

Not ACTION_CANONICAL. Not a shell COMPAT chip. Duplicate **capability** vs operator/tablet start, different **audience** (employee phone).

## Ops-Graph / Reality Review (role only)

| Surface | Class | Assignment mutation? |
|---------|-------|----------------------|
| `/execution/ops-graph` | **AUDIT_ONLY** | **YES** — controlled assign picker (`assignExecutionPlanTask`). **Not clicked.** |
| `/execution/reality-review` | **AUDIT_ONLY** | NO |

Neither is an operator action home.

## Summary

```text
watch  = /shop-floor          CANONICAL_MONITOR_HOME
plan   = /execution           ACTIVE (not this gap)
act    = /operator            COMPAT_ACTIVE
act    = /tablet              COMPAT_ACTIVE (station-scoped)
act    = /employee-app-v2     SPECIALIZED_EMPLOYEE_UI (hidden from shell)
audit  = ops-graph, reality   AUDIT_ONLY (ops-graph can assign)
```
