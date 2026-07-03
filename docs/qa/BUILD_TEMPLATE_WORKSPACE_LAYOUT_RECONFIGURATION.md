# BUILD — Template Workspace Layout Reconfiguration

## Problem

After modularization (`7054e22`), the volumetric workspace used `max-w-5xl` (~1024px) with all modules stacked vertically, leaving large unused space on the right in wide viewports and forcing extra vertical scrolling.

## Layout audit (before)

| Area / module | Position | Problem | Main? | Side? |
|---------------|----------|---------|-------|-------|
| RequestContextPanel | Top full-width | Consumes horizontal space for metadata | No | Yes (compact) |
| TemplateStatusPanel | Below context | Horizontal strip wasted in main flow | No | Yes (stacked) |
| WorkspaceTabBar | Below status | OK in main | Yes | No |
| WorkspaceAlerts | Below tabs | Form-related | Yes | No |
| TemplateConfirmationPanel | Main stack | OK with form | Yes | No |
| ProductSpecEditorSlot | Main stack | Core form | Yes | No |
| TerrainRequirementPanel | Main stack | Needs form context | Yes | No |
| ReadinessGatePanel | Bottom main | Actions scrolled away | No | Yes (sticky) |
| QuoteHandoffPanel | Full width tab | OK in main when active | Yes | No |

**Before max width:** `max-w-5xl` on workspace root.

## Layout decision

Reusable shell:

- `TemplateWorkspaceLayout` — responsive CSS grid
- `WorkspaceMainColumn` — flexible main content
- `WorkspaceSidePanel` — `xl:sticky xl:top-4` operator panel
- `StickyWorkspaceActions` — groups primary CTAs

Grid: `xl:grid-cols-[minmax(0,1fr)_minmax(280px,320px)]`

## Module placement (after)

| Main column | Side panel (sticky) |
|-------------|---------------------|
| WorkspaceTabBar | RequestContextPanel (compact) |
| WorkspaceAlerts | TemplateStatusPanel (stacked) |
| TemplateConfirmationPanel | ReadinessGatePanel (stack) |
| ProductSpecEditorSlot | Simulare ofertă + Gata pt. Ofertă |
| TerrainRequirementPanel | — |
| QuoteHandoffPanel (quote tab) | Side actions remain visible |

Duplicate “Simulare” CTA removed from tab bar; single primary action in side panel.

## Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| HEAD | `7054e22` |
| Backend | healthy |
| Frontend | `:3000` up |
| Counts before | intakes 11, quotes 7, orders 8 |

## Tests / lint

- Vitest: layout + volumetric workspace + IntakeDetail shells — **27 PASS**
- ESLint: `templateIntakeWorkspace/` — clean

## Browser validation

WI-SMOKE-P001: two-column layout uses viewport width; side panel sticky with actions; values 4800/600/60/2.88/18/9; simulation **844.41 EUR**; no quote created.

/quotes: Ofertă nouă opens generic wizard; cancel without creating quote.

## Counts after

Unchanged: intakes 11, quotes 7, orders 8.

## Confirmations

- No pricing / CostEngine / readiness policy changes
- No quote/order created
- No Reference Catalogs
- Product001IntakeSpecEditor contract unchanged
- Generic intake path unaffected

## Result

**PASS**
