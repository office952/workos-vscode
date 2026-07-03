# BUILD — WorkOS Design System Consolidation Audit

## Extra guardrails (pre-audit)

### Payment / backend WIP check — **PASS**

Before audit, verified no active WIP from:

| Build area | Tracked modifications | Untracked payment files |
|------------|----------------------|-------------------------|
| Personal Employee Payments Foundation | none | none |
| Employee Compensation Profiles | none (no QA/build doc in repo) | none |
| Payment Schedule Preview | none (no QA/build doc in repo) | none |
| Backend / migration / payment builds | none | none |

`git diff` and `git diff --cached` empty. Only untracked file: this audit QA doc.

### Commit policy — **enforced**

This build produced **no commits** of any kind:

- no `git commit`
- no `git commit-tree`
- no staging for commit
- no trailers / `Co-authored-by`

Deliverables: audit report + QA doc + READY/NOT READY for later manual review only.

### Badge replacement rule

Only **semantic source/status duplicates** of `SourceBadge` / `StatusBadge` are cleanup candidates.

**Keep local (not problems):**

- eligibility markers (`EligibilityBadge`)
- warning pills / readiness chips
- operational routing badges (`OperationRoutingBadge`, `GateBadge`)
- urgent/blocked contextual labels (`PriorityBadge`)
- density/touch/mobile-specific labels (Tablet wrappers)
- decorative or layout-only shadcn `Badge`
- module-specific semantics not yet in design-system tokens


## Context

- Branch: `local/integration-pr4-plus-svg-path`
- HEAD at audit: `7e8d2ae` (`feat(quotes): polish commercial document client-facing preview`)
- Prior pilots: Work Intake, Employee Payments, Operations, Quotes, Product Pricing, Tablet, Commercial Document preview

## Scope

### In scope

- Global frontend search for `StatusBadge`, `SourceBadge`, `DataSourceBadge`, local badge helpers
- Module coverage matrix
- Clean now / defer / keep-local classification
- QA audit doc + final report

### Out of scope (boundaries)

- No DB / seed / migrations / backend
- No CostEngine / Pricing / Quote-Order workflow logic
- No export/PDF engine
- No App shell / `index.css` / `tailwind.config`
- No runtime badge replacement in this build (audit-only)

## Audit commands used

```powershell
cd C:\Users\offic\workos
git branch --show-current
git rev-parse --short HEAD
git status --short

# Semantic search (via ripgrep)
rg "DataSourceBadge|SourceBadge|StatusBadge|statusConfig|TASK_STATUS_CONFIG|Badge" frontend/src
rg "sourcesDetail|source ===|data-source|Mock Data|Demo|Live DB|No Data|disconnected" frontend/src
```

## TASK 0 — Precheck

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` ✅ |
| HEAD | `7e8d2ae` ✅ |
| Git status | **clean** ✅ |

## Audit summary — remaining local inventory

### Design-system adopted (11 import sites)

Modules importing `@/components/workos/design-system`:

| Module | SourceBadge | StatusBadge | Notes |
|--------|-------------|-------------|-------|
| Work Intake V1 | ✅ `intakeSource` | ✅ wrapper + icons | `statusConfig` kept for pipeline cards |
| Quotes | ✅ `quotesSource` | ✅ `QuoteStatusBadge` | `VolumetricQuoteReadinessChip` still local |
| Commercial Document | — | ✅ operator chrome + action panel | No SourceBadge in client letterhead (intentional) |
| Orders | ✅ `ordersSource` | ✅ `OrderStatusBadge` | `JobStatusBadge` still local via SharedComponents |
| Operator | ✅ aggregate `source` | ✅ `ExecutionTaskStatusBadge` | `EligibilityBadge` local |
| Tablet | ✅ `TabletSourceBadge` wrapper | ✅ `executionTask` + `TASK_STATUS_CONFIG` labels | `EligibilityBadge` local |
| Employee Payments | ✅ derived | ✅ `PaymentStatusBadge` | |
| ProductSystem | ✅ load mode mapped | ✅ template + registry rows | `OperationRoutingBadge` local |
| Pricing | partial | ✅ entry rows | `GateBadge` local; SourceBadge in spacious view |
| Pricing components | ✅ registry view | ✅ entry row | |

### Local `DataSourceBadge` duplicates (3 files)

| File | Issue | Empty label today | Design-system label |
|------|-------|-------------------|---------------------|
| `Colaboratori.tsx` | Local `DataSourceBadge` | `"No Data"` | `"Live DB (gol)"` |
| `Personal.tsx` | Local `DataSourceBadge` | `"No Data"` | `"Live DB (gol)"` |
| `ShopFloor.tsx` | Local `DataSourceBadge` | `"Empty"` | `"Live DB (gol)"` |

**Risk:** Replacing without product decision changes source truthfulness copy → **defer**.

### Local `SourceBadge` name collision (1 file)

| File | Issue |
|------|-------|
| `Utilaje.tsx` | Local function `SourceBadge` shadows design-system; custom styling, partial state coverage |

### Local `StatusBadge` / status chip duplicates (non-design-system)

| File / component | Type | Recommendation |
|------------------|------|----------------|
| `ClientWorkspace.tsx` | `StatusBadge({ label, cls })` | Defer — multi-entity workspace, heavy layout |
| `DocumentCenter.tsx` | `StatusBadge({ label, cls })` | Defer — doc lifecycle specific |
| `MaterialPriceRegistry.tsx` | `StatusBadge`, `IncompleteBadge`, `ReadyBadge`, … | Defer — inventory semantics |
| `Colaboratori.tsx` | `StatusBadge` for collab status | Keep local — domain-specific (preferat/activ) |
| `CommercialMarkupPolicies.tsx` | `PolicyStatusBadge`, `ScopeBadge` | Keep local — admin policy semantics |
| `Clients.tsx` | `FiscalStatusBadge` | Keep local — fiscal display, not entity status |
| `SharedComponents.tsx` | `JobStatusBadge`, `TaskStatusBadge`, `PriorityBadge` | Defer — shop-floor job model; icons embedded |
| `ExecutionDashboard.tsx` | inline `statusBadgeCls` | Defer — divergence/reality grid |
| `ExecutionDetail.tsx` | inline + `ReasonBadge` | Defer — operational diagnostics |
| `VolumetricQuoteReadinessChip` | readiness snapshot chip | Keep local — readiness ≠ quote status |
| `OperatorView` / `TabletMode` | `EligibilityBadge` | Keep local — HR eligibility, not task status |
| `ProductSystem.tsx` | `OperationRoutingBadge` | Keep local — routing marker |
| `Pricing.tsx` | `GateBadge` | Keep local — readiness gate code |
| `RealityQualityBadge` | data quality marker | Keep local — specialized |
| `IntakeDetail.tsx` | workspace diagnostic badge | Keep local — debug/operator |
| `WorkIntakeV2` shell | text/class save status, no DS badges | Defer — separate V2 build |

### `sourcesDetail` vs aggregate `source` risks

| Location | Pattern | Risk |
|----------|---------|------|
| `Quotes.tsx` | Header uses `quotesSource` ✅ | Commercial doc visibility still gates on `source === "db"` (lines ~822, ~834) — **defer** (workflow guard, not badge) |
| `Orders.tsx` | `ordersSource` ✅ | Tests present |
| `WorkIntake.tsx` | `intakeSource` ✅ | |
| `OperatorView.tsx` | aggregate `source` only | Acceptable for operator tasks hook |
| `EmployeePayments.tsx` | derives from data length | Acceptable pattern for module |

### Counts (approximate, semantic badges only)

| Category | Count |
|----------|-------|
| Design-system `SourceBadge` usages | ~15 sites |
| Design-system `StatusBadge` usages | ~25+ sites |
| Local `DataSourceBadge` | 3 |
| Local shadow `SourceBadge` | 1 (`Utilaje`) |
| Local entity `StatusBadge` functions | ~8 pages |
| Intentional operational markers | ~12 components |
| shadcn `Badge` (ui/) | unrelated — do not migrate blindly |

## Module coverage matrix

| Module | SourceBadge | StatusBadge | Local duplicates | Source risk | Tests | Smoke | Recommendation |
|--------|-------------|-------------|------------------|-------------|-------|-------|----------------|
| Work Intake V1 | yes | yes | pipeline `cls` | low | yes | no | **keep** (pipeline uses cls for icons) |
| Work Intake V2 | n/a | n/a | save status text | n/a | yes | no | **defer** — separate V2 badge build |
| Quotes | yes | yes | readiness chip | medium (`source===db` guard) | yes | no | **defer** guard fix; badges OK |
| Commercial Document | n/a | partial | none | n/a | yes | no | **keep** — client doc intentional |
| Orders | yes | yes | JobStatusBadge | low | yes | no | **defer** JobStatusBadge |
| Execution | no | no | inline cls | n/a | partial | no | **defer** — reality/divergence UI |
| Operator | yes | yes | EligibilityBadge | low | yes | no | **keep** eligibility local |
| Tablet | yes | yes | EligibilityBadge | low | yes | no | **keep** eligibility local |
| Employee Payments | yes | yes | none | low | yes | no | **clean** (already adopted) |
| ProductSystem | yes | yes | routing badge | low | yes | no | **keep** routing local |
| Pricing | partial | yes | GateBadge | low | yes | no | **defer** gate badge |
| Inventory / MaterialPriceRegistry | no | no | many local | n/a | partial | no | **defer** — inventory build |
| Colaboratori | no | local | DataSourceBadge | medium (label) | no | no | **defer** |
| Personal | no | no | DataSourceBadge | medium (label) | no | no | **defer** |
| ShopFloor | no | no | DataSourceBadge + JobStatus | medium | no | no | **defer** |
| Utilaje | local shadow | no | SourceBadge fn | medium | no | no | **defer** |
| ClientWorkspace | no | local | multi-entity | n/a | no | no | **defer** |
| DocumentCenter | no | local | doc status | n/a | no | no | **defer** |
| Settings / Governance | no | local | category | n/a | no | no | **keep** |
| Dashboard / Control Tower | n/a | n/a | not found | n/a | no | no | n/a |

## Clean now / defer / keep local

### Clean now (selected for this build)

**None implemented.**

Reason: Every remaining `DataSourceBadge` duplicate uses **different empty/error labels** than design-system source truthfulness (`Live DB (gol)`, `Source Error`, etc.). Replacing would change operator-visible semantics without a dedicated label migration decision.

### Deferred (recommended next builds)

1. **Secondary modules source badge pilot** — `Colaboratori`, `Personal`, `ShopFloor`, `Utilaje` (with label parity tests)
2. **Quotes commercial guard** — use `quotesSource === "db"` instead of aggregate `source` for commercial document panel visibility (workflow guard, separate from badge styling)
3. **SharedComponents job/task badges** — map `JobStatus` / `TaskStatus` to design-system domains or add `job` domain in tokens
4. **Work Intake V2 operational header** — adopt `StatusBadge` for intake/save states when V2 shell build is scoped
5. **Execution / ClientWorkspace / DocumentCenter / MaterialPriceRegistry** — large surface; needs dedicated builds + tests
6. **Inventory pricing registry badges** — tied to material registry semantics

### Keep local intentionally

- `EligibilityBadge` (Operator, Tablet, FieldInstallation)
- `VolumetricQuoteReadinessChip` (Quotes)
- `OperationRoutingBadge`, `GateBadge`, `PolicyStatusBadge`, `FiscalStatusBadge`
- `RealityQualityBadge`, `ReasonBadge`, diagnostic/workspace badges
- `PriorityBadge`, `CategoryBadge`, shadcn `Badge`

## Files changed

| File | Change |
|------|--------|
| `docs/qa/BUILD_WORKOS_DESIGN_SYSTEM_CONSOLIDATION_AUDIT.md` | **New** — this audit doc |

**Runtime:** no frontend/backend files modified.

## Tests run

Audit-only build. Sanity check on design-system primitives:

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx
```

| Result |
|--------|
| **44 passed** (2 files) |

## Runtime smoke

**Not applicable** — audit-only, no runtime changes.

## Boundaries confirmed

- No DB / seed / migrations / backend changes
- No CostEngine / Pricing logic changes
- No Quote → Order workflow changes
- No export engine changes
- No App shell / global CSS / tailwind changes

## Before / after

| Area | Before audit | After this build |
|------|--------------|------------------|
| Badge adoption pilots | 8 modules + commercial doc | Unchanged (documented) |
| Remaining local inventory | Unknown | Catalogued + classified |
| Runtime code | Baseline | **Unchanged** |

## Recommended next build

1. **Pilot: Secondary source badges** — `Colaboratori`, `Personal`, `ShopFloor`, `Utilaje` with `SourceBadge` + label parity tests (`Live DB (gol)` migration explicit)
2. **Quotes source guard fix** — `quotesSource` for commercial document visibility (small, testable)
3. **ShopFloor / SharedComponents** — `JobStatusBadge` → design-system when `job` domain tokens defined
4. **Deferred larger:** Execution dashboard, ClientWorkspace, MaterialPriceRegistry, Work Intake V2 header
5. **Later:** Shell/global polish, PDF/export visual alignment, email/client templates
