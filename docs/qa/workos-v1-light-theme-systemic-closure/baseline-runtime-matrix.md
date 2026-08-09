# Light Theme — Runtime baseline matrix (pre-edit)

```text
CAPTURED = 2026-08-10
THEME_FORCED = workos-theme=light + html.light (verified via CDP)
HEAD_AT_CAPTURE = 17082af6+ (working tree may already include commercial commits)
RULE = outcome-based P0/P1 only; grep literals alone do not force patches
```

## Theme authority at capture

| Check | Result |
|-------|--------|
| `localStorage.workos-theme` | `light` |
| `document.documentElement.classList` | `light` |
| `data-theme` | `light` |

## Runtime-proven findings

| ID | Route / surface | Severity | Evidence | Likely systemic fix |
|----|-----------------|----------|----------|---------------------|
| RT-P0-01 | `/intake-v6/:id/operator` commercial hero | **P0** | CDP: `691,27 EUR` computed `color: rgb(167,243,208)` (`text-emerald-200`) on near-white surface; net `571,30 EUR` as `text-slate-200` — amount barely readable | Shared Intake pricing chrome → `wo-text-*` / emerald with light+dark pairs |
| RT-P0-02 | Intake V6 config metadata / actions | **P0/P1** | Pale `text-slate-300` on light cards (`Detalii tehnice`, Cant/Spate rows, adjustments) | Shared atoms + LiveCalc/Pricing panels |
| RT-P1-01 | Quotes list filter active chip | **P1** | `Toate` uses `text-blue-400` on translucent blue — weak on light list | Shared filter chip recipe |
| RT-P1-02 | Quotes detail status chips (emerald/amber `*-950/20` + `*-100/200` text) | **P1** | Night-oriented badge recipes on light detail rail | Shared badge / chromeRecipes |
| RT-CODE-01 | Quotes `#121B2C` frozen Snapshot V2 block | **P0 when visible** | Code path only when `acceptedSnapshotV2Id \|\| snapshotV2Code`; not on sample Tarifat quote without freeze card. Still a real operator defect when freeze present | Page-local Quotes after shared pass |
| RT-OK-01 | `/dashboard` AppShell | OK | Light coherent; sidebar/topbar readable | — |
| RT-OK-02 | `/quotes` list outer chrome | OK / partial | List cards readable; currency honesty `monedă indisponibilă` is commercial not theme | — |
| RT-OK-03 | `/orders` list | OK | `paleApprox=0`; hierarchy clear (historical RON fixtures expected) | — |
| RT-OK-04 | `/execution` list | OK | `paleApprox=0`; banners/table readable | Detail gate panels still code-suspect — audit on open |

## Hypotheses demoted until runtime proof

| Code hypothesis | Status |
|-----------------|--------|
| Every `bg-slate-900` on Quotes list | Not a list defect on current Light pass |
| Orders page night hex | Not proven on list (paleCount 0) |
| Execution dashboard night hex | Not proven on list |
| Sonner orphan next-themes | Authority defect — prove with toast trigger after shared fix |
| SourceBadge empty/mixed | Prove when empty/mixed badge appears on Pricing/PS |

## Commercial spot-check (baseline)

| Check | Result |
|-------|--------|
| Intake Letters total EUR visible | YES (`691,27 EUR` / `571,30 EUR`) — **contrast broken** but currency correct |
| Quotes commercial lines EUR | YES on detail (`… EUR` line items) |
| Hardcoded RON invent on Letters Intake | NO |

## Screenshot index (`baseline-light/`)

| File | Route |
|------|-------|
| `01-dashboard-appshell.png` | `/dashboard` |
| `02-quotes-list.png` | `/quotes` |
| `02b-quotes-detail.png` | `/quotes/:id` |
| `03-intake-v6-config.png` | `/intake-v6/.../operator` |
| `04-orders-list.png` | `/orders` |
| `05-execution.png` | `/execution` |
| *(pending)* | machine-runs, pricing, product-system, modules, governance, shop-floor, utilaje |

## Implementation order after this matrix

1. GLOBAL: Sonner → ThemeContext (keep `next-themes` package)
2. SHARED: Intake pricing text classes + presentation helpers (closes RT-P0-01/02 first)
3. SHARED: Quote chips / SourceBadge tones
4. PAGE-LOCAL: Quotes `#121B2C` freeze card; remaining proven islands
5. Dark regression after each systemic group
