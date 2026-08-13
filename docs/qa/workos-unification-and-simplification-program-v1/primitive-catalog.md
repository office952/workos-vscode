# Primitive catalog (observe only)

Wave 0 lists what already exists. Wave 1 records whether the three homes use these or page-local clones. No redesign.

## 1. Shared design-system exports

Source: [`frontend/src/components/workos/design-system/index.ts`](../../../frontend/src/components/workos/design-system/index.ts)

| Export | Intended job |
|--------|----------------|
| `PageShell` | Page frame |
| `SectionCard` | Section surface |
| `EmptyState` | Empty |
| `AlertBanner` | Alert |
| `DataTableWrapper` | Table chrome |
| `MetricTile` | KPI tile |
| `StatusBadge` | Status |
| `SourceBadge` | Provenance |
| `RiskBadge` | Risk |
| `BoundaryBadge` | Domain boundary |
| `ReadinessPanel` | Readiness list |
| `PreviewOfficialBanner` | Document stage |
| `AuditOnlyNotice` | Audit-only honesty |
| `InternalCostNotice` | Internal cost (not offer) |
| `CapacityNotice` | Capacity (not price) |
| `OwnerGoNotice` | Owner GO required |
| `ModuleModelDeferredNotice` | Deferred module |
| `ThemeToggle` | Light / dark / system |
| `chromeBanner` / `chromeForm` / `chromeTab` | Chrome recipes |
| tokens | `--wo-*` in `tokens.ts` + `index.css` |

Theme: [`frontend/src/contexts/ThemeContext.tsx`](../../../frontend/src/contexts/ThemeContext.tsx) (`workos-theme`, `html.light` / `html.dark`).

## 2. Shell (not in the barrel, but shared)

| Piece | File |
|-------|------|
| Desktop shell | `frontend/src/components/workos/AppShell.tsx` |
| Nav IA | `frontend/src/lib/shellNavigation.ts` |
| Path guard | `frontend/src/components/workos/ShellPathGuard.tsx` |
| Role home | `frontend/src/components/workos/RoleHomeRedirect.tsx` |

Standalone shells (`/employee-app/*`, `/employee-app-v2/*`, `/intake-v6-app/*`) hard-code dark backgrounds and **do not** use `ThemeContext`. Out of Wave 1 full-audit scope; note only if a nav edge lands there.

## 3. Wave 1 observation columns

For each audited surface, record:

- Uses `PageShell` / `SectionCard` / tokens? or page-local Tailwind cards?
- Empty / error: shared vs custom
- Tables: `DataTableWrapper` vs raw `<table>`
- Status / money: typed API evidence vs frontend-invented
- H1 vs sidebar label drift
- Internal codes / 1:1 technical trees shown as the operator story

Filled in Wave 1 findings, not here.
