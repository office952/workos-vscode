# BUILD — WorkOS Design System Pilot 03: Orders + Operator + Execution Badges

## Purpose

Visual/semantic adoption of shared `SourceBadge` and `StatusBadge` primitives in operational modules (Orders, Operator). No business logic, API, DB, or lifecycle changes.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD at start: `43315a4` (employee-payments pilot)
- Prior pilots: Work Intake (`3053826`), Employee Payments (`43315a4`)
- Direction: Operational Precision — status is sovereign, source truthfulness mandatory

## Scope

### In scope

- `Orders.tsx` — source + order status badges
- `OperatorView.tsx` — source + execution task status badges
- Design-system test coverage for order/executionTask domains
- New targeted page badge tests

### Out of scope (explicit boundaries)

- No DB / seed / migrations / fresh dev.db
- No backend changes
- No `index.css` / `tailwind.config` / App shell changes
- No Quotes, Commercial Document, Work Intake, Employee Payments, ProductSystem changes
- **Tablet** — observed only (`TabletSourceBadge` duplicate); deferred to Tablet-specific pilot
- **Execution** — audited and **deferred** (see below)
- No status transition / CTA / write-once / plan generation logic changes

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/Orders.tsx` | Adopt `SourceBadge` + `StatusBadge`; remove local `DataSourceBadge` / inline status badge |
| `frontend/src/pages/OperatorView.tsx` | Adopt `SourceBadge` + `ExecutionTaskStatusBadge`; remove local `DataSourceBadge`; drop `TaskStatusBadge` import |
| `frontend/src/components/workos/design-system/StatusBadge.test.tsx` | Extended order/executionTask coverage |
| `frontend/src/pages/Orders.badges.test.tsx` | **New** — Orders badge adoption tests |
| `frontend/src/pages/OperatorView.badges.test.tsx` | **New** — Operator badge adoption tests |

**Not changed:** `tokens.ts` (existing mappings sufficient), `ExecutionDetail.tsx`, `ExecutionDashboard.tsx`, Tablet pages.

## Modules touched

- Orders list + detail panel (header source badge, order cards, selected order status)
- Operator header source badge, current task panel, task list / timeline cards

## Local badges removed / replaced

| Module | Removed | Replaced with |
|--------|---------|---------------|
| Orders | `DataSourceBadge` (~38 lines) | `<SourceBadge source={ordersSource} />` |
| Orders | `OrderStatusBadge` inline span styling | `OrderStatusBadge` → `StatusBadge domain="order"` + preserved RO labels/icons |
| Operator | `DataSourceBadge` (~32 lines) | `<SourceBadge source={source} />` |
| Operator | `TaskStatusBadge` from SharedComponents (EN labels) | `ExecutionTaskStatusBadge` → `StatusBadge domain="executionTask"` (RO labels from tokens) |

**Kept locally (not entity badges):**

- Orders `statusConfig` — filter chip labels + icon/label overrides for `OrderStatusBadge`
- Orders `paymentConfig` — payment row styling (out of pilot scope)
- Orders `JobStatusBadge` — linked mock job status (SharedComponents)
- Operator `EligibilityBadge` — registry eligibility (operational, not task status domain)

## Source semantics per module

### Orders

```ts
const ordersSource = sourcesDetail?.orders ?? source;
<SourceBadge source={ordersSource} />
```

- Uses **orders-specific** source, not aggregate `source` (fixes prior bug showing aggregate mixed/mock incorrectly)
- `empty` → `Live DB (gol)` via design-system
- `mixed` → `Mixed Source` (slate, not confused with Live DB)
- Empty list with `source: "db"` still shows `Live DB` (backend truth); no false mock/demo

### Operator

```ts
<SourceBadge source={source} />
```

- `useOperatorData()` exposes `source` only (no `sourcesDetail` on hook today)
- `empty` → `Live DB (gol)` — live empty ≠ mock (preserved from prior fix)
- `mock` → mock alert banner unchanged; badge shows `Mock Data`
- `loading` → page-level spinner (early return); badge not shown during load

## Status domains used

| Location | Domain | Status values observed |
|----------|--------|------------------------|
| Orders list/detail | `order` | `created`, `confirmed`, `locked`, `in_execution`, `completed`, `cancelled` |
| Operator tasks | `executionTask` | `assigned`, `created`, `in_progress`, `paused`, `blocked`, `done` |

Token mappings in `tokens.ts` covered all observed values; no token edits required.

## Execution — deferred

**Audited files:** `ExecutionDetail.tsx`, `ExecutionDashboard.tsx`

**Why deferred:**

- No local `DataSourceBadge` duplicate
- Task status in `ExecutionDetail` uses **RealityTaskStatus** (`not_started`, `in_progress`, `completed`) — different semantic family from `executionTask` plan statuses
- Observability/gate badges use inline `statusBadgeCls()` for execution observability severities — not entity status badges
- Adoption would risk conflating plan task status vs reality observation status without a dedicated domain mapping build

**Recommendation:** Dedicated Execution pilot with `reality` or new `realityTask` domain if needed.

## Tablet — observed, not modified

- `TabletMode.tsx` has local `TabletSourceBadge` — duplicate pattern observed
- **Deferred to Tablet-specific pilot**

## Tests run + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/Orders.badges.test.tsx `
  src/pages/Orders.empty.test.tsx `
  src/pages/Orders.executionCta.test.tsx `
  src/pages/Orders.executionDispatch.test.tsx `
  src/pages/OperatorView.badges.test.tsx `
  src/pages/OperatorView.live.test.tsx `
  src/pages/OperatorView.eligibility.test.tsx
```

**Result: 54/54 PASS** (9 files)

- Design-system: 21 + 8 = 29 tests
- Orders: 6 + 3 + 3 + 3 = 15 tests
- Operator: 6 + 3 + 1 = 10 tests

## Runtime smoke (read-only) — 2026-06-13 rerun

Stack: frontend `http://127.0.0.1:3000`, backend live. Read-only; no DB/API mutations.

| Route | Result | Evidence |
|-------|--------|----------|
| `/orders` + `/orders/ORD-1781201059-1` | **PASS** | `SourceBadge` `Live DB` (`data-source="db"`); order `StatusBadge` `Înghețat` (`domain=order`, `tone=violet`); CTA `Vezi execuția` + `order-execution-plan-exists`; no mock/disconnected banner; 0 console errors |
| `/operator` | **PASS** | `SourceBadge` `Live DB`; task badges `Alocat` (blue) + `Finalizat` (emerald); 10× Start visible; no mock alert; 0 console errors |
| `/execution/1` | **PASS** (audit — page not modified in pilot) | Loads OK; 11 task rows; plan + reality present; write-once blocker text intact; inline reality status badges unchanged (no design-system adoption); 0 console errors |

## Visual before / after summary

| Element | Before | After |
|---------|--------|-------|
| Orders source | Local rounded rect badge; used aggregate `source` | Rounded-full `SourceBadge`; uses `ordersSource` |
| Orders status | Inline Tailwind per status | `StatusBadge domain="order"` + preserved RO labels/icons |
| Operator source | Local rounded-full badge | Shared `SourceBadge` |
| Operator task status | `TaskStatusBadge` (English: Assigned, Running…) | `StatusBadge domain="executionTask"` (Romanian from tokens) |

Operational density and layout preserved; badge shape aligns with Work Intake / Employee Payments pilots.

## Deferred items

- Tablet-specific adoption (`TabletSourceBadge`)
- Execution detail reality-task badges + observability severity badges
- Quotes-specific adoption (Pilot 04 candidate)
- Shell/global polish (last)

## Next steps / decisions

1. **Pilot 04:** Quotes badges vs Tablet-specific UI
2. **Source semantics:** Consider exposing `sourcesDetail.executionTasks` on `useOperatorData` when backend supports per-module source
3. **Status labels:** Keep module-level label overrides (`OrderStatusBadge` wrapper) vs centralize all RO copy in tokens

## Commit status

**NOT COMMITTED** — per build instructions, ready for manual commit-tree review.
