# BUILD — Orders Execution CTA Live Source Guard Fix

**Status:** PASS (code + tests + read-only smoke)  
**Date:** 2026-06-12  
**Routes:** `/orders`, `/orders/:orderId`, `/execution/:orderDbId`

## 1. Problem

Pe order detail live (`ORD-1781201059-1`), CTA **„Vezi Execuția”** rămânea disabled cu mesajul:

> Navigarea către Execuție este disponibilă doar pe sursă backend live.

Deși:

- order există în DB (id `1`)
- execution plan generat (11 taskuri)
- `/execution/1` funcționează direct
- Operator / Tablet văd taskuri live

## 2. Root cause

`Orders.tsx` folosea guard agregat:

```ts
source === "db"
```

Când quotes/intakes/materials sunt `db` dar alte entități diferă (sau mix), `useBackendData().source` devine **`mixed`**, deși `sourcesDetail.orders === "db"`.

Efecte secundare:

- `executionApi.getObservability` nu era apelat (`source !== "db"` → plan state rămâne `null`)
- panoul „Taskuri producție” ascuns
- CTA-uri execution disabled + warning fals

Același pattern ca bug-ul Quotes (fixat în `30b0918`).

## 3. Fix applied

### `frontend/src/pages/Orders.tsx`

```ts
const ordersSource = sourcesDetail?.orders ?? source;
const canUseLiveOrders = ordersSource === "db";
```

Înlocuit `source === "db"` / `source !== "db"` pentru acțiuni orders/execution cu `canUseLiveOrders`.

- Observability fetch: `canUseLiveOrders`
- Panou generate plan / open execution
- CTA „Vezi Execuția” (`data-testid="order-view-execution-cta"`)
- NextStepPanel actions (confirm / generate / open execution)
- FieldInstallationTeamPanel guard

Badge-ul paginii rămâne pe sursa agregată (diagnostic). Warning execution doar când `!canUseLiveOrders`.

## 4. Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/Orders.tsx` | Per-entity orders source guard |
| `frontend/src/pages/Orders.executionCta.test.tsx` | **New** — mixed aggregate + orders db |
| `frontend/src/pages/Orders.executionDispatch.test.tsx` | `sourcesDetail` în mock |
| `docs/qa/BUILD_ORDERS_EXECUTION_CTA_LIVE_SOURCE_GUARD_FIX.md` | Acest doc |

## 5. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/Orders.executionCta.test.tsx `
  src/pages/Orders.executionDispatch.test.tsx `
  src/pages/Orders.empty.test.tsx
# 3 files, 9 passed
```

## 6. Runtime smoke (read-only, DB controlat)

**Stare DB folosită:**

- Order id: `1`
- Order code: `ORD-1781201059-1`
- Source quote: `QT-E2E-COMMERCIAL-001`
- Execution tasks: **11** (fără mutații noi)

| Route | Verificare |
|-------|------------|
| `/orders` | Order listat |
| `/orders/ORD-1781201059-1` | Plan existent; „Vezi Execuția” enabled; fără warning fals |
| `/execution/1` | 11 taskuri |
| `/operator` | Taskuri live |
| `/tablet/asamblare_lipire` | Taskuri live (T-009) |

**Nu apăsat:** convert, generate plan, start/assign/complete task.

## 7. Boundaries confirmed

- No DB changes
- No new orders / execution tasks
- No seed / migrations / schema
- No backend changes
- No Quotes / Operator / Tablet / Employee Payments changes (except shared pattern)

## 8. Remaining gaps (out of scope)

- Tablet flash demo pre-auth
- Quote component breakdown — fixed in `33b8ef0`
- UX: grouping execution CTAs duplicate („Vezi Execuția” + „Deschide execuția”)
